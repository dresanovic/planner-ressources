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
    Lecturer,
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
            Lecturer(id=1, name="Ada Lovelace"),
            Cohort(id=1, name="AI 1", student_count=cohort_size),
            Room(id=1, name="R1", capacity=room_capacity),
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
                lecturer_id=1,
                cohort_id=1,
                room_id=1,
                study_type_id=1,
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
                lecturer_id=2,
                cohort_id=2,
                room_id=2,
                study_type_id=1,
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
        "lecturer": {"id": 1, "name": "Ada Lovelace"},
        "room": {"id": 1, "name": "R1"},
        "studyType": {"id": 1, "name": "Full-time"},
    }
    assert [session["units"] for session in payload["sessions"]] == [4, 4, 4, 4, 4]
    assert payload["sessions"][0]["startTime"] == "08:00"
    assert payload["sessions"][0]["endTime"] == "11:30"
    assert payload["sessions"][0] == {
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
    }

    read_response = client.get("/api/courses/1/draft-schedule")
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
    read_payload = client.get("/api/courses/1/draft-schedule").json()
    assert len(read_payload["sessions"]) == 5
    assert read_payload["sessions"][0]["date"] == "2026-09-09"


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
    assert client.get("/api/courses/1/draft-schedule").status_code == 404


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
    existing_sessions = client.get("/api/courses/1/draft-schedule").json()["sessions"]

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json=generation_payload(start="2026-09-01", end="2026-09-07"),
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "INVALID_PLANNING_PERIOD"
    assert client.get("/api/courses/1/draft-schedule").json()["sessions"] == existing_sessions


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
