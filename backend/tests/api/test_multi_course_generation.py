import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import DraftSchedule


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override():
        yield db_session
    app.dependency_overrides[get_db] = override
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()


def _assert_retired(response):
    assert response.status_code == 410
    assert response.json() == {
        "code": "GENERATION_ENDPOINT_RETIRED",
        "message": "This generation endpoint has been retired. Use the unified conflict-aware workflow.",
        "replacement": {
            "preparePath": "/api/draft-schedules/optimization/prepare",
            "generatePath": "/api/draft-schedules/optimization/generate",
        },
    }


def test_legacy_batch_prepare_is_retired_without_mutation(client, db_session):
    before = db_session.query(DraftSchedule).count()
    response = client.post("/api/draft-schedules/batch/prepare", json={"anything": "ignored"})
    _assert_retired(response)
    assert db_session.query(DraftSchedule).count() == before


def test_legacy_batch_generate_is_retired_without_mutation(client, db_session):
    before = db_session.query(DraftSchedule).count()
    response = client.post("/api/draft-schedules/batch/generate", json={"anything": "ignored"})
    _assert_retired(response)
    assert db_session.query(DraftSchedule).count() == before


@pytest.mark.parametrize("path", [
    "/api/draft-schedules/batch/prepare",
    "/api/draft-schedules/batch/generate",
])
def test_legacy_batch_openapi_documents_deprecation_and_only_gone(client, path):
    operation = client.get("/openapi.json").json()["paths"][path]["post"]

    assert operation["deprecated"] is True
    assert "requestBody" not in operation
    assert "410" in operation["responses"]
    assert "200" not in operation["responses"]
