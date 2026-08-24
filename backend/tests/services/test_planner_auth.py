from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import PlannerAccount, PlannerSession, PlannerStartupCredential
from app.services.planner_auth import (
    authenticate_session,
    PlannerAuthFailure,
    bootstrap_administrator,
    create_planner_account,
    disable_account,
    hash_password,
    issue_reactivation_access,
    issue_reset_access,
    login_planner,
    normalize_login_name,
    reconcile_startup_credentials,
    recover_administrator,
    redeem_account_access,
    transfer_administration,
    validate_new_password,
    verify_password,
)
from tests.planner_auth_fixtures import DeterministicUtcClock, startup_credential


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    with Session(engine) as session:
        yield session


def test_argon2id_password_policy_and_login_normalization():
    encoded = hash_password("ein langes passwort")
    assert encoded.startswith("$argon2id$v=19$m=65536,t=3,p=4$")
    assert verify_password(encoded, "ein langes passwort") is True
    assert verify_password(encoded, "falsch") is False
    assert normalize_login_name("  PlanEr  ") == ("PlanEr", "planer")
    validate_new_password("a" * 12, normalized_login_name="planer")
    validate_new_password("mit normalen Leerzeichen", normalized_login_name="planer")
    validate_new_password("a" * 128, normalized_login_name="planer")
    with pytest.raises(PlannerAuthFailure):
        validate_new_password("a" * 11, normalized_login_name="planer")
    with pytest.raises(PlannerAuthFailure):
        validate_new_password("a" * 129, normalized_login_name="planer")
    with pytest.raises(PlannerAuthFailure):
        validate_new_password(" PLANER ", normalized_login_name="planer")


def test_startup_reconciliation_persists_absence_replacement_and_retirement(db):
    clock = DeterministicUtcClock()
    first = startup_credential(1)
    second = startup_credential(2)

    reconcile_startup_credentials(db, bootstrap_credential=first, recovery_credential=None, clock=clock.now)
    db.commit()
    reconcile_startup_credentials(db, bootstrap_credential=None, recovery_credential=None, clock=clock.now)
    db.commit()
    current = db.scalar(select(PlannerStartupCredential).where(PlannerStartupCredential.state == "current"))
    assert current is not None

    clock.advance(minutes=1)
    reconcile_startup_credentials(db, bootstrap_credential=second, recovery_credential=None, clock=clock.now)
    db.commit()
    rows = db.scalars(select(PlannerStartupCredential).order_by(PlannerStartupCredential.first_seen_at)).all()
    assert [row.state for row in rows] == ["replaced", "current"]

    with pytest.raises(PlannerAuthFailure):
        reconcile_startup_credentials(
            db,
            bootstrap_credential=second,
            recovery_credential=second,
            clock=clock.now,
        )


def test_bootstrap_is_single_use_requires_current_purpose_and_does_not_create_session(db):
    clock = DeterministicUtcClock()
    credential = startup_credential(3)
    reconcile_startup_credentials(db, bootstrap_credential=credential, recovery_credential=None, clock=clock.now)
    db.commit()

    account = bootstrap_administrator(
        db,
        startup_credential=credential,
        login_name="  Erste.Admin  ",
        display_name=" Erste Administration ",
        password="sicheres passwort",
        clock=clock.now,
    )
    db.commit()
    assert (account.login_name, account.normalized_login_name, account.display_name) == (
        "Erste.Admin",
        "erste.admin",
        "Erste Administration",
    )
    assert account.is_active and account.is_administrator
    assert db.scalar(select(PlannerSession.id)) is None

    with pytest.raises(PlannerAuthFailure):
        bootstrap_administrator(
            db,
            startup_credential=credential,
            login_name="zweite",
            display_name="Zweite Administration",
            password="anderes passwort",
            clock=clock.now,
        )
    db.rollback()
    assert db.scalar(select(PlannerAccount).where(PlannerAccount.is_administrator)).id == account.id


def test_login_uses_generic_failures_restricts_after_ten_attempts_and_preserves_session(db):
    clock = DeterministicUtcClock()
    account = PlannerAccount(
        login_name="Planer",
        normalized_login_name="planer",
        display_name="Planung Person",
        password_hash=hash_password("richtiges passwort"),
        is_active=True,
        is_administrator=False,
        created_at=clock.now(),
    )
    db.add(account)
    db.commit()

    first_login = login_planner(db, login_name=" planer ", password="richtiges passwort", clock=clock.now)
    db.commit()
    first_digest = db.scalar(select(PlannerSession.secret_digest))

    for _ in range(10):
        with pytest.raises(PlannerAuthFailure) as failure:
            login_planner(db, login_name="PLANER", password="falsches passwort", clock=clock.now)
        assert failure.value.code == "login_failed"
        db.commit()
    db.refresh(account)
    assert account.login_blocked_until == clock.now().replace(tzinfo=None) + timedelta(minutes=15)
    assert db.scalar(select(PlannerSession.secret_digest)) == first_digest

    with pytest.raises(PlannerAuthFailure):
        login_planner(db, login_name="Planer", password="richtiges passwort", clock=clock.now)
    db.commit()
    clock.advance(minutes=15)
    replacement = login_planner(db, login_name="Planer", password="richtiges passwort", clock=clock.now)
    db.commit()
    assert replacement.raw_secret != first_login.raw_secret
    assert db.scalar(select(PlannerSession.secret_digest)) != first_digest
    db.refresh(account)
    assert account.failed_login_count == 0
    assert account.login_blocked_until is None


def test_unknown_login_runs_password_verification_without_creating_identity(db, monkeypatch):
    calls: list[tuple[str, str]] = []
    from app.services import planner_auth

    original = planner_auth.verify_password
    monkeypatch.setattr(
        planner_auth,
        "verify_password",
        lambda encoded, submitted: calls.append((encoded, submitted)) or original(encoded, submitted),
    )

    with pytest.raises(PlannerAuthFailure):
        login_planner(
            db,
            login_name="nicht-vorhanden",
            password="irgendein passwort",
            clock=lambda: datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
    assert len(calls) == 1
    assert db.scalar(select(PlannerAccount.id)) is None


def test_setup_reset_disable_reactivation_and_transfer_are_atomic_account_transitions(db):
    clock = DeterministicUtcClock()
    administrator = PlannerAccount(
        login_name="admin", normalized_login_name="admin", display_name="Administration",
        password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True,
        revision=1, created_at=clock.now(),
    )
    db.add(administrator); db.commit()
    setup = create_planner_account(db, administrator_id=administrator.id, login_name=" Planer ", display_name="Planung", clock=clock.now)
    db.commit()
    assert not setup.account.is_active and setup.account.password_hash is None
    assert len(setup.raw_secret) == 43
    redeem_account_access(db, access_credential=setup.raw_secret, password="planer passwort", clock=clock.now)
    db.commit(); planner_id = setup.account.id
    planner = db.get(PlannerAccount, planner_id); assert planner and planner.is_active

    session = login_planner(db, login_name="planer", password="planer passwort", clock=clock.now); db.commit()
    reset = issue_reset_access(db, administrator_id=administrator.id, account_id=planner_id, expected_revision=planner.revision, clock=clock.now)
    db.commit(); db.refresh(planner)
    assert planner.is_active and planner.password_hash is None
    with pytest.raises(PlannerAuthFailure): authenticate_session(db, session.raw_secret, clock=clock.now)
    db.rollback()
    redeem_account_access(db, access_credential=reset.raw_secret, password="neues passwort", clock=clock.now); db.commit(); db.refresh(planner)

    disabled = disable_account(db, administrator_id=administrator.id, account_id=planner_id, expected_revision=planner.revision, clock=clock.now)
    db.commit(); assert not disabled.is_active and disabled.disabled_at is not None
    reactivation = issue_reactivation_access(db, administrator_id=administrator.id, account_id=planner_id, expected_revision=disabled.revision, clock=clock.now)
    db.commit(); redeem_account_access(db, access_credential=reactivation.raw_secret, password="wieder passwort", clock=clock.now); db.commit(); db.refresh(planner)
    assert planner.is_active and planner.reactivated_at is not None

    former = transfer_administration(db, administrator_id=administrator.id, target_id=planner.id, expected_administrator_revision=administrator.revision, expected_target_revision=planner.revision)
    db.commit(); db.refresh(administrator); db.refresh(planner)
    assert former.id == administrator.id and not administrator.is_administrator and planner.is_administrator
    assert db.scalars(select(PlannerAccount).where(PlannerAccount.is_administrator)).all() == [planner]


def test_recovery_consumes_purpose_specific_startup_access_and_ends_prior_session(db):
    clock = DeterministicUtcClock(); recovery = startup_credential(22)
    administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("altes passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
    db.add(administrator); db.commit()
    reconcile_startup_credentials(db, bootstrap_credential=None, recovery_credential=recovery, clock=clock.now); db.commit()
    prior = login_planner(db, login_name="admin", password="altes passwort", clock=clock.now); db.commit()
    recover_administrator(db, startup_credential=recovery, password="neues passwort", clock=clock.now); db.commit()
    with pytest.raises(PlannerAuthFailure): authenticate_session(db, prior.raw_secret, clock=clock.now)
    db.rollback()
    assert login_planner(db, login_name="admin", password="neues passwort", clock=clock.now)
    db.rollback()
    with pytest.raises(PlannerAuthFailure): recover_administrator(db, startup_credential=recovery, password="noch ein passwort", clock=clock.now)
