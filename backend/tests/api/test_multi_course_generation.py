import pytest
from datetime import date, time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import CourseEligibleLecturer, CourseEligibleRoom, DraftSchedule, GenerationConstraintSet, GenerationConstraintWindow, InstitutionHoliday
from tests.multi_course_fixtures import seed_multi_course_planner


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


def prepare_payload(course_ids=(1, 2), operation="initial", semester=1):
    return {"semesterId": semester, "operationKind": operation, "courseIds": list(course_ids)}


def execution_payload(prepared, confirmed=False):
    return {
        "semesterId": prepared["semesterId"],
        "operationKind": prepared["operationKind"],
        "replacementConfirmed": confirmed,
        "courses": [
            {
                "courseId": course["courseId"],
                "expectedDraftScheduleId": course["draftScheduleId"],
                "expectedDraftRevision": course["draftRevision"],
            }
            for course in prepared["courses"]
        ],
    }


def test_prepare_preserves_order_and_canonically_marks_unavailable_courses(client, db_session):
    seed_multi_course_planner(db_session)
    response = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload((2, 999, 1)))
    assert response.status_code == 200
    body = response.json()
    assert [item["courseId"] for item in body["courses"]] == [2, 999, 1]
    assert body["courses"][1] == {
        "courseId": 999, "courseName": None, "available": False,
        "draftScheduleId": None, "draftRevision": None, "replacementRequired": False,
    }


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        (prepare_payload((1,)), "INVALID_BATCH_SIZE"),
        (prepare_payload((1, 1)), "DUPLICATE_COURSE_SELECTION"),
    ],
)
def test_prepare_rejects_invalid_initial_selection(client, db_session, payload, code):
    seed_multi_course_planner(db_session)
    response = client.post("/api/draft-schedules/batch/prepare", json=payload)
    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == code


def test_batch_all_success_persists_ordered_schedules_and_active_defaults(client, db_session):
    seed_multi_course_planner(db_session)
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    response = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared))
    assert response.status_code == 200
    result = response.json()
    assert result["summary"] == {"total": 2, "succeeded": 2, "failed": 0}
    assert [item["courseId"] for item in result["outcomes"]] == [1, 2]
    assert all(item["status"] == "succeeded" and item["draftRevision"] == 1 for item in result["outcomes"])
    assert db_session.query(DraftSchedule).count() == 2
    assert db_session.query(GenerationConstraintSet).count() == 2


def test_batch_preparation_marks_course_unavailable_for_wrong_semester(client, db_session):
    seed_multi_course_planner(db_session)
    from app.models.planning import Course
    db_session.get(Course, 1).current_semester_id = 2
    db_session.commit()
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    first = next(item for item in prepared["courses"] if item["courseId"] == 1)
    assert first["available"] is False


def test_partial_success_preserves_failed_course_and_reports_every_reason(client, db_session):
    seed_multi_course_planner(db_session, invalid_course_id=2)
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    result = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared)).json()
    assert result["summary"] == {"total": 2, "succeeded": 1, "failed": 1}
    assert result["outcomes"][1]["errors"][0]["code"] == "INSUFFICIENT_ROOM_CAPACITY"
    assert db_session.query(DraftSchedule).filter_by(course_id=2).one_or_none() is None


def test_batch_api_loads_holidays_server_side_and_returns_per_course_named_evidence(client, db_session):
    seed_multi_course_planner(db_session)
    constraint = GenerationConstraintSet(
        course_id=1,
        semester_id=1,
        planning_start_date=date(2026, 9, 7),
        planning_end_date=date(2026, 9, 7),
        windows=[GenerationConstraintWindow(
            source_time_window_id=1,
            weekday=0,
            start_time=time(8),
            end_time=time(12),
            sort_order=1,
        )],
    )
    db_session.add_all([constraint, InstitutionHoliday(date=date(2026, 9, 7), name="Founders Day")])
    db_session.commit()
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()

    result = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared)).json()

    first = next(item for item in result["outcomes"] if item["courseId"] == 1)
    reason = next(item for item in first["errors"] if item["code"] == "INSTITUTION_HOLIDAY")
    assert reason["holidayDate"] == "2026-09-07"
    assert reason["holidayName"] == "Founders Day"
    assert all("holidayDate" not in item and "holidayName" not in item for item in first["errors"] if item is not reason)
    assert db_session.query(DraftSchedule).filter_by(course_id=1).one_or_none() is None


def test_retry_allows_one_failed_course_without_regenerating_success(client, db_session):
    seed_multi_course_planner(db_session, invalid_course_id=2)
    initial = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    first = client.post("/api/draft-schedules/batch/generate", json=execution_payload(initial)).json()
    first_revision = first["outcomes"][0]["draftRevision"]
    from app.models.planning import Room
    db_session.get(Room, 2).capacity = 40
    db_session.commit()
    retry = client.post(
        "/api/draft-schedules/batch/prepare", json=prepare_payload((2,), "retry")
    ).json()
    result = client.post("/api/draft-schedules/batch/generate", json=execution_payload(retry)).json()
    assert result["summary"] == {"total": 1, "succeeded": 1, "failed": 0}
    assert db_session.query(DraftSchedule).filter_by(course_id=1, semester_id=1).one().revision == first_revision


def test_replacement_requires_confirmation_and_cancel_path_writes_nothing(client, db_session):
    seed_multi_course_planner(db_session)
    first = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    client.post("/api/draft-schedules/batch/generate", json=execution_payload(first))
    before = {(d.course_id, d.id, d.revision) for d in db_session.query(DraftSchedule).all()}
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    assert prepared["replacementCourseIds"] == [1, 2]
    response = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared))
    assert response.status_code == 409
    assert {(d.course_id, d.id, d.revision) for d in db_session.query(DraftSchedule).all()} == before


def test_confirmed_replacement_increments_revision_and_preserves_other_semester(client, db_session):
    seed_multi_course_planner(db_session)
    from app.models.planning import Course
    db_session.get(Course, 1).current_semester_id = 2
    db_session.commit()
    spring = client.post(
        "/api/draft-schedules/batch/prepare", json=prepare_payload((1,), "retry", 2)
    ).json()
    client.post("/api/draft-schedules/batch/generate", json=execution_payload(spring))
    db_session.get(Course, 1).current_semester_id = 1
    db_session.commit()
    fall = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    client.post("/api/draft-schedules/batch/generate", json=execution_payload(fall))
    replacement = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    result = client.post(
        "/api/draft-schedules/batch/generate", json=execution_payload(replacement, True)
    ).json()
    assert all(item["draftRevision"] == 2 for item in result["outcomes"])
    assert db_session.query(DraftSchedule).filter_by(course_id=1, semester_id=2).one().revision == 1


def test_stale_prepared_draft_is_course_local_failure(client, db_session):
    seed_multi_course_planner(db_session)
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    other = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    client.post("/api/draft-schedules/batch/generate", json=execution_payload(other))
    result = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared)).json()
    assert result["summary"] == {"total": 2, "succeeded": 0, "failed": 2}
    assert {item["errors"][0]["code"] for item in result["outcomes"]} == {"STALE_DRAFT_SCHEDULE"}


def test_unexpected_batch_failure_rolls_back_all_courses_and_returns_no_false_outcomes(
    client, db_session, monkeypatch
):
    seed_multi_course_planner(db_session)
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    import app.services.multi_course_generation as service
    original = service.replace_draft_schedule
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected")
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_second)
    response = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared))
    assert response.status_code == 500
    assert response.json()["code"] == "BATCH_OPERATION_FAILED"
    assert "outcomes" not in response.json()
    assert db_session.query(DraftSchedule).count() == 0


def test_post_batch_overview_keeps_overlaps_non_blocking_and_visible(client, db_session):
    seed_multi_course_planner(db_session)
    from app.models.planning import Course
    second = db_session.get(Course, 2)
    second.eligible_lecturers = [CourseEligibleLecturer(lecturer_id=1)]
    second.cohort_id = 1
    second.eligible_rooms = [CourseEligibleRoom(room_id=1)]
    db_session.commit()
    prepared = client.post("/api/draft-schedules/batch/prepare", json=prepare_payload()).json()
    result = client.post("/api/draft-schedules/batch/generate", json=execution_payload(prepared)).json()
    assert result["summary"]["succeeded"] == 2
    overview = client.get("/api/draft-schedules?semesterId=1").json()
    codes = {alert["code"] for schedule in overview for session in schedule["sessions"] for alert in session["validationAlerts"]}
    assert {"LECTURER_OVERLAP", "ROOM_OVERLAP", "COHORT_OVERLAP"}.issubset(codes)
