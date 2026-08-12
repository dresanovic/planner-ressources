import sys
from pathlib import Path
import json
from datetime import time

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
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
    Room,
    Semester,
    StudyTypeTimeWindow,
)
from scripts import create_seed_data
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


def test_seed_accepts_custom_json_data_file(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'custom-seed.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)
    data_file = tmp_path / "planning-setup.json"
    data_file.write_text(
        json.dumps(
            {
                "version": 1,
                "lecturers": [
                    {"name": "Dr. Custom", "reference_code": "CUSTOM", "revision": 1}
                ],
                "rooms": [
                    {
                        "name": "Room Custom",
                        "reference_code": "R-CUSTOM",
                        "capacity": 20,
                        "revision": 1,
                    }
                ],
                "cohorts": [
                    {"name": "Custom Cohort", "student_count": 18, "revision": 1}
                ],
                "semesters": [
                    {
                        "name": "Custom Semester",
                        "start_date": "2026-09-01",
                        "end_date": "2027-01-31",
                        "revision": 1,
                    }
                ],
                "study_types": [{"name": "Custom Type", "revision": 1}],
                "study_type_time_windows": [
                    {
                        "study_type": "Custom Type",
                        "weekday": 2,
                        "start_time": "08:00",
                        "end_time": "12:00",
                        "sort_order": 1,
                        "is_active": True,
                        "revision": 1,
                    }
                ],
                "courses": [
                    {
                        "name": "Custom Course",
                        "total_units": 16,
                        "min_session_units": 2,
                        "max_session_units": 4,
                        "cohort": "Custom Cohort",
                        "study_type": "Custom Type",
                        "current_semester": "Custom Semester",
                        "eligible_lecturers": ["Dr. Custom"],
                        "eligible_rooms": ["Room Custom"],
                        "revision": 1,
                    }
                ],
                "institution_holidays": [
                    {"date": "2026-12-24", "name": "Custom Holiday", "revision": 1}
                ],
            }
        ),
        encoding="utf-8",
    )

    seed_script.seed(data_file)

    with Session(engine) as db:
        course = db.execute(select(Course)).scalar_one()
        assert course.name == "Custom Course"
        assert course.cohort.name == "Custom Cohort"
        assert course.study_type.name == "Custom Type"
        assert course.current_semester.name == "Custom Semester"
        assert [item.lecturer.name for item in course.eligible_lecturers] == ["Dr. Custom"]
        assert [item.room.name for item in course.eligible_rooms] == ["Room Custom"]
        assert db.query(InstitutionHoliday).count() == 1


def test_export_current_configuration_excludes_scheduling_data(tmp_path, monkeypatch):
    source_engine = create_engine(f"sqlite:///{tmp_path / 'export-source.db'}")
    monkeypatch.setattr(seed_script, "engine", source_engine)
    seed_script.seed()

    with Session(source_engine) as db:
        course = db.execute(select(Course).where(Course.name == "Operations Planning")).scalar_one()
        semester = db.execute(select(Semester).where(Semester.name == "Fall 2026")).scalar_one()
        lecturer = db.execute(select(Lecturer).where(Lecturer.reference_code == "LECT-1")).scalar_one()
        db.add(
            CourseExamConfiguration(
                course_id=course.id,
                semester_id=semester.id,
                enabled=True,
                duration_minutes=90,
                responsible_lecturer_id=lecturer.id,
            )
        )
        period = ResourceUnavailabilityPeriod(
            lecturer_id=lecturer.id,
            kind="recurring",
            start_time=time(14, 0),
            end_time=time(16, 0),
            revision=1,
        )
        period.weekdays = [ResourceUnavailabilityWeekday(weekday=3)]
        db.add(period)
        db.commit()

    export_file = tmp_path / "exported-setup.json"
    seed_script.export_current_configuration(export_file)

    payload = json.loads(export_file.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert "draft_schedules" not in payload
    assert len(payload["resource_unavailability_periods"]) == 1
    assert len(payload["course_exam_configurations"]) == 1

    target_engine = create_engine(f"sqlite:///{tmp_path / 'export-target.db'}")
    monkeypatch.setattr(seed_script, "engine", target_engine)
    seed_script.seed(export_file)

    with Session(target_engine) as db:
        assert db.query(DraftSchedule).count() == 0
        assert db.query(DraftSession).count() == 0
        assert db.query(ExamSession).count() == 0
        assert db.query(GenerationConstraintSet).count() == 0
        assert db.query(ResourceUnavailabilityPeriod).count() == 1
        assert db.query(CourseExamConfiguration).count() == 1


def test_create_seed_data_script_writes_importable_json(tmp_path, monkeypatch):
    source_engine = create_engine(f"sqlite:///{tmp_path / 'create-source.db'}")
    monkeypatch.setattr(seed_script, "engine", source_engine)
    seed_script.seed()

    output_file = tmp_path / "generated-seed-data.json"
    create_seed_data.create_seed_data(output_file)

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert len(payload["courses"]) == 7

    target_engine = create_engine(f"sqlite:///{tmp_path / 'create-target.db'}")
    monkeypatch.setattr(seed_script, "engine", target_engine)
    seed_script.seed(output_file)

    with Session(target_engine) as db:
        assert db.query(Course).count() == 7
        assert db.query(DraftSchedule).count() == 0
