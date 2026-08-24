from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app import main as app_main
from app.db.schema import initialize_database
from app.db.session import get_db
from app.models.planning import PlannerAccount, PlannerSession
from app.services.planner_auth import reconcile_startup_credentials
from tests.planner_auth_fixtures import startup_credential


@pytest.fixture
def client_and_db(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'planner-auth-api.db'}",
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = factory()
    credential = startup_credential(11)
    reconcile_startup_credentials(
        db,
        bootstrap_credential=credential,
        recovery_credential=None,
        clock=lambda: datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    db.commit()

    app_main.app.dependency_overrides[get_db] = lambda: (yield db)
    monkeypatch.setattr(app_main, "SessionLocal", factory)
    monkeypatch.setenv("APP_ENV", "development")
    with TestClient(app_main.app) as client:
        yield client, db, credential
    app_main.app.dependency_overrides.clear()
    db.close()
    engine.dispose()


def test_bootstrap_login_session_and_minimal_administrator_listing(client_and_db):
    client, db, credential = client_and_db
    csrf = {"X-CSRF-Protection": "1"}
    bootstrap = client.post(
        "/api/auth/bootstrap",
        headers=csrf,
        json={
            "startupCredential": credential,
            "loginName": "  Admin  ",
            "displayName": "System Administration",
            "password": "sicheres passwort",
        },
    )
    assert bootstrap.status_code == 204
    assert bootstrap.headers["cache-control"] == "no-store"
    assert not client.cookies

    second = client.post(
        "/api/auth/bootstrap",
        headers=csrf,
        json={
            "startupCredential": credential,
            "loginName": "andere",
            "displayName": "Andere",
            "password": "anderes passwort",
        },
    )
    assert second.status_code in {400, 409}
    assert "Startzugang" in second.json()["message"]
    assert db.scalar(select(PlannerAccount).where(PlannerAccount.is_administrator)).login_name == "Admin"

    failed = client.post(
        "/api/auth/login",
        headers=csrf,
        json={"loginName": "Admin", "password": "falsches passwort"},
    )
    assert failed.status_code == 401
    assert failed.json() == {
        "code": "login_failed",
        "message": "Die Anmeldung war nicht möglich. Prüfen Sie Ihre Angaben und versuchen Sie es erneut. Wenn Sie weiterhin keinen Zugang haben, wenden Sie sich an die Systemadministration.",
    }

    login = client.post(
        "/api/auth/login",
        headers=csrf,
        json={"loginName": " admin ", "password": "sicheres passwort"},
    )
    assert login.status_code == 200
    assert login.json() == {
        "id": 1,
        "loginName": "Admin",
        "displayName": "System Administration",
        "isAdministrator": True,
    }
    cookie = login.headers["set-cookie"]
    assert "planner_session=" in cookie
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert "Max-Age" not in cookie and "expires=" not in cookie.casefold()

    inspection = client.get("/api/auth/session")
    assert inspection.status_code == 200
    assert inspection.json() == login.json()
    accounts = client.get("/api/planner-accounts", headers={"X-Planner-Activity": "user"})
    assert accounts.status_code == 200
    assert set(accounts.json()["accounts"][0]) == {
        "id", "loginName", "displayName", "accessLevel", "state", "revision", "createdAt", "disabledAt", "reactivatedAt"
    }
    serialized = accounts.text.casefold()
    assert "password" not in serialized and "secret" not in serialized and "failed" not in serialized


def test_production_cookie_is_host_prefixed_and_secure(client_and_db, monkeypatch):
    client, db, credential = client_and_db
    monkeypatch.setenv("APP_ENV", "production")
    client.post(
        "/api/auth/bootstrap",
        headers={"X-CSRF-Protection": "1"},
        json={"startupCredential": credential, "loginName": "admin", "displayName": "Admin", "password": "sicheres passwort"},
    )
    response = client.post(
        "/api/auth/login",
        headers={"X-CSRF-Protection": "1"},
        json={"loginName": "admin", "password": "sicheres passwort"},
    )
    assert "__Host-planner_session=" in response.headers["set-cookie"]
    assert "Secure" in response.headers["set-cookie"]


def test_bootstrap_and_login_require_json_and_csrf(client_and_db):
    client, _, _ = client_and_db
    assert client.post("/api/auth/login", json={"loginName": "x", "password": "a" * 12}).status_code == 403
    assert client.post(
        "/api/auth/login",
        headers={"X-CSRF-Protection": "1", "Content-Type": "text/plain"},
        content='{"loginName":"x","password":"aaaaaaaaaaaa"}',
    ).status_code == 415


def test_short_submitted_login_password_uses_generic_failure_and_retry_accounting(client_and_db):
    client, db, credential = client_and_db
    csrf = {"X-CSRF-Protection": "1"}
    assert client.post(
        "/api/auth/bootstrap",
        headers=csrf,
        json={
            "startupCredential": credential,
            "loginName": "admin",
            "displayName": "Administration",
            "password": "sicheres passwort",
        },
    ).status_code == 204

    response = client.post(
        "/api/auth/login",
        headers=csrf,
        json={"loginName": "admin", "password": "kurz"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "login_failed",
        "message": "Die Anmeldung war nicht möglich. Prüfen Sie Ihre Angaben und versuchen Sie es erneut. Wenn Sie weiterhin keinen Zugang haben, wenden Sie sich an die Systemadministration.",
    }
    db.expire_all()
    assert db.scalar(select(PlannerAccount)).failed_login_count == 1


def test_complete_account_administration_and_one_time_access_contract(client_and_db):
    client, db, credential = client_and_db
    csrf = {"X-CSRF-Protection": "1"}
    assert client.post("/api/auth/bootstrap", headers=csrf, json={"startupCredential": credential, "loginName": "admin", "displayName": "Administration", "password": "admin passwort"}).status_code == 204
    assert client.post("/api/auth/login", headers=csrf, json={"loginName": "admin", "password": "admin passwort"}).status_code == 200

    created = client.post("/api/planner-accounts", headers=csrf, json={"loginName": "planner", "displayName": "Planung Person"})
    assert created.status_code == 201
    assert created.json()["account"]["state"] == "inactive"
    setup = created.json()["oneTimeAccess"]
    assert set(setup) == {"credential", "purpose", "expiresAt"} and setup["purpose"] == "setup"
    assert len(setup["credential"]) == 43

    redeemed = client.post("/api/auth/account-access/redemption", headers=csrf, json={"accessCredential": setup["credential"], "password": "planner passwort"})
    assert redeemed.status_code == 204
    assert client.post("/api/auth/account-access/redemption", headers=csrf, json={"accessCredential": setup["credential"], "password": "anderes passwort"}).status_code in {400, 409}

    accounts = client.get("/api/planner-accounts").json()["accounts"]
    planner = next(item for item in accounts if item["loginName"] == "planner")
    reset = client.post(f"/api/planner-accounts/{planner['id']}/reset-access", headers=csrf, json={"expectedRevision": planner["revision"]})
    assert reset.status_code == 200 and reset.json()["oneTimeAccess"]["purpose"] == "reset"
    assert client.post("/api/auth/account-access/redemption", headers=csrf, json={"accessCredential": reset.json()["oneTimeAccess"]["credential"], "password": "neues passwort"}).status_code == 204

    planner = next(item for item in client.get("/api/planner-accounts").json()["accounts"] if item["loginName"] == "planner")
    disabled = client.post(f"/api/planner-accounts/{planner['id']}/disable", headers=csrf, json={"expectedRevision": planner["revision"]})
    assert disabled.status_code == 200 and disabled.json()["state"] == "inactive" and disabled.json()["disabledAt"]
    reactivation = client.post(f"/api/planner-accounts/{planner['id']}/reactivation-access", headers=csrf, json={"expectedRevision": disabled.json()["revision"]})
    assert reactivation.status_code == 200 and reactivation.json()["oneTimeAccess"]["purpose"] == "reactivation"
    assert client.post("/api/auth/account-access/redemption", headers=csrf, json={"accessCredential": reactivation.json()["oneTimeAccess"]["credential"], "password": "wieder passwort"}).status_code == 204

    accounts = client.get("/api/planner-accounts").json()["accounts"]
    admin = next(item for item in accounts if item["accessLevel"] == "administrator")
    planner = next(item for item in accounts if item["loginName"] == "planner")
    transferred = client.post(f"/api/planner-accounts/{planner['id']}/administrator-transfer", headers=csrf, json={"expectedTargetRevision": planner["revision"], "expectedAdministratorRevision": admin["revision"]})
    assert transferred.status_code == 200 and transferred.json()["isAdministrator"] is False
    assert client.get("/api/planner-accounts").status_code == 403

    recovery_credential = startup_credential(12)
    reconcile_startup_credentials(db, bootstrap_credential=None, recovery_credential=recovery_credential)
    db.commit(); client.cookies.clear()
    recovered = client.post("/api/auth/administrator-recovery", headers=csrf, json={"startupCredential": recovery_credential, "password": "wiederhergestelltes passwort"})
    assert recovered.status_code == 204 and not client.cookies
    assert client.post("/api/auth/administrator-recovery", headers=csrf, json={"startupCredential": recovery_credential, "password": "noch ein neues passwort"}).status_code == 400
    assert client.post("/api/auth/login", headers=csrf, json={"loginName": "planner", "password": "wieder passwort"}).status_code == 401
    recovered_login = client.post("/api/auth/login", headers=csrf, json={"loginName": "planner", "password": "wiederhergestelltes passwort"})
    assert recovered_login.status_code == 200 and recovered_login.json()["isAdministrator"] is True


def test_session_replacement_logout_password_change_and_expiry(client_and_db):
    client, db, credential = client_and_db; csrf = {"X-CSRF-Protection": "1"}
    client.post("/api/auth/bootstrap", headers=csrf, json={"startupCredential": credential, "loginName": "admin", "displayName": "Administration", "password": "admin passwort"})
    first = client.post("/api/auth/login", headers=csrf, json={"loginName": "admin", "password": "admin passwort"}); assert first.status_code == 200
    first_secret = client.cookies.get("planner_session", domain="testserver.local", path="/")
    failed = client.post("/api/auth/login", headers=csrf, json={"loginName": "admin", "password": "falsches passwort"}); assert failed.status_code == 401
    client.cookies.set("planner_session", first_secret, domain="testserver.local", path="/"); assert client.get("/api/auth/session").status_code == 200

    second = client.post("/api/auth/login", headers=csrf, json={"loginName": "admin", "password": "admin passwort"}); assert second.status_code == 200
    second_secret = client.cookies.get("planner_session", domain="testserver.local", path="/"); assert second_secret != first_secret
    client.cookies.set("planner_session", first_secret, domain="testserver.local", path="/"); assert client.get("/api/auth/session").status_code == 401
    client.cookies.set("planner_session", second_secret, domain="testserver.local", path="/")
    changed = client.post("/api/auth/password-change", headers=csrf, json={"currentPassword": "admin passwort", "newPassword": "neues admin passwort"}); assert changed.status_code == 204
    client.cookies.set("planner_session", second_secret, domain="testserver.local", path="/"); assert client.get("/api/auth/session").status_code == 401
    assert client.post("/api/auth/login", headers=csrf, json={"loginName": "admin", "password": "neues admin passwort"}).status_code == 200

    session = db.scalar(select(PlannerSession)); assert session is not None
    now = datetime.now(timezone.utc)
    session.created_at = now - timedelta(minutes=61)
    session.last_activity_at = now - timedelta(minutes=60)
    session.absolute_expires_at = now + timedelta(hours=11)
    db.commit()
    assert client.get("/api/auth/session").status_code == 401
    assert db.scalar(select(PlannerSession)) is None
