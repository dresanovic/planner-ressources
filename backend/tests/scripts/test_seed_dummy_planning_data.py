import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from app.models.planning import (
    Cohort,
    Course,
    CourseExamConfiguration,
    DraftSchedule,
    DraftSession,
    ExamSession,
    GenerationConstraintSet,
    InstitutionHoliday,
    Lecturer,
    Room,
    Semester,
    StudyTypeTimeWindow,
)
from scripts import seed_dummy_planning_data as seed_script


def test_seeded_courses_have_current_semester_and_canonical_catalog_fields(
    tmp_path, monkeypatch
):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)
    seed_script.seed()
    with Session(engine) as db:
        courses = list(db.execute(select(Course)).scalars())
        assert {course.name for course in courses} == {
            "Operations Planning",
            "KI Grundlagen",
            "SOD 2",
            "SSY",
            "VSY",
            "Mathematik 1",
            "Data Visualization",
        }
        assert all(course.current_semester_id is not None for course in courses)
        assert all(
            course.normalized_name == course.name.strip().casefold()
            for course in courses
        )
        assert all(
            course.normalized_name_key == course.normalized_name for course in courses
        )
        assert all(course.is_active for course in courses)
        assert {
            course.name: (
                course.total_units,
                course.min_session_units,
                course.max_session_units,
                course.revision,
            )
            for course in courses
        } == {
            "Operations Planning": (20, 2, 4, 1),
            "KI Grundlagen": (22, 3, 5, 3),
            "SOD 2": (24, 3, 4, 3),
            "SSY": (28, 3, 5, 1),
            "VSY": (34, 3, 5, 1),
            "Mathematik 1": (28, 2, 4, 1),
            "Data Visualization": (24, 3, 6, 1),
        }


def test_seeded_resources_have_deterministic_editable_codes_and_course_eligibility(
    tmp_path, monkeypatch
):
    engine = create_engine(f"sqlite:///{tmp_path / 'resource-seed.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)

    seed_script.seed()
    seed_script.seed()

    with Session(engine) as db:
        lecturers = list(db.execute(select(Lecturer)).scalars())
        rooms = list(db.execute(select(Room)).scalars())
        courses = list(db.execute(select(Course)).scalars())
        assert len(lecturers) == 8
        assert len(rooms) == 6
        assert len(courses) == 7
        assert {item.reference_code for item in lecturers} == {
            "LECT-1",
            "LECT-2",
            "DR",
            "SelS",
            "SG",
            "PB",
            "SafS",
            "ES",
        }
        assert {item.reference_code for item in rooms} == {
            "ROOM-1",
            "ROOM-2",
            "ROOM-3",
            "ROOM-7",
            "ROOM-8",
            "ROOM-9",
        }
        assert all(
            item.normalized_reference_code == item.reference_code.casefold()
            for item in lecturers + rooms
        )
        assert all(item.is_active for item in lecturers + rooms)
        assert {
            course.name: len(course.eligible_lecturers) for course in courses
        } == {
            "Operations Planning": 1,
            "KI Grundlagen": 2,
            "SOD 2": 1,
            "SSY": 1,
            "VSY": 1,
            "Mathematik 1": 1,
            "Data Visualization": 1,
        }
        assert all(len(course.eligible_rooms) == 1 for course in courses)


def test_seeded_baseline_excludes_generated_schedules_sessions_and_exams(
    tmp_path, monkeypatch
):
    engine = create_engine(f"sqlite:///{tmp_path / 'baseline-only.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)

    seed_script.seed()

    with Session(engine) as db:
        assert db.query(Cohort).count() == 3
        assert db.query(Semester).count() == 1
        assert db.query(StudyTypeTimeWindow).count() == 6
        assert db.query(InstitutionHoliday).count() == 13
        assert db.query(DraftSchedule).count() == 0
        assert db.query(DraftSession).count() == 0
        assert db.query(ExamSession).count() == 0
        assert db.query(CourseExamConfiguration).count() == 0
        assert db.query(GenerationConstraintSet).count() == 0
