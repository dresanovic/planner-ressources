import hashlib
import re
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app import main as app_main
from app.db.schema import initialize_database
from app.models.planning import Cohort, LecturerReviewLink, PlannerAccount, PlannerSession
from tests.lecturer_review_fixtures import seed_lecturer_review_fixture


def _registered_protected_operations():
    operations: list[tuple[str, str]] = []
    def flattened(routes):
        for route in routes:
            original_router = getattr(route, "original_router", None)
            if original_router is not None:
                yield from flattened(original_router.routes)
            else:
                yield route

    for route in flattened(app_main.app.routes):
        path = getattr(route, "path", "")
        if not path.startswith("/api/"):
            continue
        concrete = re.sub(r"\{[^}]+\}", "1", path)
        for method in sorted(getattr(route, "methods", set()) - {"HEAD", "OPTIONS"}):
            if (method, path) not in app_main._PUBLIC_API_OPERATIONS:
                operations.append((method, concrete))
    return operations


def _request(client: TestClient, method: str, path: str, *, bearer: str | None = None):
    headers = {"X-CSRF-Protection": "1", "Content-Type": "application/json"}
    if bearer is not None:
        headers["Authorization"] = f"Bearer {bearer}"
    return client.request(method, path, headers=headers, json={} if method not in {"GET", "DELETE"} else None)


def _sqlite_snapshot(engine) -> tuple[str, ...]:
    connection = engine.raw_connection()
    try:
        return tuple(connection.driver_connection.iterdump())
    finally:
        connection.close()


def test_planner_apis_default_deny_before_validation_and_mutation(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'authorization.db'}",
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(app_main, "SessionLocal", factory)
    with TestClient(app_main.app) as client:
        for cookie in (None, "malformed", "unknown-session-secret"):
            client.cookies.clear()
            if cookie is not None:
                client.cookies.set("planner_session", cookie)
            response = client.post(
                "/api/academic/cohorts",
                headers={"X-CSRF-Protection": "1"},
                json={"not": "a valid cohort"},
            )
            assert response.status_code == 401
            assert response.json()["message"] == "Ihre Sitzung ist beendet. Melden Sie sich erneut an."
        with Session(engine) as db:
            assert db.scalar(select(func.count()).select_from(Cohort)) == 0
        assert client.get("/health").status_code == 200
        assert client.get("/health", headers={"Accept": "text/html"}, follow_redirects=False).status_code == 200
        assert client.get("/api/public/ui-terminology").status_code == 200
        assert client.get("/docs").status_code == 401
        assert client.get("/openapi.json").status_code == 401
        for path in ("/", "/index.html", "/planner-near-miss"):
            for accept in (None, "*/*", "text/html"):
                headers = {} if accept is None else {"Accept": accept}
                page = client.get(path, headers=headers, follow_redirects=False)
                assert page.status_code == 307, (path, accept, page.status_code)
                assert page.headers["location"] == "/login/"
    engine.dispose()


def test_unsafe_public_auth_routes_have_only_exact_exceptions(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'exact-public.db'}", connect_args={"check_same_thread": False})
    initialize_database(engine)
    monkeypatch.setattr(app_main, "SessionLocal", sessionmaker(bind=engine))
    with TestClient(app_main.app) as client:
        assert client.post(
            "/api/auth/login",
            headers={"X-CSRF-Protection": "1"},
            json={"loginName": "nobody", "password": "a" * 12},
        ).status_code == 401
        assert client.post(
            "/api/auth/login/near-miss",
            headers={"X-CSRF-Protection": "1"},
            json={},
        ).status_code == 401
    engine.dispose()


def test_every_registered_planner_operation_denies_every_invalid_session_state(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'authorization-matrix.db'}", connect_args={"check_same_thread": False})
    initialize_database(engine); factory = sessionmaker(bind=engine)
    monkeypatch.setattr(app_main, "SessionLocal", factory)
    operations = _registered_protected_operations()
    assert len(operations) >= 50
    now = datetime.now(timezone.utc)

    with TestClient(app_main.app) as client:
        for method, path in operations:
            for raw in (None, "malformed", "u" * 43):
                client.cookies.clear()
                if raw is not None:
                    client.cookies.set("planner_session", raw)
                response = _request(client, method, path)
                assert response.status_code == 401, (method, path, raw, response.text)
                assert response.headers["cache-control"] == "no-store"

        with factory() as db:
            account = PlannerAccount(login_name="matrix", normalized_login_name="matrix", display_name="Matrix", password_hash="$argon2id$not-verified", is_active=True, is_administrator=False, revision=1, created_at=now)
            db.add(account); db.commit(); account_id = account.id

        states = ("replaced", "inactive", "passwordless", "inactivity-expired", "absolute-expired")
        for state in states:
            for index, (method, path) in enumerate(operations):
                raw = f"{states.index(state) + 1}{index:042d}"
                with factory() as db:
                    account = db.get(PlannerAccount, account_id)
                    account.is_active = state != "inactive"
                    account.password_hash = None if state == "passwordless" else "$argon2id$not-verified"
                    db.query(PlannerSession).filter(PlannerSession.account_id == account_id).delete()
                    current_raw = ("z" * 42 + str(index % 10)) if state == "replaced" else raw
                    created = now - timedelta(hours=13) if state == "absolute-expired" else now - timedelta(minutes=61)
                    last_activity = now - timedelta(minutes=60) if state == "inactivity-expired" else now - timedelta(minutes=1)
                    absolute = now if state == "absolute-expired" else now + timedelta(hours=11)
                    db.add(PlannerSession(account_id=account_id, secret_digest=hashlib.sha256(current_raw.encode("ascii")).hexdigest(), created_at=created, last_activity_at=last_activity, absolute_expires_at=absolute))
                    db.commit()
                client.cookies.clear(); client.cookies.set("planner_session", raw)
                response = _request(client, method, path)
                assert response.status_code == 401, (state, method, path, response.text)
                assert response.json()["code"] == "session_ended"
    engine.dispose()


def test_every_registered_planner_operation_rejects_every_stored_lecturer_state_without_mutation(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'lecturer-authorization-matrix.db'}",
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(app_main, "SessionLocal", factory)
    operations = _registered_protected_operations()
    now = datetime.now(timezone.utc)
    planner_secret = "p" * 43
    lecturer_secrets = {
        "active": "a" * 43,
        "ended": "e" * 43,
        "replaced": "r" * 43,
    }

    with factory() as db:
        seed_lecturer_review_fixture(db)
        planner = PlannerAccount(
            login_name="matrix-admin",
            normalized_login_name="matrix-admin",
            display_name="Matrix Administration",
            password_hash="$argon2id$not-verified",
            is_active=True,
            is_administrator=True,
            revision=1,
            created_at=now,
        )
        db.add(planner)
        db.flush()
        db.add(
            PlannerSession(
                account_id=planner.id,
                secret_digest=hashlib.sha256(planner_secret.encode("ascii")).hexdigest(),
                created_at=now,
                last_activity_at=now,
                absolute_expires_at=now + timedelta(hours=12),
            )
        )
        replacement = LecturerReviewLink(
            schedule_revision_id=2,
            lecturer_id=3,
            intended_lecturer_name="Katherine Johnson",
            secret_digest=hashlib.sha256(("n" * 43).encode("ascii")).hexdigest(),
            duration_days=1,
            issued_at=now,
            expires_at=now + timedelta(days=1),
            status="active",
        )
        db.add(replacement)
        db.flush()
        db.add_all(
            [
                LecturerReviewLink(
                    schedule_revision_id=2,
                    lecturer_id=1,
                    intended_lecturer_name="Ada Lovelace",
                    secret_digest=hashlib.sha256(lecturer_secrets["active"].encode("ascii")).hexdigest(),
                    duration_days=1,
                    issued_at=now,
                    expires_at=now + timedelta(days=1),
                    status="active",
                ),
                LecturerReviewLink(
                    schedule_revision_id=2,
                    lecturer_id=2,
                    intended_lecturer_name="Grace Hopper",
                    secret_digest=hashlib.sha256(lecturer_secrets["ended"].encode("ascii")).hexdigest(),
                    duration_days=1,
                    issued_at=now - timedelta(days=1),
                    expires_at=now + timedelta(days=1),
                    status="revoked",
                    ended_at=now,
                    end_reason="revoked",
                ),
                LecturerReviewLink(
                    schedule_revision_id=1,
                    lecturer_id=3,
                    intended_lecturer_name="Katherine Johnson",
                    secret_digest=hashlib.sha256(lecturer_secrets["replaced"].encode("ascii")).hexdigest(),
                    duration_days=1,
                    issued_at=now - timedelta(days=1),
                    expires_at=now + timedelta(days=1),
                    status="replaced",
                    ended_at=now,
                    end_reason="replaced",
                    replaced_by_id=replacement.id,
                ),
            ]
        )
        db.commit()

    with TestClient(app_main.app) as client:
        for method, path in operations:
            for state, bearer in lecturer_secrets.items():
                for has_planner_cookie in (False, True):
                    client.cookies.clear()
                    if has_planner_cookie:
                        client.cookies.set("planner_session", planner_secret)
                    before = _sqlite_snapshot(engine) if method not in {"GET", "HEAD", "OPTIONS"} else None
                    response = _request(client, method, path, bearer=bearer)
                    assert response.status_code == 403, (
                        state,
                        has_planner_cookie,
                        method,
                        path,
                        response.text,
                    )
                    assert response.json() == {
                        "code": "PLANNER_AUTHORIZATION_REQUIRED",
                        "message": "Planner authorization is required.",
                    }
                    if before is not None:
                        assert _sqlite_snapshot(engine) == before, (
                            state,
                            has_planner_cookie,
                            method,
                            path,
                        )
    engine.dispose()
