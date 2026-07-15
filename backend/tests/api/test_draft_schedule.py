from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    Lecturer,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
    Room,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)


def generation_payload(
    *,
    start="2026-09-07",
    end="2026-12-20",
    windows=None,
):
    return {
        "semesterId": 1,
        "planningPeriod": {"startDate": start, "endDate": end},
        "allowedTeachingWindows": windows
        if windows is not None
        else [
            {
                "weekday": 0,
                "startTime": "08:00",
                "endTime": "12:00",
                "sourceTimeWindowId": 1,
            },
            {
                "weekday": 2,
                "startTime": "08:00",
                "endTime": "12:00",
                "sourceTimeWindowId": 2,
            },
        ],
    }


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_valid_course(db, *, total_units=20, room_capacity=40, cohort_size=30, min_units=2, max_units=4):
    db.add_all(
        [
            Lecturer(id=1, name="Ada Lovelace", reference_code="LEC-001", normalized_reference_code="lec-001"),
            Cohort(id=1, name="AI 1", student_count=cohort_size),
            Room(id=1, name="R1", reference_code="ROOM-001", normalized_reference_code="room-001", capacity=room_capacity),
            Room(id=3, name="R3", reference_code="ROOM-003", normalized_reference_code="room-003", capacity=60),
            Room(id=4, name="Tiny", reference_code="ROOM-004", normalized_reference_code="room-004", capacity=20),
            StudyType(id=1, name="Full-time"),
            Semester(id=1, name="Fall", start_date=date(2026, 9, 7), end_date=date(2026, 12, 20)),
            StudyTypeTimeWindow(
                id=1,
                study_type_id=1,
                weekday=0,
                start_time=time(8, 0),
                end_time=time(12, 0),
                sort_order=1,
            ),
            StudyTypeTimeWindow(
                id=2,
                study_type_id=1,
                weekday=2,
                start_time=time(8, 0),
                end_time=time(12, 0),
                sort_order=2,
            ),
            Course(
                id=1,
                name="Planning 101",
                total_units=total_units,
                min_session_units=min_units,
                max_session_units=max_units,
                cohort_id=1,
                study_type_id=1,
                current_semester_id=1,
                eligible_lecturers=[CourseEligibleLecturer(lecturer_id=1)],
                eligible_rooms=[CourseEligibleRoom(room_id=1)],
            ),
        ]
    )
    db.commit()


def seed_second_course(db):
    db.add_all(
        [
            Lecturer(id=2, name="Grace Hopper"),
            Cohort(id=2, name="AI 2", student_count=24),
            Room(id=2, name="R2", capacity=30),
            Course(
                id=2,
                name="Scheduling 201",
                total_units=16,
                min_session_units=2,
                max_session_units=4,
                cohort_id=2,
                study_type_id=1,
                current_semester_id=1,
                eligible_lecturers=[CourseEligibleLecturer(lecturer_id=2)],
                eligible_rooms=[CourseEligibleRoom(room_id=2)],
            ),
        ]
    )
    db.commit()


def test_read_planning_options_returns_database_courses_and_windows(client, db_session):
    seed_valid_course(db_session)
    seed_second_course(db_session)

    response = client.get("/api/planning-options")

    assert response.status_code == 200
    payload = response.json()
    assert [course["name"] for course in payload["courses"]] == ["Planning 101", "Scheduling 201"]
    assert payload["courses"][0]["cohort"] == {"id": 1, "name": "AI 1"}
    assert payload["courses"][1]["lecturer"] == {"id": 2, "name": "Grace Hopper"}
    assert payload["courses"][1]["room"] == {"id": 2, "name": "R2"}
    assert [(room["id"], room["name"], room["capacity"]) for room in payload["rooms"]] == [
        (1, "R1", 40), (2, "R2", 30), (3, "R3", 60), (4, "Tiny", 20),
    ]
    assert all(room["referenceCode"] for room in payload["rooms"])
    assert payload["semesters"] == [
        {
            "id": 1,
            "name": "Fall",
            "startDate": "2026-09-07",
            "endDate": "2026-12-20",
        }
    ]
    assert [
        {
            "id": window["id"],
            "studyTypeId": window["studyTypeId"],
            "weekday": window["weekday"],
            "startTime": window["startTime"],
            "endTime": window["endTime"],
        }
        for window in payload["timeWindows"]
    ] == [
        {"id": 1, "studyTypeId": 1, "weekday": 0, "startTime": "08:00", "endTime": "12:00"},
        {"id": 2, "studyTypeId": 1, "weekday": 2, "startTime": "08:00", "endTime": "12:00"},
    ]


def test_generate_and_read_current_draft_schedule(client, db_session):
    seed_valid_course(db_session)

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["courseId"] == 1
    assert payload["context"] == {
        "course": {"id": 1, "name": "Planning 101"},
        "cohort": {"id": 1, "name": "AI 1"},
        "cohortSize": 30,
        "lecturer": {"id": 1, "name": "Ada Lovelace"},
        "room": {"id": 1, "name": "R1"},
        "studyType": {"id": 1, "name": "Full-time"},
    }
    assert [session["units"] for session in payload["sessions"]] == [4, 4, 4, 4, 4]
    assert payload["sessions"][0]["startTime"] == "08:00"
    assert payload["sessions"][0]["endTime"] == "11:30"
    assert {key: payload["sessions"][0][key] for key in (
        "id", "date", "startTime", "endTime", "units", "courseId", "lecturerId",
        "cohortId", "roomId", "studyTypeId", "timeWindowId", "constraintWindowIndex", "validationAlerts",
    )} == {
        "id": payload["sessions"][0]["id"],
        "date": "2026-09-07",
        "startTime": "08:00",
        "endTime": "11:30",
        "units": 4,
        "courseId": 1,
        "lecturerId": 1,
        "cohortId": 1,
        "roomId": 1,
        "studyTypeId": 1,
        "timeWindowId": 1,
        "constraintWindowIndex": 0,
        "validationAlerts": [],
    }
    assert payload["sessions"][0]["lecturer"]["referenceCode"] == "LEC-001"
    assert payload["sessions"][0]["room"]["referenceCode"] == "ROOM-001"

    read_response = client.get("/api/courses/1/draft-schedule?semesterId=1")
    assert read_response.status_code == 200
    assert read_response.json()["sessions"] == payload["sessions"]


def test_read_draft_schedules_lists_generated_plans_for_selected_semester(client, db_session):
    seed_valid_course(db_session)
    seed_second_course(db_session)

    first = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())
    second = client.post("/api/courses/2/draft-schedule/generate", json=generation_payload())

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get("/api/draft-schedules?semesterId=1")

    assert response.status_code == 200
    payload = response.json()
    assert [schedule["context"]["course"]["name"] for schedule in payload] == [
        "Planning 101",
        "Scheduling 201",
    ]
    assert all(schedule["semesterId"] == 1 for schedule in payload)
    assert all(schedule["sessions"] for schedule in payload)


def test_read_draft_schedules_returns_overlap_validation_alerts(client, db_session):
    seed_valid_course(db_session)
    seed_second_course(db_session)
    second_course = db_session.get(Course, 2)
    second_course.eligible_lecturers = [CourseEligibleLecturer(lecturer_id=1)]
    second_course.eligible_rooms = [CourseEligibleRoom(room_id=1)]
    second_course.cohort_id = 1
    db_session.commit()

    assert client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).status_code == 201
    assert client.post("/api/courses/2/draft-schedule/generate", json=generation_payload()).status_code == 201

    response = client.get("/api/draft-schedules?semesterId=1")

    assert response.status_code == 200
    first_session = response.json()[0]["sessions"][0]
    codes = {alert["code"] for alert in first_session["validationAlerts"]}
    assert {"LECTURER_OVERLAP", "ROOM_OVERLAP", "COHORT_OVERLAP"}.issubset(codes)
    lecturer_alert = next(alert for alert in first_session["validationAlerts"] if alert["code"] == "LECTURER_OVERLAP")
    assert lecturer_alert["relatedSessions"][0]["courseName"] == "Scheduling 201"


def test_read_single_draft_schedule_returns_validation_alerts(client, db_session):
    seed_valid_course(db_session)
    seed_second_course(db_session)
    second_course = db_session.get(Course, 2)
    second_course.eligible_lecturers = [CourseEligibleLecturer(lecturer_id=1)]
    db_session.commit()
    client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())
    client.post("/api/courses/2/draft-schedule/generate", json=generation_payload())

    response = client.get("/api/courses/1/draft-schedule?semesterId=1")

    assert response.status_code == 200
    alerts = response.json()["sessions"][0]["validationAlerts"]
    assert any(alert["code"] == "LECTURER_OVERLAP" for alert in alerts)


def test_validation_alerts_include_capacity_window_and_missing_data_codes(client, db_session):
    seed_valid_course(db_session)
    db_session.add(CourseEligibleRoom(course_id=1, room_id=3))
    db_session.commit()
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]
    db_session.get(Room, 1).capacity = 20
    db_session.commit()

    capacity_payload = client.get("/api/courses/1/draft-schedule?semesterId=1").json()
    capacity_session = next(session for session in capacity_payload["sessions"] if session["id"] == session_id)
    assert any(alert["code"] == "ROOM_CAPACITY" for alert in capacity_session["validationAlerts"])
    db_session.get(Room, 1).capacity = 40
    db_session.commit()

    edit_response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-09-08", "startTime": "13:00", "endTime": "15:00", "roomId": 3},
    )

    assert edit_response.status_code == 200
    edited = next(session for session in edit_response.json()["sessions"] if session["id"] == session_id)
    codes = {alert["code"] for alert in edited["validationAlerts"]}
    assert "GENERATION_CONSTRAINT_VIOLATION" in codes
    assert "STUDY_TYPE_WINDOW_VIOLATION" not in codes


def test_default_study_type_window_violation_is_reported_without_custom_constraints(client, db_session):
    seed_valid_course(db_session)
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]
    client.delete("/api/courses/1/generation-constraints?semesterId=1")

    edit_response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-09-08", "startTime": "13:00", "endTime": "15:00", "roomId": 1},
    )

    assert edit_response.status_code == 200
    edited = next(session for session in edit_response.json()["sessions"] if session["id"] == session_id)
    codes = {alert["code"] for alert in edited["validationAlerts"]}
    assert "STUDY_TYPE_WINDOW_VIOLATION" in codes


def test_custom_friday_evening_constraint_does_not_return_study_type_window_alert(client, db_session):
    seed_valid_course(db_session)

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(
            windows=[
                {
                    "weekday": 4,
                    "startTime": "18:00",
                    "endTime": "22:00",
                    "sourceTimeWindowId": None,
                }
            ]
        ),
    )

    assert response.status_code == 201
    overview = client.get("/api/draft-schedules?semesterId=1").json()
    assert overview[0]["sessions"][0]["date"] == "2026-09-11"
    assert overview[0]["sessions"][0]["startTime"] == "18:00"
    assert overview[0]["sessions"][0]["endTime"] == "21:30"
    assert all(
        alert["code"] != "STUDY_TYPE_WINDOW_VIOLATION"
        for session in overview[0]["sessions"]
        for alert in session["validationAlerts"]
    )


def test_custom_constraint_violation_does_not_duplicate_study_type_window_alert(client, db_session):
    seed_valid_course(db_session)
    generated = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(
            windows=[
                {
                    "weekday": 4,
                    "startTime": "18:00",
                    "endTime": "22:00",
                    "sourceTimeWindowId": None,
                }
            ]
        ),
    ).json()
    session_id = generated["sessions"][0]["id"]

    edit_response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-09-11", "startTime": "17:01", "endTime": "21:30", "roomId": 1},
    )

    assert edit_response.status_code == 200
    edited = next(session for session in edit_response.json()["sessions"] if session["id"] == session_id)
    codes = {alert["code"] for alert in edited["validationAlerts"]}
    assert "GENERATION_CONSTRAINT_VIOLATION" in codes
    assert "STUDY_TYPE_WINDOW_VIOLATION" not in codes


def test_second_generation_replaces_previous_draft(client, db_session):
    seed_valid_course(db_session)

    client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(),
    )
    second = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(
            windows=[
                {
                    "weekday": 2,
                    "startTime": "08:00",
                    "endTime": "12:00",
                    "sourceTimeWindowId": 2,
                }
            ]
        ),
    )

    assert second.status_code == 201
    read_payload = client.get("/api/courses/1/draft-schedule?semesterId=1").json()
    assert len(read_payload["sessions"]) == 5
    assert read_payload["sessions"][0]["date"] == "2026-09-09"


def test_generation_returns_non_blocking_validation_alerts(client, db_session):
    seed_valid_course(db_session)
    seed_second_course(db_session)
    second_course = db_session.get(Course, 2)
    second_course.eligible_lecturers = [CourseEligibleLecturer(lecturer_id=1)]
    db_session.commit()
    client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())

    response = client.post("/api/courses/2/draft-schedule/generate", json=generation_payload())

    assert response.status_code == 201
    assert any(
        alert["code"] == "LECTURER_OVERLAP"
        for session in response.json()["sessions"]
        for alert in session["validationAlerts"]
    )


def test_generated_sessions_never_exceed_allowed_windows(client, db_session):
    seed_valid_course(db_session)

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(),
    )

    assert response.status_code == 201
    for session in response.json()["sessions"]:
        assert session["startTime"] >= "08:00"
        assert session["endTime"] <= "12:00"


def test_generation_returns_multiple_failure_reasons_without_partial_draft(client, db_session):
    seed_valid_course(db_session, room_capacity=40, cohort_size=45, min_units=5, max_units=4)

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(),
    )

    assert response.status_code == 422
    codes = {error["code"] for error in response.json()["errors"]}
    assert codes == {"INSUFFICIENT_ROOM_CAPACITY", "INVALID_SESSION_PREFERENCE"}
    assert client.get("/api/courses/1/draft-schedule?semesterId=1").status_code == 404


def test_generation_blocks_wrong_current_semester_and_missing_active_window(client, db_session):
    seed_valid_course(db_session)
    db_session.add(Semester(id=2, name="Spring", start_date=date(2027, 2, 1), end_date=date(2027, 6, 20)))
    db_session.commit()
    mismatch = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload() | {"semesterId": 2, "planningPeriod": {"startDate": "2027-02-01", "endDate": "2027-06-20"}})
    assert mismatch.status_code == 422
    assert any(error["code"] == "COURSE_SEMESTER_MISMATCH" for error in mismatch.json()["errors"])

    for window in db_session.query(StudyTypeTimeWindow).all():
        window.is_active = False
    db_session.commit()
    missing = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())
    assert missing.status_code == 422
    assert any(error["code"] == "MISSING_ACTIVE_TIME_WINDOW" for error in missing.json()["errors"])


def test_generation_constraints_default_load_save_reload_and_clear(client, db_session):
    seed_valid_course(db_session)

    default_response = client.get("/api/courses/1/generation-constraints?semesterId=1")

    assert default_response.status_code == 200
    defaults = default_response.json()
    assert defaults["isCustom"] is False
    assert defaults["planningPeriod"] == {"startDate": "2026-09-07", "endDate": "2026-12-20"}
    assert defaults["allowedTeachingWindows"] == [
        {"weekday": 0, "startTime": "08:00", "endTime": "12:00", "sourceTimeWindowId": 1},
        {"weekday": 2, "startTime": "08:00", "endTime": "12:00", "sourceTimeWindowId": 2},
    ]

    custom_payload = generation_payload(
        start="2026-09-14",
        end="2026-10-21",
        windows=[{"weekday": 2, "startTime": "09:00", "endTime": "13:00"}],
    )
    generate_response = client.post("/api/courses/1/draft-schedule/generate", json=custom_payload)
    assert generate_response.status_code == 201

    saved_response = client.get("/api/courses/1/generation-constraints?semesterId=1")
    saved = saved_response.json()
    assert saved["isCustom"] is True
    assert saved["planningPeriod"] == {"startDate": "2026-09-14", "endDate": "2026-10-21"}
    assert saved["allowedTeachingWindows"] == [
        {"weekday": 2, "startTime": "09:00", "endTime": "13:00", "sourceTimeWindowId": None}
    ]

    clear_response = client.delete("/api/courses/1/generation-constraints?semesterId=1")
    assert clear_response.status_code == 204
    cleared = client.get("/api/courses/1/generation-constraints?semesterId=1").json()
    assert cleared["isCustom"] is False
    assert cleared["planningPeriod"] == {"startDate": "2026-09-07", "endDate": "2026-12-20"}


def test_invalid_generation_constraints_do_not_replace_saved_constraints_or_draft(client, db_session):
    seed_valid_course(db_session)

    successful = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())
    assert successful.status_code == 201
    existing_sessions = client.get("/api/courses/1/draft-schedule?semesterId=1").json()["sessions"]

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(start="2026-09-01", end="2026-09-07"),
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "INVALID_PLANNING_PERIOD"
    assert client.get("/api/courses/1/draft-schedule?semesterId=1").json()["sessions"] == existing_sessions


def test_empty_or_invalid_teaching_windows_return_constraint_failures(client, db_session):
    seed_valid_course(db_session)

    missing = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(windows=[]),
    )
    invalid = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(
            windows=[{"weekday": 7, "startTime": "12:00", "endTime": "08:00"}]
        ),
    )

    assert missing.status_code == 422
    assert missing.json()["errors"][0]["code"] == "MISSING_TEACHING_WINDOW"
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["code"] == "INVALID_TEACHING_WINDOW"


def test_update_draft_session_edits_time_and_rejects_invalid_values(client, db_session):
    seed_valid_course(db_session)
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]

    response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "roomId": 1},
    )

    assert response.status_code == 200
    edited = response.json()["sessions"][-1]
    assert edited["id"] == session_id
    assert edited["date"] == "2026-12-14"
    assert edited["startTime"] == "09:00"
    assert edited["endTime"] == "10:30"

    invalid = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-09-01", "startTime": "09:00", "endTime": "10:30", "roomId": 1},
    )
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["code"] == "INVALID_SESSION_DATE"

    duplicate = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-09-14", "startTime": "09:00", "endTime": "10:30", "roomId": 1},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["errors"][0]["code"] == "DUPLICATE_SESSION_DATE"

    invalid_date = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "not-a-date", "startTime": "09:00", "endTime": "10:30", "roomId": 1},
    )
    assert invalid_date.status_code == 422
    assert invalid_date.json()["errors"][0]["code"] == "INVALID_SESSION_DATE"

    invalid_time = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "", "endTime": "10:30", "roomId": 1},
    )
    assert invalid_time.status_code == 422
    assert invalid_time.json()["errors"][0]["code"] == "INVALID_SESSION_TIME_RANGE"


def test_update_draft_session_room_capacity_and_missing_room(client, db_session):
    seed_valid_course(db_session)
    db_session.add_all([
        CourseEligibleRoom(course_id=1, room_id=3),
        CourseEligibleRoom(course_id=1, room_id=4),
    ])
    db_session.commit()
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]

    room_response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "roomId": 3},
    )
    assert room_response.status_code == 200
    assert room_response.json()["sessions"][-1]["roomId"] == 3

    capacity_response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "roomId": 4},
    )
    assert capacity_response.status_code == 422
    assert capacity_response.json()["errors"][0]["code"] == "INSUFFICIENT_ROOM_CAPACITY"

    missing_response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "roomId": 999},
    )
    assert missing_response.status_code == 404


def test_update_draft_session_changes_lecturer_and_room_only_to_current_valid_eligible_choices(client, db_session):
    seed_valid_course(db_session)
    db_session.add(Lecturer(id=2, name="Grace Hopper", reference_code="LEC-002", normalized_reference_code="lec-002"))
    db_session.add_all([
        CourseEligibleLecturer(course_id=1, lecturer_id=2),
        CourseEligibleRoom(course_id=1, room_id=3),
    ])
    db_session.commit()
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]

    changed = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "lecturerId": 2, "roomId": 3},
    )
    assert changed.status_code == 200
    edited = next(item for item in changed.json()["sessions"] if item["id"] == session_id)
    assert (edited["lecturerId"], edited["roomId"]) == (2, 3)
    assert edited["lecturer"]["referenceCode"] == "LEC-002"

    invalid = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "lecturerId": 999, "roomId": 3},
    )
    assert invalid.status_code == 422
    assert invalid.json()["errors"][0]["code"] == "LECTURER_INELIGIBLE"


def test_update_draft_session_preserves_an_unchanged_legacy_invalid_assignment(client, db_session):
    seed_valid_course(db_session)
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]
    db_session.query(CourseEligibleRoom).filter_by(course_id=1, room_id=1).delete()
    db_session.commit()

    response = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "lecturerId": 1, "roomId": 1},
    )

    assert response.status_code == 200
    edited = next(item for item in response.json()["sessions"] if item["id"] == session_id)
    assert edited["roomId"] == 1
    assert "ROOM_INELIGIBLE" in {alert["code"] for alert in edited["validationAlerts"]}


def test_draft_api_serializes_combined_resource_alerts_without_mutating_assignments(client, db_session):
    seed_valid_course(db_session)
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    before = [
        (item["id"], item["lecturerId"], item["roomId"], item["date"], item["startTime"], item["endTime"])
        for item in generated["sessions"]
    ]
    lecturer_period = ResourceUnavailabilityPeriod(
        lecturer_id=1, kind="recurring", start_time=time(8), end_time=time(12)
    )
    lecturer_period.weekdays = [ResourceUnavailabilityWeekday(weekday=0)]
    room_period = ResourceUnavailabilityPeriod(
        room_id=1,
        kind="dated",
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 7),
        start_time=time(8),
        end_time=time(12),
    )
    db_session.add_all([lecturer_period, room_period])
    db_session.query(CourseEligibleLecturer).filter_by(course_id=1, lecturer_id=1).delete()
    db_session.query(CourseEligibleRoom).filter_by(course_id=1, room_id=1).delete()
    db_session.get(Room, 1).capacity = 20
    db_session.commit()

    payload = client.get("/api/courses/1/draft-schedule?semesterId=1").json()
    first = payload["sessions"][0]
    codes = {alert["code"] for alert in first["validationAlerts"]}
    assert {
        "LECTURER_INELIGIBLE", "ROOM_INELIGIBLE", "LECTURER_UNAVAILABLE",
        "ROOM_UNAVAILABLE", "ROOM_CAPACITY",
    }.issubset(codes)
    assert first["lecturer"]["referenceCode"] == "LEC-001"
    assert first["room"]["referenceCode"] == "ROOM-001"
    after = [
        (item["id"], item["lecturerId"], item["roomId"], item["date"], item["startTime"], item["endTime"])
        for item in payload["sessions"]
    ]
    assert after == before


def test_cohort_growth_validates_saved_sessions_against_current_cohort_size(client, db_session):
    seed_valid_course(
        db_session,
        total_units=4,
        room_capacity=30,
        cohort_size=20,
        min_units=2,
        max_units=2,
    )
    generated = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(),
    )
    assert generated.status_code == 201

    grown = client.patch(
        "/api/academic/cohorts/1",
        json={"name": "AI 1", "studentCount": 35, "expectedRevision": 1},
    )
    assert grown.status_code == 200

    reread = client.get("/api/courses/1/draft-schedule?semesterId=1")
    assert reread.status_code == 200
    for session in reread.json()["sessions"]:
        codes = {alert["code"] for alert in session["validationAlerts"]}
        assert {"ROOM_INELIGIBLE", "ROOM_CAPACITY"}.issubset(codes)


def test_read_draft_schedules_returns_saved_manual_edit_values_and_regeneration_replaces_them(client, db_session):
    seed_valid_course(db_session)
    db_session.add(CourseEligibleRoom(course_id=1, room_id=3))
    db_session.commit()
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    session_id = generated["sessions"][0]["id"]

    client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "roomId": 3},
    )

    schedules = client.get("/api/draft-schedules?semesterId=1").json()
    edited = schedules[0]["sessions"][-1]
    assert edited["id"] == session_id
    assert edited["date"] == "2026-12-14"
    assert edited["roomId"] == 3

    regenerated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())
    assert regenerated.status_code == 201
    regenerated_sessions = client.get("/api/draft-schedules?semesterId=1").json()[0]["sessions"]
    assert all(session["date"] != "2026-12-14" for session in regenerated_sessions)
    assert all(session["roomId"] == 1 for session in regenerated_sessions)


def test_single_course_read_requires_semester_and_manual_edit_increments_revision(client, db_session):
    seed_valid_course(db_session)
    generated = client.post("/api/courses/1/draft-schedule/generate", json=generation_payload()).json()
    assert generated["revision"] == 1
    assert client.get("/api/courses/1/draft-schedule").status_code == 422

    session_id = generated["sessions"][0]["id"]
    edited = client.patch(
        f"/api/draft-sessions/{session_id}",
        json={"date": "2026-12-14", "startTime": "09:00", "endTime": "10:30", "roomId": 1},
    ).json()
    assert edited["revision"] == 2


def test_single_course_generation_rolls_back_schedule_when_constraint_persistence_crashes(
    client, db_session, monkeypatch
):
    seed_valid_course(db_session)
    import app.api.draft_schedule as draft_api

    def crash(*args, **kwargs):
        raise RuntimeError("injected persistence error")

    monkeypatch.setattr(draft_api, "save_generation_constraints", crash)
    with pytest.raises(RuntimeError, match="injected persistence error"):
        client.post("/api/courses/1/draft-schedule/generate", json=generation_payload())
    assert client.get("/api/courses/1/draft-schedule?semesterId=1").status_code == 404
