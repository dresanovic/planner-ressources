from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import pytest

from app.db.schema import initialize_database
from app.db.session import get_db
from app.main import app
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester


@pytest.fixture()
def client_and_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    initialize_database(engine)
    with Session(engine) as db:
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            yield client, db
        app.dependency_overrides.clear()


def test_lifecycle_api_supports_start_draft_prepare_and_explicit_publish(client_and_db):
    client, db = client_and_db
    seed_lifecycle_semester(db, with_schedule=True)

    overview_response = client.get("/api/semesters/1/schedule-lifecycle")
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["allowedActions"]["createWorkingRevision"] is True

    created_response = client.post(
        "/api/semesters/1/schedule-revisions",
        json={"expectedStateToken": overview["stateToken"]},
    )
    assert created_response.status_code == 201
    created = created_response.json()
    revision = created["activeWorkingRevision"]
    assert revision["createdAt"].endswith("Z")

    preparation_response = client.post(
        f"/api/schedule-revisions/{revision['revisionId']}/publication-preparation",
        json={
            "expectedRevisionVersion": revision["revisionVersion"],
            "expectedStateToken": created["stateToken"],
        },
    )
    assert preparation_response.status_code == 200
    preparation = preparation_response.json()
    assert preparation["conditions"]

    publish_response = client.post(
        f"/api/schedule-revisions/{revision['revisionId']}/transitions",
        json={
            "action": "publish",
            "expectedRevisionVersion": revision["revisionVersion"],
            "expectedStateToken": created["stateToken"],
            "confirmed": True,
            "publicationToken": preparation["preparationToken"],
        },
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["currentPublication"]["state"] == "published"

    detail_response = client.get(
        f"/api/schedule-revisions/{revision['revisionId']}"
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["contentSource"] == "captured_snapshot"


def test_lifecycle_api_returns_structured_not_found_conflict_and_validation(client_and_db):
    client, db = client_and_db
    seed_lifecycle_semester(db, with_schedule=False)

    missing = client.get("/api/semesters/999/schedule-lifecycle")
    assert missing.status_code == 404
    assert missing.json()["errors"][0]["code"] == "semester_not_found"

    overview = client.get("/api/semesters/1/schedule-lifecycle").json()
    stale = client.post(
        "/api/semesters/1/schedule-revisions",
        json={"expectedStateToken": "stale"},
    )
    assert stale.status_code == 409
    assert stale.json()["errors"][0]["code"] == "stale_lifecycle_state"
    assert stale.json()["currentOverview"]["stateToken"] == overview["stateToken"]

    invalid = client.post(
        "/api/semesters/1/schedule-revisions", json={"expectedStateToken": ""}
    )
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["code"] == "validation_error"


def test_runtime_openapi_exposes_exact_lifecycle_paths_and_contract_fields(client_and_db):
    client, _db = client_and_db
    document = client.get("/openapi.json").json()
    expected_paths = {
        "/api/semesters/{semester_id}/schedule-lifecycle",
        "/api/semesters/{semester_id}/schedule-revisions",
        "/api/schedule-revisions/{revision_id}",
        "/api/schedule-revisions/{revision_id}/publication-preparation",
        "/api/schedule-revisions/{revision_id}/transitions",
    }
    assert expected_paths.issubset(document["paths"])
    request_schema = document["components"]["schemas"]["CreateWorkingRevisionRequest"]
    assert request_schema["required"] == ["expectedStateToken"]


def test_lifecycle_api_supports_ready_successor_abandon_restore_and_replacement(client_and_db):
    client, db = client_and_db
    seed_lifecycle_semester(db, with_schedule=True)
    empty = client.get("/api/semesters/1/schedule-lifecycle").json()
    created = client.post("/api/semesters/1/schedule-revisions", json={"expectedStateToken": empty["stateToken"]}).json()
    revision = created["activeWorkingRevision"]
    ready = client.post(f"/api/schedule-revisions/{revision['revisionId']}/transitions", json={"action": "mark_ready", "expectedRevisionVersion": revision["revisionVersion"], "expectedStateToken": created["stateToken"], "confirmed": False}).json()
    assert ready["activeWorkingRevision"]["state"] == "ready_for_review"
    ready_revision = ready["activeWorkingRevision"]
    preparation = client.post(f"/api/schedule-revisions/{revision['revisionId']}/publication-preparation", json={"expectedRevisionVersion": ready_revision["revisionVersion"], "expectedStateToken": ready["stateToken"]}).json()
    published = client.post(f"/api/schedule-revisions/{revision['revisionId']}/transitions", json={"action": "publish", "expectedRevisionVersion": ready_revision["revisionVersion"], "expectedStateToken": ready["stateToken"], "confirmed": True, "publicationToken": preparation["preparationToken"]}).json()
    successor = client.post("/api/semesters/1/schedule-revisions", json={"expectedStateToken": published["stateToken"]}).json()
    working = successor["activeWorkingRevision"]
    assert working["originRevisionId"] == published["currentPublication"]["revisionId"]
    abandoned = client.post(f"/api/schedule-revisions/{working['revisionId']}/transitions", json={"action": "abandon", "expectedRevisionVersion": working["revisionVersion"], "expectedStateToken": successor["stateToken"], "confirmed": True}).json()
    assert abandoned["currentPublication"]["revisionId"] == published["currentPublication"]["revisionId"]
    abandoned_revision = next(item for item in abandoned["revisions"] if item["revisionId"] == working["revisionId"])
    restored = client.post(f"/api/schedule-revisions/{working['revisionId']}/transitions", json={"action": "restore", "expectedRevisionVersion": abandoned_revision["revisionVersion"], "expectedStateToken": abandoned["stateToken"], "confirmed": True}).json()
    assert restored["activeWorkingRevision"]["revisionId"] == working["revisionId"]
    restored_revision = restored["activeWorkingRevision"]
    replacement_preparation = client.post(
        f"/api/schedule-revisions/{working['revisionId']}/publication-preparation",
        json={
            "expectedRevisionVersion": restored_revision["revisionVersion"],
            "expectedStateToken": restored["stateToken"],
        },
    ).json()
    replacement_response = client.post(
        f"/api/schedule-revisions/{working['revisionId']}/transitions",
        json={
            "action": "publish",
            "expectedRevisionVersion": restored_revision["revisionVersion"],
            "expectedStateToken": restored["stateToken"],
            "confirmed": True,
            "publicationToken": replacement_preparation["preparationToken"],
        },
    )
    assert replacement_response.status_code == 200, replacement_response.json()
    replacement = replacement_response.json()
    assert replacement["currentPublication"]["revisionId"] == working["revisionId"]
    assert replacement["activeWorkingRevision"] is None
    assert next(item for item in replacement["revisions"] if item["revisionId"] == revision["revisionId"])["state"] == "superseded"
