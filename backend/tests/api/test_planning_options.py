from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import Cohort, Course, CourseEligibleLecturer, CourseEligibleRoom, Lecturer, Room, Semester, StudyType, StudyTypeTimeWindow


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
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()


def test_planning_options_filter_by_current_semester_and_keep_missing_window_unavailable(client, db_session):
    db_session.add_all([
        Lecturer(id=10, name="L"), Room(id=10, name="R", capacity=30),
        Cohort(id=10, name="C", student_count=20, normalized_name="c", normalized_name_key="c"),
        Semester(id=10, name="Fall", start_date=date(2026, 9, 1), end_date=date(2026, 12, 20), normalized_name="fall", normalized_name_key="fall"),
        Semester(id=11, name="Spring", start_date=date(2027, 2, 1), end_date=date(2027, 6, 20), normalized_name="spring", normalized_name_key="spring"),
        StudyType(id=10, name="Full-time", normalized_name="full-time", normalized_name_key="full-time"),
        Course(id=10, name="Visible unavailable", normalized_name="visible unavailable", normalized_name_key="visible unavailable", total_units=8, min_session_units=2, max_session_units=4, cohort_id=10, study_type_id=10, current_semester_id=10, eligible_lecturers=[CourseEligibleLecturer(lecturer_id=10)], eligible_rooms=[CourseEligibleRoom(room_id=10)]),
    ])
    db_session.commit()

    fall = client.get("/api/planning-options?semesterId=10").json()
    spring = client.get("/api/planning-options?semesterId=11").json()
    assert fall["courses"][0]["semesterId"] == 10
    assert fall["courses"][0]["availability"] == {"available": False, "reasons": ["MISSING_ACTIVE_TIME_WINDOW"]}
    assert spring["courses"] == []
    assert [(item["id"], item["name"]) for item in fall["lecturers"]] == [(10, "L")]
    assert fall["lecturers"][0]["referenceCode"]
    assert fall["courseResources"][0]["preferences"] == {"minimizeLecturerChanges": True, "minimizeRoomChanges": True}


def test_inactive_parent_excludes_course_and_inactive_window(client, db_session):
    db_session.add_all([
        Lecturer(id=20, name="L"), Room(id=20, name="R", capacity=30),
        Cohort(id=20, name="C", student_count=20, normalized_name="c20", normalized_name_key="c20", is_active=False),
        Semester(id=20, name="Fall", start_date=date(2026, 9, 1), end_date=date(2026, 12, 20), normalized_name="fall20", normalized_name_key="fall20"),
        StudyType(id=20, name="Full-time", normalized_name="full20", normalized_name_key="full20"),
        StudyTypeTimeWindow(id=20, study_type_id=20, weekday=0, start_time=time(8), end_time=time(12), sort_order=0, is_active=False),
        Course(id=20, name="Hidden", normalized_name="hidden20", normalized_name_key="hidden20", total_units=8, min_session_units=2, max_session_units=4, cohort_id=20, study_type_id=20, current_semester_id=20, eligible_lecturers=[CourseEligibleLecturer(lecturer_id=20)], eligible_rooms=[CourseEligibleRoom(room_id=20)]),
    ])
    db_session.commit()
    payload = client.get("/api/planning-options?semesterId=20").json()
    assert payload["courses"] == []
    assert payload["timeWindows"] == []


def test_planning_options_keep_courses_visible_with_resource_readiness_reasons(client, db_session):
    lecturer = Lecturer(id=30, name="L", is_active=False)
    room = Room(id=30, name="R", capacity=10)
    db_session.add_all([
        lecturer, room,
        Cohort(id=30, name="C", student_count=20, normalized_name="c30", normalized_name_key="c30"),
        Semester(id=30, name="Fall", start_date=date(2026, 9, 1), end_date=date(2026, 12, 20), normalized_name="fall30", normalized_name_key="fall30"),
        StudyType(id=30, name="Full-time", normalized_name="full30", normalized_name_key="full30"),
        StudyTypeTimeWindow(id=30, study_type_id=30, weekday=0, start_time=time(8), end_time=time(12), sort_order=0),
        Course(id=30, name="Needs resources", normalized_name="needs resources", normalized_name_key="needs resources", total_units=8, min_session_units=2, max_session_units=4, cohort_id=30, study_type_id=30, current_semester_id=30, eligible_lecturers=[CourseEligibleLecturer(lecturer_id=30)], eligible_rooms=[CourseEligibleRoom(room_id=30)]),
    ])
    db_session.commit()
    course = client.get("/api/planning-options?semesterId=30").json()["courses"][0]
    assert course["availability"]["available"] is False
    assert set(course["availability"]["reasons"]) == {"NO_ACTIVE_ELIGIBLE_LECTURER", "NO_USABLE_ELIGIBLE_ROOM"}


def test_planning_options_exclude_inactive_resources_from_new_choice_lists(client, db_session):
    db_session.add_all([
        Lecturer(id=40, name="Active Lecturer", reference_code="L-A", normalized_reference_code="l-a"),
        Lecturer(id=41, name="Inactive Lecturer", reference_code="L-I", normalized_reference_code="l-i", is_active=False),
        Room(id=40, name="Active Room", reference_code="R-A", normalized_reference_code="r-a", capacity=30),
        Room(id=41, name="Inactive Room", reference_code="R-I", normalized_reference_code="r-i", capacity=30, is_active=False),
    ])
    db_session.commit()

    payload = client.get("/api/planning-options").json()

    assert [item["name"] for item in payload["lecturers"]] == ["Active Lecturer"]
    assert [item["name"] for item in payload["rooms"]] == ["Active Room"]
