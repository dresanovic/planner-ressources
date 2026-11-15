from datetime import date
from copy import deepcopy
import pytest

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
from tests.planner_auth_fixtures import authenticate_test_client


def _client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    db = Session(engine)
    app.dependency_overrides[get_db] = lambda: (yield db)
    client = TestClient(app)
    authenticate_test_client(client, db)
    return client, db


def test_time_grid_additive_contract_on_existing_authenticated_route():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    client, db = _client()
    try:
        seed_time_grid_workspace(db)
        response = client.get('/api/semesters/1/calendar-workspace')
        assert response.status_code == 200
        body = response.json()
        assert body['sectionStatus']['teachingWindows']['availability'] == 'available'
        context = body['teachingWindowContexts'][0]
        assert context['reason'] is None
        assert context['sourceRevision'] is None
        assert context['windows'][0]['kind'] == 'weekly'
        assert context['windows'][0]['date'] is None
        assert body['selectedRevision']['validationBasis'] == 'current'
    finally:
        app.dependency_overrides.clear()
        client.close()
        db.close()


@pytest.mark.parametrize('capture', ['working', 'published', 'legacy', 'legacy_metadata', 'missing_identity', 'mixed'])
def test_time_grid_wire_provenance_nullable_identity_and_read_only_capture(capture):
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    from app.models.planning import CohortCalendarTimeWindow
    from sqlalchemy import select
    client, db = _client()
    try:
        seed_time_grid_workspace(db, capture=capture, second_calendar=capture == 'mixed')
        revision = db.scalar(select(ScheduleRevision))
        snapshot_before = deepcopy(revision.snapshot_document)
        # Authentication deliberately records session activity on authenticated reads.
        # The presentation invariant covers planning records, not auth activity.
        def planning_dump():
            return [line for line in db.connection().connection.iterdump()
                    if not line.startswith('INSERT INTO "planner_sessions"')]
        records_before = planning_dump()
        body = client.get('/api/semesters/1/calendar-workspace').json()
        contexts = body['teachingWindowContexts']
        assert len({c['courseRef'] for c in contexts}) == len(body['courses'])
        context = contexts[0]
        if capture == 'mixed':
            assert body['sectionStatus']['teachingWindows']['availability'] == 'partial'
            assert contexts[1]['availability'] == 'unavailable'
            assert contexts[1]['windows'] == contexts[1]['days'] == []
            assert contexts[1]['calendarRef'] == 'calendar:2'
        assert context['calendarRef'] == (None if capture == 'missing_identity' else 'calendar:1')
        assert body['selectedRevision']['validationBasis'] == 'current'
        assert context['availability'] == ('unavailable' if capture == 'legacy' else 'available')
        assert context['basis'] == ('unavailable' if capture == 'legacy' else 'current_working' if capture == 'working' else 'captured_published')
        if capture == 'legacy':
            assert context['windows'] == context['days'] == []
            assert context['isCustom'] is context['planningStartDate'] is None
        else:
            assert context['windows'][0]['kind'] == 'weekly'
            assert context['windows'][0]['isIntensive'] is False
            assert context['windows'][0]['date'] is None
            assert context['days'][0]['periodStatus'] == 'outside_period'  # saved exam in December
        assert revision.snapshot_document == snapshot_before
        assert records_before == planning_dump()
        if capture == 'working':
            db.delete(db.scalar(select(CohortCalendarTimeWindow)))
            db.commit()
            empty = client.get('/api/semesters/1/calendar-workspace').json()['teachingWindowContexts'][0]
            assert empty['availability'] == 'available'
            assert empty['windows'] == []
    finally:
        app.dependency_overrides.clear()
        client.close()
        db.close()


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
        assert no_revision.json()['teachingWindowContexts'] == []
        assert no_revision.json()['sectionStatus']['teachingWindows']['availability'] == 'not_applicable'

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
