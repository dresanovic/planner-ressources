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
        json={"semesterId": 1, "selectedTimeWindowId": 1},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["courseId"] == 1
    assert payload["selectedTimeWindowId"] == 1
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
    }

    read_response = client.get("/api/courses/1/draft-schedule")
    assert read_response.status_code == 200
    assert read_response.json()["sessions"] == payload["sessions"]


def test_second_generation_replaces_previous_draft(client, db_session):
    seed_valid_course(db_session)

    client.post(
        "/api/courses/1/draft-schedule/generate",
        json={"semesterId": 1, "selectedTimeWindowId": 1},
    )
    second = client.post(
        "/api/courses/1/draft-schedule/generate",
        json={"semesterId": 1, "selectedTimeWindowId": 2},
    )

    assert second.status_code == 201
    read_payload = client.get("/api/courses/1/draft-schedule").json()
    assert read_payload["selectedTimeWindowId"] == 2
    assert len(read_payload["sessions"]) == 5


def test_generated_sessions_never_exceed_allowed_windows(client, db_session):
    seed_valid_course(db_session)

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json={"semesterId": 1, "selectedTimeWindowId": 1},
    )

    assert response.status_code == 201
    for session in response.json()["sessions"]:
        assert session["startTime"] >= "08:00"
        assert session["endTime"] <= "12:00"


def test_generation_returns_multiple_failure_reasons_without_partial_draft(client, db_session):
    seed_valid_course(db_session, room_capacity=40, cohort_size=45, min_units=5, max_units=4)

    response = client.post(
        "/api/courses/1/draft-schedule/generate",
        json={"semesterId": 1, "selectedTimeWindowId": 1},
    )

    assert response.status_code == 422
    codes = {error["code"] for error in response.json()["errors"]}
    assert codes == {"INSUFFICIENT_ROOM_CAPACITY", "INVALID_SESSION_PREFERENCE"}
    assert client.get("/api/courses/1/draft-schedule").status_code == 404
