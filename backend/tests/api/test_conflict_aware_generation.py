import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import Cohort, Course, DraftSchedule, Room
from tests.optimization_fixtures import seed_optimization_planner
from app.services.draft_schedule_repository import get_draft_schedule, load_course_plan, replace_draft_schedule
from app.services.schedule_generation import GeneratedSession
from datetime import date, time


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


def generation_payload(prepared, confirmed=False):
    return {
        "semesterId": prepared["semesterId"],
        "unavailableDates": prepared["unavailableDates"],
        "sharedSnapshotToken": prepared["sharedSnapshotToken"],
        "replacementConfirmed": confirmed,
        "courses": [{
            "courseId": item["courseId"],
            "expectedDraftScheduleId": item["draftScheduleId"],
            "expectedDraftRevision": item["draftRevision"],
            "inputSnapshotToken": item["inputSnapshotToken"],
        } for item in prepared["courses"]],
    }


def test_prepare_deduplicates_dates_and_generate_returns_proven_complete_saved_result(client, db_session):
    seed_optimization_planner(db_session, course_count=2)
    response = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "courseIds": [2, 1], "unavailableDates": ["2026-10-26", "2026-10-26"]})
    assert response.status_code == 200
    prepared = response.json()
    assert prepared["unavailableDates"] == ["2026-10-26"]
    assert [item["courseId"] for item in prepared["courses"]] == [1, 2]

    generated = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))
    assert generated.status_code == 200
    assert generated.json()["summary"]["complete"] == 2
    assert generated.json()["summary"]["optimalForPreparedSnapshot"] is True


@pytest.mark.parametrize("course_ids", [[], list(range(1, 22)), [1, 1]])
def test_prepare_rejects_invalid_selection(client, db_session, course_ids):
    seed_optimization_planner(db_session, course_count=1)
    response = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "courseIds": course_ids, "unavailableDates": []})
    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] in {"INVALID_OPTIMIZATION_SIZE", "DUPLICATE_COURSE_SELECTION"}


def test_prepare_rejects_complete_selection_when_one_course_belongs_to_another_semester(client, db_session):
    seed_optimization_planner(db_session, course_count=2)
    db_session.get(Course, 2).current_semester_id = 2
    db_session.commit()

    response = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "courseIds": [1, 2], "unavailableDates": []},
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "COURSE_SEMESTER_MISMATCH"
    assert db_session.query(DraftSchedule).count() == 0


def test_existing_draft_requires_explicit_replacement_confirmation(client, db_session):
    seed_optimization_planner(db_session, course_count=1)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1)])
    db_session.commit()
    prepared = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "courseIds": [1], "unavailableDates": []}).json()
    response = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))
    assert response.status_code == 409
    assert response.json()["code"] == "REPLACEMENT_CONFIRMATION_REQUIRED"


def test_unproven_solver_result_returns_503_and_saves_nothing(client, db_session, monkeypatch):
    seed_optimization_planner(db_session, course_count=1)
    prepared = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "courseIds": [1], "unavailableDates": []}).json()
    from app.services.semester_optimization import OptimalResultNotProven
    import app.services.conflict_aware_generation as service
    monkeypatch.setattr(service, "optimize_semester", lambda *args, **kwargs: (_ for _ in ()).throw(OptimalResultNotProven("not proven")))
    response = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))
    assert response.status_code == 503
    assert response.json() == {"code": "OPTIMAL_RESULT_NOT_PROVEN", "message": "not proven", "saved": False}


def test_material_change_after_preparation_returns_saved_state_stale_outcome(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    room = db_session.get(Room, 1)
    room.capacity = 20
    room.revision += 1
    db_session.commit()

    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )

    assert response.status_code == 200
    assert response.json()["summary"]["stale"] == 1
    assert response.json()["summary"]["optimalForPreparedSnapshot"] is False
    assert response.json()["outcomes"][0]["status"] == "stale"
    assert db_session.query(DraftSchedule).count() == 0


def test_confirmed_equal_non_improvement_preserves_current_draft(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()

    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared, confirmed=True),
    )

    assert response.status_code == 200
    assert response.json()["outcomes"][0]["status"] == "unchanged"
    assert response.json()["outcomes"][0]["saved"] is False
    assert get_draft_schedule(db_session, 1, 1).revision == 1


def test_confirmed_equal_unit_conflict_reduction_replaces_current_draft(client, db_session):
    seed_optimization_planner(db_session, course_count=2, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    replace_draft_schedule(db_session, load_course_plan(db_session, 2), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()

    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared, confirmed=True),
    )
    outcome = response.json()["outcomes"][0]
    current = get_draft_schedule(db_session, 1, 1)

    assert response.status_code == 200
    assert outcome["status"] == "complete" and outcome["saved"] is True
    assert outcome["improvement"]["reducedConflicts"] == 2
    assert current.revision == 2
    assert current.sessions[0].date != date(2026, 9, 7)


def test_mixed_saved_failed_and_post_solve_stale_outcomes_share_one_response(client, db_session, monkeypatch):
    seed_optimization_planner(db_session, course_count=3, total_units=4)
    db_session.get(Cohort, 2).is_active = False
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "courseIds": [1, 2, 3], "unavailableDates": []},
    ).json()
    import app.services.conflict_aware_generation as service
    original = service.optimize_semester

    def solve_then_change_third_course(*args, **kwargs):
        result = original(*args, **kwargs)
        course = db_session.get(Course, 3)
        course.total_units = 6
        course.revision += 1
        db_session.flush()
        return result

    monkeypatch.setattr(service, "optimize_semester", solve_then_change_third_course)
    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )
    body = response.json()

    assert response.status_code == 200
    assert body["summary"] | {"elapsedMilliseconds": 0} == {
        "total": 3,
        "complete": 1,
        "improvedPartial": 0,
        "unchanged": 0,
        "failed": 1,
        "stale": 1,
        "scheduledUnits": 4,
        "remainingUnits": 10,
        "elapsedMilliseconds": 0,
        "optimalForPreparedSnapshot": True,
    }
    assert [item["status"] for item in body["outcomes"]] == ["complete", "failed", "stale"]
    assert db_session.query(DraftSchedule).filter_by(course_id=1, semester_id=1).count() == 1
    assert db_session.query(DraftSchedule).filter_by(course_id=2, semester_id=1).count() == 0
    assert db_session.query(DraftSchedule).filter_by(course_id=3, semester_id=1).count() == 0
