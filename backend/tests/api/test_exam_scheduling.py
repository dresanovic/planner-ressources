from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from tests.exam_fixtures import exam_catalog, teaching_draft


@pytest.fixture()
def client_and_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all(exam_catalog())
    db.add(teaching_draft())
    db.commit()
    app.dependency_overrides[get_db] = lambda: (yield db)
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        db.close()


def _configuration(expected_revision=None):
    return {"semesterId": 1, "enabled": True, "expectedRevision": expected_revision, "configuration": {"identifier": "Final exam", "durationMinutes": 120, "recommendedStartOverride": None, "recommendedEndOverride": None, "requiredCapacity": 40, "examType": "Written", "responsibleLecturerId": 1}}


def test_configuration_overview_manual_update_and_delete_contract(client_and_db):
    client, _db = client_and_db
    created = client.put("/api/courses/1/exam-configuration", json=_configuration())
    assert created.status_code == 201
    state = created.json()
    assert state["configuration"]["recommendedStartDate"] == "2026-10-09"
    overview = client.get("/api/exam-planning?semesterId=1")
    assert overview.status_code == 200
    manual = client.post("/api/courses/1/exam-sessions", json={"semesterId": 1, "date": "2026-10-16", "startTime": "13:00", "lecturerId": 1, "roomId": 1, "expectedConfigurationRevision": 1, "inputSnapshotToken": state["inputSnapshotToken"]})
    assert manual.status_code == 201
    exam = manual.json()["activeExam"]
    updated = client.patch(f"/api/exam-sessions/{exam['id']}", json={"date": "2026-10-17", "startTime": "09:00", "lecturerId": 1, "roomId": 1, "expectedExamRevision": 1, "inputSnapshotToken": exam["inputSnapshotToken"]})
    assert updated.status_code == 200
    changed = updated.json()["activeExam"]
    deleted = client.request("DELETE", f"/api/exam-sessions/{exam['id']}", json={"confirmed": True, "expectedExamRevision": 2, "inputSnapshotToken": changed["inputSnapshotToken"]})
    assert deleted.status_code == 200
    assert deleted.json()["deletedExamId"] == exam["id"]


def test_generation_prepare_and_generate_mixed_contract(client_and_db):
    client, _db = client_and_db
    state = client.put("/api/courses/1/exam-configuration", json=_configuration()).json()
    prepared = client.post("/api/exams/generation/prepare", json={"semesterId": 1, "courseIds": [1]})
    assert prepared.status_code == 200
    payload = prepared.json()
    generated = client.post("/api/exams/generation", json={"semesterId": 1, "institutionToday": payload["institutionToday"], "sharedSnapshotToken": payload["sharedSnapshotToken"], "courses": [{"courseId": 1, "configurationId": 1, "configurationRevision": 1, "inputSnapshotToken": payload["courses"][0]["inputSnapshotToken"]}]})
    assert generated.status_code == 200
    assert generated.json()["summary"]["scheduled"] == 1


def test_structured_validation_stale_and_not_found_errors(client_and_db):
    client, _db = client_and_db
    invalid = client.put("/api/courses/1/exam-configuration", json={**_configuration(), "configuration": {**_configuration()["configuration"], "identifier": " ", "durationMinutes": 0}})
    assert invalid.status_code == 422
    assert len(invalid.json()["errors"]) >= 2
    missing = client.get("/api/exam-planning?semesterId=999")
    assert missing.status_code == 404
    first = client.put("/api/courses/1/exam-configuration", json=_configuration())
    stale = client.put("/api/courses/1/exam-configuration", json=_configuration())
    assert first.status_code == 201
    assert stale.status_code == 409


def test_configuration_validation_reports_every_semantic_field_together(client_and_db):
    client, _db = client_and_db
    payload = _configuration()
    payload["configuration"] = {
        "identifier": " ",
        "durationMinutes": 0,
        "recommendedStartOverride": "2026-10-10",
        "recommendedEndOverride": None,
        "requiredCapacity": 0,
        "examType": " ",
        "responsibleLecturerId": 0,
    }

    response = client.put("/api/courses/1/exam-configuration", json=payload)

    assert response.status_code == 422
    assert {item["field"] for item in response.json()["errors"]} == {
        "identifier", "durationMinutes", "recommendedEndOverride",
        "requiredCapacity", "examType", "responsibleLecturerId",
    }


def test_openapi_exposes_only_the_six_fs012_operations_with_contract_aliases():
    document = app.openapi()
    expected = {
        "/api/exam-planning": {"get"},
        "/api/courses/{course_id}/exam-configuration": {"put"},
        "/api/exams/generation/prepare": {"post"},
        "/api/exams/generation": {"post"},
        "/api/courses/{course_id}/exam-sessions": {"post"},
        "/api/exam-sessions/{exam_id}": {"patch", "delete"},
    }
    for path, methods in expected.items():
        assert methods.issubset(document["paths"][path])
    save_schema = document["components"]["schemas"]["SaveExamConfigurationRequest"]
    assert set(save_schema["required"]) == {"semesterId", "enabled", "expectedRevision", "configuration"}
    assert "recommendedStartDate" in document["components"]["schemas"]["ExamConfiguration"]["properties"]
    assert "lifecycleStatus" in document["components"]["schemas"]["ExamSessionResponse"]["properties"]
