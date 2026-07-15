from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.planning import Course, Lecturer, Room
from scripts import seed_dummy_planning_data as seed_script


def test_seeded_courses_have_current_semester_and_canonical_catalog_fields(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)
    seed_script.seed()
    with Session(engine) as db:
        courses = list(db.execute(select(Course)).scalars())
        assert courses
        assert all(course.current_semester_id is not None for course in courses)
        assert all(course.normalized_name == course.name.strip().casefold() for course in courses)
        assert all(course.normalized_name_key == course.normalized_name for course in courses)
        assert all(course.is_active and course.revision == 1 for course in courses)


def test_seeded_resources_have_deterministic_editable_codes_and_course_eligibility(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'resource-seed.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)

    seed_script.seed()
    seed_script.seed()

    with Session(engine) as db:
        lecturers = list(db.execute(select(Lecturer)).scalars())
        rooms = list(db.execute(select(Room)).scalars())
        courses = list(db.execute(select(Course)).scalars())
        assert len(lecturers) == 2
        assert len(rooms) == 3
        assert len(courses) == 3
        assert {item.reference_code for item in lecturers} == {"LECT-FISCHER", "LECT-NOVAK"}
        assert {item.reference_code for item in rooms} == {"ROOM-A-101", "ROOM-B-204", "ROOM-LAB"}
        assert all(item.normalized_reference_code == item.reference_code.casefold() for item in lecturers + rooms)
        assert all(item.is_active and item.revision == 1 for item in lecturers + rooms)
        assert all(len(course.eligible_lecturers) == 1 for course in courses)
        assert all(len(course.eligible_rooms) == 1 for course in courses)
