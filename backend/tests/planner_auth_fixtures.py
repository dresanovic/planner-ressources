from __future__ import annotations

import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.schema import initialize_database


@dataclass
class DeterministicUtcClock:
    current: datetime = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current

    def advance(self, **delta: int) -> datetime:
        self.current += timedelta(**delta)
        return self.current


def startup_credential(fill: int = 1) -> str:
    """Return a valid, deterministic 32-byte startup credential as hex."""
    if not 0 <= fill <= 255:
        raise ValueError("fill must fit in one byte")
    return (bytes([fill]) * 32).hex()


def secret_digest(raw_secret: str) -> str:
    return hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()


def file_backed_engine(database_path: Path) -> Engine:
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    return engine


def add_planner_account(
    db: Session,
    *,
    login_name: str = "planner",
    display_name: str = "Planung Person",
    password_hash: str | None = "$argon2id$fixture",
    active: bool = True,
    administrator: bool = False,
    now: datetime | None = None,
):
    from app.models.planning import PlannerAccount

    account = PlannerAccount(
        login_name=login_name.strip(),
        normalized_login_name=login_name.strip().casefold(),
        display_name=display_name.strip(),
        password_hash=password_hash,
        is_active=active,
        is_administrator=administrator,
        failed_login_count=0,
        revision=1,
        created_at=now or datetime.now(timezone.utc),
    )
    db.add(account)
    db.flush()
    return account


def add_current_session(
    db: Session,
    *,
    account_id: int,
    raw_secret: str = "s" * 43,
    now: datetime | None = None,
) -> tuple[object, str]:
    from app.models.planning import PlannerSession

    created_at = now or datetime.now(timezone.utc)
    session = PlannerSession(
        account_id=account_id,
        secret_digest=secret_digest(raw_secret),
        created_at=created_at,
        last_activity_at=created_at,
        absolute_expires_at=created_at + timedelta(hours=12),
    )
    db.add(session)
    db.flush()
    return session, raw_secret


def authenticate_test_client(
    client: TestClient,
    db: Session,
    *,
    administrator: bool = True,
    login_name: str = "fixture-planner",
) -> object:
    """Authenticate an existing client through the real persistence boundary."""
    account = add_planner_account(
        db,
        login_name=login_name,
        display_name="Fixture Administration" if administrator else "Fixture Planung",
        administrator=administrator,
    )
    _, raw_secret = add_current_session(db, account_id=account.id)
    db.commit()
    client.cookies.set("planner_session", raw_secret)
    client.headers.update(
        {
            "X-CSRF-Protection": "1",
            "X-Planner-Activity": "user",
            "Content-Type": "application/json",
        }
    )
    return account


@contextmanager
def authenticated_planner_client(
    monkeypatch,
    database_path: Path,
    *,
    administrator: bool = False,
    clock: DeterministicUtcClock | None = None,
) -> Iterator[tuple[TestClient, Session, object]]:
    """Create a real persisted account/session and present its cookie to TestClient.

    This helper deliberately uses the production authentication tables and normal
    request middleware. It does not install an authorization bypass.
    """
    from app import main as app_main
    from app.db.session import get_db

    engine = file_backed_engine(database_path)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = session_factory()
    now = (clock or DeterministicUtcClock()).now()
    account = add_planner_account(
        db,
        login_name="administrator" if administrator else "planner",
        display_name="Systemadministration" if administrator else "Planung Person",
        administrator=administrator,
        now=now,
    )
    _, raw_secret = add_current_session(db, account_id=account.id, now=now)
    db.commit()

    def override_get_db():
        yield db

    app_main.app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(app_main, "SessionLocal", session_factory)
    try:
        with TestClient(app_main.app) as client:
            client.cookies.set("planner_session", raw_secret)
            yield client, db, account
    finally:
        app_main.app.dependency_overrides.clear()
        db.close()
        engine.dispose()
