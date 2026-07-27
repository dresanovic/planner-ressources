from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.db.session import get_db
from app.main import app
from app.models.planning import ScheduleRevision, Semester
from app.services.schedule_lifecycle import create_working_revision, get_lifecycle_overview
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester


def _client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    db = Session(engine)
    app.dependency_overrides[get_db] = lambda: (yield db)
    return TestClient(app), db


def test_endpoint_returns_distinct_no_revision_and_loaded_variants():
    client, db = _client()
    try:
        seed_lifecycle_semester(db, with_schedule=True)
        empty = Semester(
            id=2,
            name="Empty",
            start_date=date(2027, 2, 1),
            end_date=date(2027, 6, 20),
        )
        db.add(empty)
        db.commit()

        no_revision = client.get("/api/semesters/2/calendar-workspace")
        assert no_revision.status_code == 200
        assert no_revision.json()["workspaceState"] == "no_revision"
        assert no_revision.json()["courses"] == []

        initial = get_lifecycle_overview(db, 1)
        create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        loaded = client.get("/api/semesters/1/calendar-workspace")
        assert loaded.status_code == 200
        body = loaded.json()
        assert body["workspaceState"] == "loaded"
        assert body["selectedRevision"]["designation"] == "active_working"
        assert body["workspaceToken"]
        exam = next(
            occurrence
            for occurrence in body["occurrences"]
            if occurrence["kind"] == "exam"
        )
        assert exam["requiredCapacity"] == 30
        assert exam["assignedRoomName"] == "Room 1"
        assert exam["currentRoomCapacity"] == 40
        assert body["summary"]["planningFailures"]["availability"] == "unavailable"
        assert body["summary"]["planningFailures"]["coverage"] == {
            "eligibleCourseCount": 1,
            "coveredCourseCount": 0,
            "coverageComplete": False,
        }
        assert set(body["summary"]) == {
            "unscheduledWork",
            "conflicts",
            "capacityIssues",
            "planningFailures",
            "needsReview",
        }
    finally:
        app.dependency_overrides.clear()
        client.close()
        db.close()


def test_endpoint_rejects_historical_revision_and_reports_missing_context():
    client, db = _client()
    try:
        seed_lifecycle_semester(db, with_schedule=False)
        db.add(
            ScheduleRevision(
                id=9,
                semester_id=1,
                revision_number=1,
                state="abandoned",
                row_version=1,
                snapshot_schema_version=1,
                snapshot_document={
                    "schemaVersion": 1,
                    "capturedAt": "2026-07-23T10:00:00Z",
                    "semester": {
                        "sourceId": 1,
                        "name": "Semester 1",
                        "startDate": "2026-09-01",
                        "endDate": "2026-12-20",
                    },
                    "courses": [],
                    "examSessions": [],
                    "capturedConditions": [],
                },
            )
        )
        db.commit()

        historical = client.get(
            "/api/semesters/1/calendar-workspace?revisionId=9"
        )
        missing = client.get("/api/semesters/999/calendar-workspace")

        assert historical.status_code == 422
        assert "active Working or Current Published" in historical.json()["detail"]
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()
        client.close()
        db.close()
