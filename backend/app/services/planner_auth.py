from __future__ import annotations

import hashlib
import logging
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.planning import (
    PlannerAccount,
    PlannerAccountAccess,
    PlannerSession,
    PlannerStartupCredential,
)


UTCClock = Callable[[], datetime]
STARTUP_SHAPE = re.compile(r"^[0-9a-fA-F]{64}$")
SESSION_SHAPE = re.compile(r"^[A-Za-z0-9_-]{43}$")
PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65_536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)
DUMMY_PASSWORD_HASH = PASSWORD_HASHER.hash("dummy password verification only")

LOGIN_FAILURE_MESSAGE = (
    "Die Anmeldung war nicht möglich. Prüfen Sie Ihre Angaben und versuchen Sie es erneut. "
    "Wenn Sie weiterhin keinen Zugang haben, wenden Sie sich an die Systemadministration."
)
STARTUP_FAILURE_MESSAGE = (
    "Der Startzugang ist nicht verfügbar. Prüfen Sie die bereitgestellten Zugangsdaten "
    "oder wenden Sie sich an den Infrastruktur-Betrieb."
)
ACCOUNT_ACCESS_FAILURE_MESSAGE = (
    "Der Zugang ist nicht verfügbar. Bitten Sie die Systemadministration um einen neuen Zugangslink."
)
SESSION_ENDED_MESSAGE = "Ihre Sitzung ist beendet. Melden Sie sich erneut an."
ADMIN_REQUIRED_MESSAGE = "Diese Aktion ist nur für die Systemadministration verfügbar."


class PlannerAuthFailure(RuntimeError):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class LoginResult:
    account: PlannerAccount
    raw_secret: str


@dataclass(frozen=True)
class AuthenticatedPlanner:
    account: PlannerAccount
    session: PlannerSession
    secret_digest: str


@dataclass(frozen=True)
class IssuedAccountAccess:
    account: PlannerAccount
    raw_secret: str
    purpose: str
    expires_at: datetime


def _now(clock: UTCClock | None) -> datetime:
    value = clock() if clock else datetime.now(timezone.utc)
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def normalize_login_name(login_name: str) -> tuple[str, str]:
    trimmed = login_name.strip()
    if not 1 <= len(trimmed) <= 128:
        raise PlannerAuthFailure(400, "invalid_account_identity", "Prüfen Sie den Benutzernamen.")
    return trimmed, trimmed.casefold()


def _normalize_display_name(display_name: str) -> str:
    trimmed = display_name.strip()
    if not 1 <= len(trimmed) <= 200:
        raise PlannerAuthFailure(400, "invalid_account_identity", "Prüfen Sie die Anzeigename-Angabe.")
    return trimmed


def validate_new_password(password: str, *, normalized_login_name: str) -> None:
    if not 12 <= len(password) <= 128 or password.strip().casefold() == normalized_login_name:
        raise PlannerAuthFailure(
            400,
            "invalid_password",
            "Das Passwort muss 12 bis 128 Zeichen lang sein und darf nicht dem Benutzernamen entsprechen.",
        )


def hash_password(password: str) -> str:
    return PASSWORD_HASHER.hash(password)


def verify_password(encoded_hash: str, submitted_password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(encoded_hash, submitted_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _digest_secret(raw_secret: str) -> str:
    return hashlib.sha256(raw_secret.encode("ascii")).hexdigest()


def _startup_digest(raw_credential: str) -> str:
    return hashlib.sha256(bytes.fromhex(raw_credential)).hexdigest()


def _validate_startup(raw_credential: str) -> None:
    if not STARTUP_SHAPE.fullmatch(raw_credential):
        raise PlannerAuthFailure(400, "startup_access_unavailable", STARTUP_FAILURE_MESSAGE)


def _begin_write(db: Session) -> None:
    if db.bind is not None and db.bind.dialect.name == "sqlite" and not db.in_transaction():
        db.execute(text("BEGIN IMMEDIATE"))


def reconcile_startup_credentials(
    db: Session,
    *,
    bootstrap_credential: str | None,
    recovery_credential: str | None,
    clock: UTCClock | None = None,
) -> None:
    configured = {
        "bootstrap": bootstrap_credential or None,
        "recovery": recovery_credential or None,
    }
    for raw in configured.values():
        if raw is not None:
            _validate_startup(raw)
    if bootstrap_credential and recovery_credential and secrets.compare_digest(
        bootstrap_credential.casefold(), recovery_credential.casefold()
    ):
        raise PlannerAuthFailure(400, "startup_access_unavailable", STARTUP_FAILURE_MESSAGE)

    _begin_write(db)
    observed_at = _now(clock)
    for purpose, raw in configured.items():
        if raw is None:
            continue
        digest = _startup_digest(raw)
        existing = db.get(PlannerStartupCredential, digest)
        if existing is not None:
            if existing.purpose != purpose or existing.state != "current":
                logging.getLogger(__name__).warning(
                    "Configured %s startup credential is retired or registered for another purpose.",
                    purpose,
                )
            continue
        current = db.scalar(
            select(PlannerStartupCredential).where(
                PlannerStartupCredential.purpose == purpose,
                PlannerStartupCredential.state == "current",
            )
        )
        if current is not None:
            current.state = "replaced"
            current.retired_at = observed_at
        db.add(
            PlannerStartupCredential(
                secret_digest=digest,
                purpose=purpose,
                state="current",
                first_seen_at=observed_at,
            )
        )
    db.flush()


def bootstrap_administrator(
    db: Session,
    *,
    startup_credential: str,
    login_name: str,
    display_name: str,
    password: str,
    clock: UTCClock | None = None,
) -> PlannerAccount:
    try:
        _validate_startup(startup_credential)
    except PlannerAuthFailure:
        raise
    _begin_write(db)
    if db.scalar(select(PlannerAccount.id).where(PlannerAccount.is_administrator)) is not None:
        raise PlannerAuthFailure(409, "startup_access_unavailable", STARTUP_FAILURE_MESSAGE)
    credential = db.get(PlannerStartupCredential, _startup_digest(startup_credential))
    if credential is None or credential.purpose != "bootstrap" or credential.state != "current":
        raise PlannerAuthFailure(400, "startup_access_unavailable", STARTUP_FAILURE_MESSAGE)
    shown_login, normalized_login = normalize_login_name(login_name)
    shown_display = _normalize_display_name(display_name)
    validate_new_password(password, normalized_login_name=normalized_login)
    account = PlannerAccount(
        login_name=shown_login,
        normalized_login_name=normalized_login,
        display_name=shown_display,
        password_hash=hash_password(password),
        is_active=True,
        is_administrator=True,
        failed_login_count=0,
        revision=1,
        created_at=_now(clock),
    )
    credential.state = "consumed"
    credential.retired_at = _now(clock)
    db.add(account)
    try:
        db.flush()
    except IntegrityError as exc:
        raise PlannerAuthFailure(409, "startup_access_unavailable", STARTUP_FAILURE_MESSAGE) from exc
    return account


def login_planner(
    db: Session,
    *,
    login_name: str,
    password: str,
    clock: UTCClock | None = None,
) -> LoginResult:
    now = _now(clock)
    try:
        _, normalized = normalize_login_name(login_name)
    except PlannerAuthFailure:
        normalized = ""
    account = db.scalar(select(PlannerAccount).where(PlannerAccount.normalized_login_name == normalized))
    if account is None:
        verify_password(DUMMY_PASSWORD_HASH, password)
        raise PlannerAuthFailure(401, "login_failed", LOGIN_FAILURE_MESSAGE)

    account_id = account.id
    verified_hash = account.password_hash
    blocked_until = _aware(account.login_blocked_until) if account.login_blocked_until else None
    was_blocked = bool(blocked_until and now < blocked_until)
    verified = verify_password(
        DUMMY_PASSWORD_HASH if was_blocked else verified_hash or DUMMY_PASSWORD_HASH,
        password,
    )

    # Password verification is deliberately outside the SQLite write lock so
    # independent attempts can perform Argon2 work concurrently. Re-read the
    # account under BEGIN IMMEDIATE before changing retry or session state.
    db.rollback()
    _begin_write(db)
    account = db.get(PlannerAccount, account_id)
    if account is None:
        raise PlannerAuthFailure(401, "login_failed", LOGIN_FAILURE_MESSAGE)

    blocked_until = _aware(account.login_blocked_until) if account.login_blocked_until else None
    if blocked_until and now < blocked_until:
        raise PlannerAuthFailure(401, "login_failed", LOGIN_FAILURE_MESSAGE)
    if blocked_until and now >= blocked_until:
        account.failed_login_count = 0
        account.login_blocked_until = None

    usable = account.is_active and account.password_hash is not None
    if was_blocked or account.password_hash != verified_hash:
        verified = verify_password(account.password_hash or DUMMY_PASSWORD_HASH, password)
    if not usable or not verified:
        account.failed_login_count += 1
        if account.failed_login_count >= 10:
            account.login_blocked_until = now + timedelta(minutes=15)
        db.flush()
        raise PlannerAuthFailure(401, "login_failed", LOGIN_FAILURE_MESSAGE)

    if PASSWORD_HASHER.check_needs_rehash(account.password_hash):
        account.password_hash = hash_password(password)
    account.failed_login_count = 0
    account.login_blocked_until = None
    db.execute(delete(PlannerSession).where(PlannerSession.account_id == account.id))
    raw_secret = secrets.token_urlsafe(32)
    db.add(
        PlannerSession(
            account_id=account.id,
            secret_digest=_digest_secret(raw_secret),
            created_at=now,
            last_activity_at=now,
            absolute_expires_at=now + timedelta(hours=12),
        )
    )
    db.flush()
    return LoginResult(account=account, raw_secret=raw_secret)


def authenticate_session(
    db: Session,
    raw_secret: str | None,
    *,
    clock: UTCClock | None = None,
) -> AuthenticatedPlanner:
    if raw_secret is None or not SESSION_SHAPE.fullmatch(raw_secret):
        raise PlannerAuthFailure(401, "session_ended", SESSION_ENDED_MESSAGE)
    digest = _digest_secret(raw_secret)
    session = db.scalar(select(PlannerSession).where(PlannerSession.secret_digest == digest))
    if session is None:
        raise PlannerAuthFailure(401, "session_ended", SESSION_ENDED_MESSAGE)
    account = db.get(PlannerAccount, session.account_id)
    now = _now(clock)
    valid = (
        account is not None
        and account.is_active
        and account.password_hash is not None
        and now < _aware(session.last_activity_at) + timedelta(minutes=60)
        and now < _aware(session.absolute_expires_at)
    )
    if not valid:
        db.delete(session)
        db.flush()
        raise PlannerAuthFailure(401, "session_ended", SESSION_ENDED_MESSAGE)
    return AuthenticatedPlanner(account=account, session=session, secret_digest=digest)


def touch_session_if_current(
    db: Session,
    *,
    account_id: int,
    secret_digest: str,
    clock: UTCClock | None = None,
) -> None:
    now = _now(clock)
    session = db.scalar(
        select(PlannerSession).where(
            PlannerSession.account_id == account_id,
            PlannerSession.secret_digest == secret_digest,
        )
    )
    if (
        session is not None
        and now < _aware(session.last_activity_at) + timedelta(minutes=60)
        and now < _aware(session.absolute_expires_at)
    ):
        session.last_activity_at = now
        db.flush()


def require_administrator(db: Session, account_id: int) -> PlannerAccount:
    account = db.get(PlannerAccount, account_id)
    if account is None or not account.is_active or not account.is_administrator:
        raise PlannerAuthFailure(403, "administrator_required", ADMIN_REQUIRED_MESSAGE)
    return account


def current_account_projection(account: PlannerAccount) -> dict[str, object]:
    return {
        "id": account.id,
        "loginName": account.login_name,
        "displayName": account.display_name,
        "isAdministrator": account.is_administrator,
    }


def account_projection(account: PlannerAccount) -> dict[str, object]:
    return {
        "id": account.id,
        "loginName": account.login_name,
        "displayName": account.display_name,
        "accessLevel": "administrator" if account.is_administrator else "planner",
        "state": "active" if account.is_active else "inactive",
        "revision": account.revision,
        "createdAt": account.created_at,
        "disabledAt": account.disabled_at,
        "reactivatedAt": account.reactivated_at,
    }


def list_planner_accounts(db: Session, administrator_id: int) -> list[dict[str, object]]:
    require_administrator(db, administrator_id)
    return [account_projection(item) for item in db.scalars(select(PlannerAccount).order_by(PlannerAccount.id))]


def end_session(db: Session, account_id: int) -> None:
    db.execute(delete(PlannerSession).where(PlannerSession.account_id == account_id))
    db.flush()


def end_authenticated_session(
    db: Session,
    *,
    account_id: int,
    secret_digest: str,
) -> None:
    db.execute(
        delete(PlannerSession).where(
            PlannerSession.account_id == account_id,
            PlannerSession.secret_digest == secret_digest,
        )
    )
    db.flush()


def change_password(
    db: Session,
    *,
    account_id: int,
    current_password: str,
    new_password: str,
) -> None:
    _begin_write(db)
    account = db.get(PlannerAccount, account_id)
    if account is None or account.password_hash is None or not verify_password(account.password_hash, current_password):
        raise PlannerAuthFailure(400, "password_change_failed", "Das Passwort konnte nicht geändert werden. Prüfen Sie Ihre Angaben.")
    validate_new_password(new_password, normalized_login_name=account.normalized_login_name)
    account.password_hash = hash_password(new_password)
    account.failed_login_count = 0
    account.login_blocked_until = None
    end_session(db, account.id)


def _issue_access(db: Session, account: PlannerAccount, purpose: str, now: datetime) -> IssuedAccountAccess:
    db.execute(delete(PlannerAccountAccess).where(PlannerAccountAccess.account_id == account.id))
    raw_secret = secrets.token_urlsafe(32)
    expires_at = now + timedelta(hours=24)
    db.add(
        PlannerAccountAccess(
            account_id=account.id,
            secret_digest=_digest_secret(raw_secret),
            purpose=purpose,
            issued_at=now,
            expires_at=expires_at,
        )
    )
    db.flush()
    return IssuedAccountAccess(account, raw_secret, purpose, expires_at)


def create_planner_account(
    db: Session,
    *,
    administrator_id: int,
    login_name: str,
    display_name: str,
    clock: UTCClock | None = None,
) -> IssuedAccountAccess:
    _begin_write(db)
    require_administrator(db, administrator_id)
    shown_login, normalized = normalize_login_name(login_name)
    account = PlannerAccount(
        login_name=shown_login,
        normalized_login_name=normalized,
        display_name=_normalize_display_name(display_name),
        password_hash=None,
        is_active=False,
        is_administrator=False,
        revision=1,
        created_at=_now(clock),
    )
    db.add(account)
    try:
        db.flush()
    except IntegrityError as exc:
        raise PlannerAuthFailure(409, "login_name_unavailable", "Der Benutzername ist nicht verfügbar.") from exc
    return _issue_access(db, account, "setup", _now(clock))


def reissue_setup_access(db: Session, *, administrator_id: int, account_id: int, expected_revision: int, clock: UTCClock | None = None) -> IssuedAccountAccess:
    _begin_write(db)
    require_administrator(db, administrator_id)
    account = _action_account(db, account_id, expected_revision)
    if account.is_active or account.disabled_at is not None or account.password_hash is not None:
        raise PlannerAuthFailure(400, "account_action_invalid", "Diese Aktion ist für das Planer-Konto nicht verfügbar.")
    account.revision += 1
    return _issue_access(db, account, "setup", _now(clock))


def redeem_account_access(db: Session, *, access_credential: str, password: str, clock: UTCClock | None = None) -> None:
    if not SESSION_SHAPE.fullmatch(access_credential):
        raise PlannerAuthFailure(400, "account_access_unavailable", ACCOUNT_ACCESS_FAILURE_MESSAGE)
    _begin_write(db)
    access = db.scalar(select(PlannerAccountAccess).where(PlannerAccountAccess.secret_digest == _digest_secret(access_credential)))
    now = _now(clock)
    if access is None or now >= _aware(access.expires_at):
        if access is not None:
            db.delete(access)
            db.flush()
        raise PlannerAuthFailure(400, "account_access_unavailable", ACCOUNT_ACCESS_FAILURE_MESSAGE)
    account = db.get(PlannerAccount, access.account_id)
    if account is None:
        raise PlannerAuthFailure(400, "account_access_unavailable", ACCOUNT_ACCESS_FAILURE_MESSAGE)
    valid_state = (
        (access.purpose == "setup" and not account.is_active and account.disabled_at is None)
        or (access.purpose == "reset" and account.is_active and account.password_hash is None)
        or (access.purpose == "reactivation" and not account.is_active and account.disabled_at is not None)
    )
    if not valid_state:
        raise PlannerAuthFailure(400, "account_access_unavailable", ACCOUNT_ACCESS_FAILURE_MESSAGE)
    validate_new_password(password, normalized_login_name=account.normalized_login_name)
    account.password_hash = hash_password(password)
    account.is_active = True
    account.failed_login_count = 0
    account.login_blocked_until = None
    if access.purpose == "reactivation":
        account.reactivated_at = now
        account.revision += 1
    db.delete(access)
    db.flush()


def _action_account(db: Session, account_id: int, expected_revision: int) -> PlannerAccount:
    account = db.get(PlannerAccount, account_id)
    if account is None:
        raise PlannerAuthFailure(400, "account_action_invalid", "Diese Aktion ist für das Planer-Konto nicht verfügbar.")
    if account.revision != expected_revision:
        raise PlannerAuthFailure(409, "stale_account", "Das Planer-Konto wurde geändert. Aktualisieren Sie die Ansicht.")
    return account


def issue_reset_access(db: Session, *, administrator_id: int, account_id: int, expected_revision: int, clock: UTCClock | None = None) -> IssuedAccountAccess:
    _begin_write(db)
    require_administrator(db, administrator_id)
    account = _action_account(db, account_id, expected_revision)
    if account.is_administrator or not account.is_active:
        raise PlannerAuthFailure(400, "account_action_invalid", "Diese Aktion ist für das Planer-Konto nicht verfügbar.")
    account.password_hash = None
    account.failed_login_count = 0
    account.login_blocked_until = None
    account.revision += 1
    end_session(db, account.id)
    return _issue_access(db, account, "reset", _now(clock))


def disable_account(db: Session, *, administrator_id: int, account_id: int, expected_revision: int, clock: UTCClock | None = None) -> PlannerAccount:
    _begin_write(db)
    require_administrator(db, administrator_id)
    account = _action_account(db, account_id, expected_revision)
    if account.is_administrator or not account.is_active:
        raise PlannerAuthFailure(400, "account_action_invalid", "Diese Aktion ist für das Planer-Konto nicht verfügbar.")
    account.is_active = False
    account.password_hash = None
    account.disabled_at = _now(clock)
    account.revision += 1
    end_session(db, account.id)
    db.execute(delete(PlannerAccountAccess).where(PlannerAccountAccess.account_id == account.id))
    db.flush()
    return account


def issue_reactivation_access(db: Session, *, administrator_id: int, account_id: int, expected_revision: int, clock: UTCClock | None = None) -> IssuedAccountAccess:
    _begin_write(db)
    require_administrator(db, administrator_id)
    account = _action_account(db, account_id, expected_revision)
    if account.is_active or account.disabled_at is None:
        raise PlannerAuthFailure(400, "account_action_invalid", "Diese Aktion ist für das Planer-Konto nicht verfügbar.")
    account.revision += 1
    return _issue_access(db, account, "reactivation", _now(clock))


def transfer_administration(db: Session, *, administrator_id: int, target_id: int, expected_administrator_revision: int, expected_target_revision: int) -> PlannerAccount:
    _begin_write(db)
    current = require_administrator(db, administrator_id)
    target = _action_account(db, target_id, expected_target_revision)
    if current.revision != expected_administrator_revision:
        raise PlannerAuthFailure(409, "stale_account", "Das Planer-Konto wurde geändert. Aktualisieren Sie die Ansicht.")
    if target.id == current.id or not target.is_active or target.password_hash is None or target.is_administrator:
        raise PlannerAuthFailure(400, "account_action_invalid", "Diese Aktion ist für das Planer-Konto nicht verfügbar.")
    current.is_administrator = False
    current.revision += 1
    db.flush()
    target.is_administrator = True
    target.revision += 1
    db.flush()
    return current


def recover_administrator(db: Session, *, startup_credential: str, password: str, clock: UTCClock | None = None) -> None:
    _validate_startup(startup_credential)
    _begin_write(db)
    credential = db.get(PlannerStartupCredential, _startup_digest(startup_credential))
    administrator = db.scalar(select(PlannerAccount).where(PlannerAccount.is_administrator))
    if credential is None or credential.purpose != "recovery" or credential.state != "current" or administrator is None:
        raise PlannerAuthFailure(400, "startup_access_unavailable", STARTUP_FAILURE_MESSAGE)
    validate_new_password(password, normalized_login_name=administrator.normalized_login_name)
    administrator.password_hash = hash_password(password)
    administrator.failed_login_count = 0
    administrator.login_blocked_until = None
    credential.state = "consumed"
    credential.retired_at = _now(clock)
    end_session(db, administrator.id)
