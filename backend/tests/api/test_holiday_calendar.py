from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import pytest

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: (yield db)
    try:
        with TestClient(app) as value:
            yield value
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_holiday_crud_contract_and_no_history(client):
    created = client.post("/api/holidays", json={"date": "2026-12-25", "name": " Winter Holiday "})
    assert created.status_code == 201
    assert created.json()["name"] == "Winter Holiday"
    holiday_id = created.json()["id"]
    assert client.get(f"/api/holidays/{holiday_id}").json() == created.json()
    updated = client.patch(
        f"/api/holidays/{holiday_id}",
        json={"date": "2026-12-24", "name": "Winter Break", "expectedRevision": 1},
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    assert client.get("/api/holidays").json() == [updated.json()]
    assert client.delete(f"/api/holidays/{holiday_id}?expectedRevision=2&confirmed=true").status_code == 204
    assert client.get("/api/holidays").json() == []


def test_duplicate_stale_confirmation_and_validation_errors(client):
    first = client.post("/api/holidays", json={"date": "2026-12-24", "name": "First"}).json()
    duplicate = client.post("/api/holidays", json={"date": "2026-12-24", "name": "Second"})
    assert duplicate.status_code == 409
    assert duplicate.json()["errors"][0]["code"] == "DUPLICATE_HOLIDAY_DATE"
    assert client.delete(f"/api/holidays/{first['id']}?expectedRevision=1&confirmed=false").status_code == 422
    changed = client.patch(
        f"/api/holidays/{first['id']}",
        json={"date": "2026-12-24", "name": "Changed", "expectedRevision": 1},
    )
    assert changed.status_code == 200
    stale = client.patch(
        f"/api/holidays/{first['id']}",
        json={"date": "2026-12-24", "name": "Old", "expectedRevision": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["errors"][0]["meta"]["currentRevision"] == 2
    invalid = client.post("/api/holidays", json={"date": "2026-12-25", "name": " "})
    assert invalid.status_code == 422

    invalid_date = client.post("/api/holidays", json={"date": "2026-02-30", "name": "Impossible"})
    assert invalid_date.status_code == 422
    assert invalid_date.json()["errors"][0]["code"] == "VALIDATION_ERROR"
    assert invalid_date.json()["errors"][0]["field"] == "date"

    datetime_date = client.post(
        "/api/holidays",
        json={"date": "2026-12-25T00:00:00", "name": "Not date-only"},
    )
    assert datetime_date.status_code == 422
    assert datetime_date.json()["errors"][0]["field"] == "date"

    extra = client.post("/api/holidays", json={"date": "2026-12-25", "name": "Valid", "source": "ical"})
    assert extra.status_code == 422
    assert extra.json()["errors"][0]["field"] == "source"
