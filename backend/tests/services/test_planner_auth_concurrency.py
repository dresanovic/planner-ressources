import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import PlannerAccount, PlannerAccountAccess, PlannerSession, PlannerStartupCredential
from app.services.planner_auth import (
    PlannerAuthFailure,
    authenticate_session,
    bootstrap_administrator,
    create_planner_account,
    disable_account,
    end_authenticated_session,
    hash_password,
    issue_reactivation_access,
    issue_reset_access,
    login_planner,
    reconcile_startup_credentials,
    recover_administrator,
    redeem_account_access,
    reissue_setup_access,
    transfer_administration,
    verify_password,
)
from tests.planner_auth_fixtures import DeterministicUtcClock, startup_credential


def test_concurrent_bootstrap_has_one_complete_winner(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'bootstrap-race.db'}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    initialize_database(engine)
    clock = DeterministicUtcClock()
    credential = startup_credential(7)
    with Session(engine) as db:
        reconcile_startup_credentials(db, bootstrap_credential=credential, recovery_credential=None, clock=clock.now)
        db.commit()

    def attempt(index: int) -> bool:
        with Session(engine) as db:
            try:
                bootstrap_administrator(
                    db,
                    startup_credential=credential,
                    login_name="Administrator",
                    display_name=f"Administration {index}",
                    password="sicheres passwort",
                    clock=clock.now,
                )
                db.commit()
                return True
            except PlannerAuthFailure:
                db.rollback()
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (1, 2)))

    with Session(engine) as db:
        assert outcomes.count(True) == 1
        assert db.scalar(select(func.count()).select_from(PlannerAccount)) == 1
        assert db.scalar(select(func.count()).select_from(PlannerAccount).where(PlannerAccount.is_administrator)) == 1
        credential_row = db.scalar(select(PlannerStartupCredential))
        assert credential_row is not None and credential_row.state == "consumed"
    engine.dispose()


def test_concurrent_setup_redemption_has_at_most_one_success(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'redemption-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        db.add(administrator); db.flush()
        access = create_planner_account(db, administrator_id=administrator.id, login_name="planer", display_name="Planung", clock=clock.now)
        raw_secret = access.raw_secret; account_id = access.account.id; db.commit()

    def redeem(_index: int) -> bool:
        with Session(engine) as db:
            try:
                redeem_account_access(db, access_credential=raw_secret, password="planer passwort", clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback()
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(redeem, (1, 2)))
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert outcomes.count(True) == 1
        assert account is not None and account.is_active and account.password_hash is not None
        assert db.scalar(select(func.count()).select_from(PlannerAccountAccess)) == 0
    engine.dispose()


def test_concurrent_duplicate_account_creation_has_one_complete_winner(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'account-create-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash="$argon2id$fixture", is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        db.add(administrator); db.commit(); administrator_id = administrator.id

    def create(index: int) -> bool:
        with Session(engine) as db:
            try:
                create_planner_account(db, administrator_id=administrator_id, login_name=" Planer " if index == 1 else "planer", display_name=f"Planung {index}", clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(create, (1, 2)))
    with Session(engine) as db:
        planners = list(db.scalars(select(PlannerAccount).where(PlannerAccount.is_administrator.is_(False))))
        assert outcomes.count(True) == 1
        assert len(planners) == 1 and not planners[0].is_active and planners[0].password_hash is None
        assert db.scalar(select(func.count()).select_from(PlannerAccountAccess).where(PlannerAccountAccess.account_id == planners[0].id)) == 1
    engine.dispose()


def test_concurrent_failed_logins_are_counted_without_lost_updates(tmp_path, monkeypatch):
    from app.services import planner_auth

    engine = create_engine(f"sqlite:///{tmp_path / 'failed-login-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    monkeypatch.setattr(planner_auth, "verify_password", lambda _encoded, _submitted: False)
    with Session(engine) as db:
        account = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash="$argon2id$fixture", is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        db.add(account); db.commit(); account_id = account.id

    def fail_login(_index: int) -> str:
        with Session(engine) as db:
            try:
                login_planner(db, login_name="admin", password="falsches passwort", clock=clock.now)
            except PlannerAuthFailure as exc:
                db.commit(); return exc.code
        raise AssertionError("wrong password unexpectedly succeeded")

    with ThreadPoolExecutor(max_workers=10) as pool:
        outcomes = list(pool.map(fail_login, range(10)))
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert outcomes == ["login_failed"] * 10
        assert account is not None and account.failed_login_count == 10
        assert account.login_blocked_until == clock.now().replace(tzinfo=None) + timedelta(minutes=15)
        assert db.scalar(select(func.count()).select_from(PlannerSession)) == 0
    engine.dispose()


def test_concurrent_setup_reissue_accepts_only_one_current_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'setup-reissue-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        db.add(administrator); db.flush()
        issued = create_planner_account(db, administrator_id=administrator.id, login_name="planer", display_name="Planung", clock=clock.now)
        administrator_id = administrator.id; account_id = issued.account.id; revision = issued.account.revision; db.commit()

    def reissue(_index: int) -> bool:
        with Session(engine) as db:
            try:
                reissue_setup_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=revision, clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reissue, (1, 2)))
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert outcomes.count(True) == 1
        assert account is not None and account.revision == revision + 1
        assert db.scalar(select(func.count()).select_from(PlannerAccountAccess)) == 1
    engine.dispose()


def test_concurrent_reactivation_reissue_accepts_only_one_current_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'reactivation-reissue-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        planner = PlannerAccount(login_name="planer", normalized_login_name="planer", display_name="Planung", password_hash=None, is_active=False, is_administrator=False, revision=3, created_at=clock.now(), disabled_at=clock.now())
        db.add_all([administrator, planner]); db.commit()
        administrator_id = administrator.id; account_id = planner.id; revision = planner.revision

    def reissue(_index: int) -> bool:
        with Session(engine) as db:
            try:
                issue_reactivation_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=revision, clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reissue, (1, 2)))
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        access = db.scalar(select(PlannerAccountAccess).where(PlannerAccountAccess.account_id == account_id))
        assert outcomes.count(True) == 1
        assert account is not None and account.revision == revision + 1
        assert access is not None and access.purpose == "reactivation"
    engine.dispose()


def test_reset_racing_login_and_request_leaves_no_usable_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'reset-login-request-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        planner = PlannerAccount(login_name="planer", normalized_login_name="planer", display_name="Planung", password_hash=hash_password("planer passwort"), is_active=True, is_administrator=False, revision=1, created_at=clock.now())
        db.add_all([administrator, planner]); db.commit()
        administrator_id = administrator.id; account_id = planner.id
        existing = login_planner(db, login_name="planer", password="planer passwort", clock=clock.now); db.commit(); old_secret = existing.raw_secret

    def reset() -> bool:
        with Session(engine) as db:
            issue_reset_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=1, clock=clock.now)
            db.commit(); return True

    def relogin() -> str | None:
        with Session(engine) as db:
            try:
                result = login_planner(db, login_name="planer", password="planer passwort", clock=clock.now)
                db.commit(); return result.raw_secret
            except PlannerAuthFailure:
                db.commit(); return None

    def request() -> bool:
        with Session(engine) as db:
            try:
                authenticate_session(db, old_secret, clock=clock.now); return True
            except PlannerAuthFailure:
                db.commit(); return False

    with ThreadPoolExecutor(max_workers=3) as pool:
        reset_future = pool.submit(reset); login_future = pool.submit(relogin); request_future = pool.submit(request)
        assert reset_future.result() is True
        replacement_secret = login_future.result()
        assert request_future.result() in {True, False}

    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert account is not None and account.password_hash is None and account.revision == 2
        assert db.scalar(select(func.count()).select_from(PlannerSession).where(PlannerSession.account_id == account_id)) == 0
        access = db.scalar(select(PlannerAccountAccess).where(PlannerAccountAccess.account_id == account_id))
        assert access is not None and access.purpose == "reset"
        for secret in (old_secret, replacement_secret):
            if secret is not None:
                with pytest.raises(PlannerAuthFailure):
                    authenticate_session(db, secret, clock=clock.now)
                db.rollback()
    engine.dispose()


def test_disable_racing_reset_redemption_finishes_inactive_without_access(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'disable-redemption-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        planner = PlannerAccount(login_name="planer", normalized_login_name="planer", display_name="Planung", password_hash=hash_password("planer passwort"), is_active=True, is_administrator=False, revision=1, created_at=clock.now())
        db.add_all([administrator, planner]); db.commit(); administrator_id = administrator.id; account_id = planner.id
        reset = issue_reset_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=1, clock=clock.now); db.commit(); raw_secret = reset.raw_secret

    def disable() -> bool:
        with Session(engine) as db:
            disable_account(db, administrator_id=administrator_id, account_id=account_id, expected_revision=2, clock=clock.now)
            db.commit(); return True

    def redeem() -> bool:
        with Session(engine) as db:
            try:
                redeem_account_access(db, access_credential=raw_secret, password="neues passwort", clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        disabled, redeemed = pool.submit(disable), pool.submit(redeem)
        assert disabled.result() is True
        assert redeemed.result() in {True, False}
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert account is not None and not account.is_active and account.password_hash is None and account.revision == 3
        assert db.scalar(select(func.count()).select_from(PlannerAccountAccess).where(PlannerAccountAccess.account_id == account_id)) == 0
        assert db.scalar(select(func.count()).select_from(PlannerSession).where(PlannerSession.account_id == account_id)) == 0
    engine.dispose()


def test_disable_racing_request_invalidates_every_later_request(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'disable-request-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        planner = PlannerAccount(login_name="planer", normalized_login_name="planer", display_name="Planung", password_hash=hash_password("planer passwort"), is_active=True, is_administrator=False, revision=1, created_at=clock.now())
        db.add_all([administrator, planner]); db.commit(); administrator_id = administrator.id; account_id = planner.id
        login = login_planner(db, login_name="planer", password="planer passwort", clock=clock.now); db.commit(); raw_secret = login.raw_secret

    def disable() -> bool:
        with Session(engine) as db:
            disable_account(db, administrator_id=administrator_id, account_id=account_id, expected_revision=1, clock=clock.now)
            db.commit(); return True

    def request() -> bool:
        with Session(engine) as db:
            try:
                authenticate_session(db, raw_secret, clock=clock.now); return True
            except PlannerAuthFailure:
                db.commit(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        disable_future = pool.submit(disable)
        request_future = pool.submit(request)
        assert disable_future.result() is True
        assert request_future.result() in {True, False}
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert account is not None and not account.is_active and account.password_hash is None
        with pytest.raises(PlannerAuthFailure):
            authenticate_session(db, raw_secret, clock=clock.now)
        db.commit()
        assert db.scalar(select(func.count()).select_from(PlannerSession).where(PlannerSession.account_id == account_id)) == 0
    engine.dispose()


def test_reactivation_reissue_racing_redemption_has_one_credential_outcome(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'reactivation-redemption-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        planner = PlannerAccount(login_name="planer", normalized_login_name="planer", display_name="Planung", password_hash=None, is_active=False, is_administrator=False, revision=3, created_at=clock.now(), disabled_at=clock.now())
        db.add_all([administrator, planner]); db.commit(); administrator_id = administrator.id; account_id = planner.id
        initial = issue_reactivation_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=3, clock=clock.now); db.commit(); raw_secret = initial.raw_secret

    def reissue() -> bool:
        with Session(engine) as db:
            try:
                issue_reactivation_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=4, clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    def redeem() -> bool:
        with Session(engine) as db:
            try:
                redeem_account_access(db, access_credential=raw_secret, password="neues passwort", clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        reissue_future = pool.submit(reissue)
        redeem_future = pool.submit(redeem)
        outcomes = [reissue_future.result(), redeem_future.result()]
    assert outcomes.count(True) == 1
    with Session(engine) as db:
        account = db.get(PlannerAccount, account_id)
        assert account is not None and account.revision == 5
        access_count = db.scalar(select(func.count()).select_from(PlannerAccountAccess).where(PlannerAccountAccess.account_id == account_id))
        assert (account.is_active and account.password_hash is not None and access_count == 0) or (not account.is_active and account.password_hash is None and access_count == 1)
        with pytest.raises(PlannerAuthFailure):
            issue_reactivation_access(db, administrator_id=administrator_id, account_id=account_id, expected_revision=4, clock=clock.now)
        db.rollback()
    engine.dispose()


def test_competing_transfers_keep_exactly_one_administrator(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'transfer-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        accounts = [
            PlannerAccount(login_name=name, normalized_login_name=name, display_name=name.title(), password_hash=hash_password(f"{name} passwort"), is_active=True, is_administrator=name == "admin", revision=1, created_at=clock.now())
            for name in ("admin", "planer-a", "planer-b")
        ]
        db.add_all(accounts); db.commit()
        administrator_id, first_id, second_id = [item.id for item in accounts]

    def transfer(target_id: int) -> bool:
        with Session(engine) as db:
            try:
                transfer_administration(db, administrator_id=administrator_id, target_id=target_id, expected_administrator_revision=1, expected_target_revision=1)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback()
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(transfer, (first_id, second_id)))
    with Session(engine) as db:
        assert outcomes.count(True) == 1
        assert db.scalar(select(func.count()).select_from(PlannerAccount).where(PlannerAccount.is_administrator)) == 1
    engine.dispose()


def test_target_disablement_racing_transfer_has_one_complete_winner(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'disable-transfer-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock()
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("admin passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        target = PlannerAccount(login_name="planer", normalized_login_name="planer", display_name="Planung", password_hash=hash_password("planer passwort"), is_active=True, is_administrator=False, revision=1, created_at=clock.now())
        db.add_all([administrator, target]); db.commit(); administrator_id = administrator.id; target_id = target.id

    start = Barrier(2)

    def disable() -> bool:
        with Session(engine) as db:
            start.wait()
            try:
                disable_account(db, administrator_id=administrator_id, account_id=target_id, expected_revision=1, clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    def transfer() -> bool:
        with Session(engine) as db:
            start.wait()
            try:
                transfer_administration(db, administrator_id=administrator_id, target_id=target_id, expected_administrator_revision=1, expected_target_revision=1)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        disable_future = pool.submit(disable)
        transfer_future = pool.submit(transfer)
        outcomes = [disable_future.result(), transfer_future.result()]
    with Session(engine) as db:
        administrator = db.get(PlannerAccount, administrator_id)
        target = db.get(PlannerAccount, target_id)
        assert outcomes.count(True) == 1
        assert administrator is not None and target is not None
        assert sum(account.is_administrator for account in (administrator, target)) == 1
        assert (target.is_administrator and target.is_active) or (administrator.is_administrator and not target.is_active)
    engine.dispose()


def test_concurrent_recovery_consumes_startup_credential_once(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'recovery-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock(); credential = startup_credential(31)
    with Session(engine) as db:
        account = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("altes passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        db.add(account); reconcile_startup_credentials(db, bootstrap_credential=None, recovery_credential=credential, clock=clock.now); db.commit()

    def recover(index: int) -> bool:
        with Session(engine) as db:
            try:
                recover_administrator(db, startup_credential=credential, password=f"neues passwort {index}", clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.rollback()
                return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(recover, (1, 2)))
    with Session(engine) as db:
        assert outcomes.count(True) == 1
        startup = db.scalar(select(PlannerStartupCredential).where(PlannerStartupCredential.purpose == "recovery"))
        assert startup is not None and startup.state == "consumed"
        assert db.scalar(select(func.count()).select_from(PlannerAccount).where(PlannerAccount.is_administrator)) == 1
    engine.dispose()


def test_recovery_racing_current_session_login_leaves_only_recovered_access(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'recovery-login-race.db'}", connect_args={"check_same_thread": False, "timeout": 10})
    initialize_database(engine); clock = DeterministicUtcClock(); credential = startup_credential(41); session_secret = "s" * 43
    with Session(engine) as db:
        administrator = PlannerAccount(login_name="admin", normalized_login_name="admin", display_name="Administration", password_hash=hash_password("altes passwort"), is_active=True, is_administrator=True, revision=1, created_at=clock.now())
        db.add(administrator); db.flush(); administrator_id = administrator.id
        db.add(PlannerSession(account_id=administrator_id, secret_digest=hashlib.sha256(session_secret.encode("ascii")).hexdigest(), created_at=clock.now(), last_activity_at=clock.now(), absolute_expires_at=clock.now() + timedelta(hours=12)))
        reconcile_startup_credentials(db, bootstrap_credential=None, recovery_credential=credential, clock=clock.now); db.commit()

    start = Barrier(2)

    def recover() -> None:
        with Session(engine) as db:
            start.wait()
            recover_administrator(db, startup_credential=credential, password="wiederhergestelltes passwort", clock=clock.now)
            db.commit()

    def login_with_old_password() -> bool:
        with Session(engine) as db:
            start.wait()
            try:
                login_planner(db, login_name="admin", password="altes passwort", clock=clock.now)
                db.commit(); return True
            except PlannerAuthFailure:
                db.commit(); return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        recovery_future = pool.submit(recover)
        login_future = pool.submit(login_with_old_password)
        recovery_future.result()
        login_future.result()
    with Session(engine) as db:
        administrator = db.get(PlannerAccount, administrator_id)
        startup = db.scalar(select(PlannerStartupCredential).where(PlannerStartupCredential.purpose == "recovery"))
        assert administrator is not None and administrator.is_administrator and administrator.is_active
        assert administrator.password_hash is not None and verify_password(administrator.password_hash, "wiederhergestelltes passwort")
        assert not verify_password(administrator.password_hash, "altes passwort")
        assert startup is not None and startup.state == "consumed"
        assert db.scalar(select(func.count()).select_from(PlannerSession).where(PlannerSession.account_id == administrator_id)) == 0
    engine.dispose()


def test_old_logout_finishing_after_replacement_login_preserves_new_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'logout-login-race.db'}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    initialize_database(engine)
    clock = DeterministicUtcClock()
    old_secret = "o" * 43
    with Session(engine) as db:
        account = PlannerAccount(
            login_name="planer",
            normalized_login_name="planer",
            display_name="Planung",
            password_hash=hash_password("sicheres passwort"),
            is_active=True,
            is_administrator=False,
            revision=1,
            created_at=clock.now(),
        )
        db.add(account)
        db.flush()
        account_id = account.id
        db.add(
            PlannerSession(
                account_id=account_id,
                secret_digest=hashlib.sha256(old_secret.encode("ascii")).hexdigest(),
                created_at=clock.now(),
                last_activity_at=clock.now(),
                absolute_expires_at=clock.now() + timedelta(hours=12),
            )
        )
        db.commit()

    replacement_ready = Event()
    old_request_authenticated = Event()

    def old_logout() -> None:
        with Session(engine) as db:
            authenticated = authenticate_session(db, old_secret, clock=clock.now)
            old_request_authenticated.set()
            assert replacement_ready.wait(timeout=10)
            end_authenticated_session(
                db,
                account_id=authenticated.account.id,
                secret_digest=authenticated.secret_digest,
            )
            db.commit()

    def replacement_login() -> str:
        assert old_request_authenticated.wait(timeout=10)
        with Session(engine) as db:
            result = login_planner(
                db,
                login_name="planer",
                password="sicheres passwort",
                clock=clock.now,
            )
            db.commit()
            replacement_ready.set()
            return result.raw_secret

    with ThreadPoolExecutor(max_workers=2) as pool:
        logout_future = pool.submit(old_logout)
        login_future = pool.submit(replacement_login)
        replacement_secret = login_future.result()
        logout_future.result()

    with Session(engine) as db:
        authenticated = authenticate_session(db, replacement_secret, clock=clock.now)
        assert authenticated.account.id == account_id
        assert db.scalar(
            select(func.count())
            .select_from(PlannerSession)
            .where(PlannerSession.account_id == account_id)
        ) == 1
    engine.dispose()
