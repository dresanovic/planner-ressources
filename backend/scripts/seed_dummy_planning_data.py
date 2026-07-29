from __future__ import annotations

import os
import sys
from datetime import date, time
from pathlib import Path
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_ROOT / 'planner.db').as_posix()}"

if os.getenv("DATABASE_URL") in {None, "sqlite:///./planner.db"}:
    os.environ["DATABASE_URL"] = DEFAULT_DATABASE_URL

sys.path.insert(0, str(BACKEND_ROOT))

from app.db.schema import initialize_database  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models.planning import (  # noqa: E402
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    InstitutionHoliday,
    Lecturer,
    Room,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)

ModelT = TypeVar("ModelT")


LECTURERS = [
    {"name": "Prof. Elena Fischer", "reference_code": "LECT-1", "revision": 1},
    {"name": "Prof. Martin Novak", "reference_code": "LECT-2", "revision": 1},
    {"name": "Prof. Daniel Resanovic", "reference_code": "DR", "revision": 1},
    {"name": "Prof. Selver Softic", "reference_code": "SelS", "revision": 1},
    {"name": "Prof. Stefan Günter", "reference_code": "SG", "revision": 1},
    {"name": "Prof. Patrick Beer", "reference_code": "PB", "revision": 1},
    {"name": "Safet Softic", "reference_code": "SafS", "revision": 1},
    {"name": "Eva Schirgi", "reference_code": "ES", "revision": 1},
]

ROOMS = [
    {"name": "Room CZ-103", "reference_code": "ROOM-1", "capacity": 36, "revision": 2},
    {"name": "Room CR-402", "reference_code": "ROOM-2", "capacity": 30, "revision": 2},
    {"name": "Room CZ-106", "reference_code": "ROOM-3", "capacity": 30, "revision": 2},
    {"name": "Room CZ-107", "reference_code": "ROOM-7", "capacity": 36, "revision": 1},
    {"name": "Room CZ-108", "reference_code": "ROOM-8", "capacity": 36, "revision": 1},
    {"name": "Room CZ-109", "reference_code": "ROOM-9", "capacity": 32, "revision": 1},
]

COHORTS = [
    {"name": "AI and Business Analitics 2026", "student_count": 25, "revision": 2},
    {"name": "Business SW Dev 2026", "student_count": 25, "revision": 2},
    {"name": "Business Informatics 2026", "student_count": 35, "revision": 2},
]

SEMESTERS = [
    {
        "name": "Fall 2026",
        "start_date": date(2026, 9, 7),
        "end_date": date(2027, 2, 12),
        "revision": 2,
    }
]

STUDY_TYPES = [
    {"name": "Full-time", "revision": 1},
    {"name": "Part-time", "revision": 1},
]

STUDY_TYPE_TIME_WINDOWS = [
    {
        "study_type": "Full-time",
        "weekday": 1,
        "start_time": time(8, 0),
        "end_time": time(13, 0),
        "sort_order": 1,
        "is_active": True,
        "revision": 3,
    },
    {
        "study_type": "Full-time",
        "weekday": 2,
        "start_time": time(9, 0),
        "end_time": time(13, 0),
        "sort_order": 2,
        "is_active": True,
        "revision": 1,
    },
    {
        "study_type": "Part-time",
        "weekday": 4,
        "start_time": time(16, 0),
        "end_time": time(20, 0),
        "sort_order": 7740,
        "is_active": False,
        "revision": 2,
    },
    {
        "study_type": "Part-time",
        "weekday": 5,
        "start_time": time(9, 0),
        "end_time": time(15, 0),
        "sort_order": 7740,
        "is_active": True,
        "revision": 2,
    },
    {
        "study_type": "Full-time",
        "weekday": 0,
        "start_time": time(8, 15),
        "end_time": time(13, 45),
        "sort_order": 0,
        "is_active": True,
        "revision": 1,
    },
    {
        "study_type": "Part-time",
        "weekday": 4,
        "start_time": time(18, 0),
        "end_time": time(22, 0),
        "sort_order": 0,
        "is_active": True,
        "revision": 1,
    },
]

COURSES = [
    {
        "name": "Operations Planning",
        "total_units": 20,
        "min_session_units": 2,
        "max_session_units": 4,
        "cohort": "AI and Business Analitics 2026",
        "study_type": "Full-time",
        "current_semester": "Fall 2026",
        "revision": 1,
    },
    {
        "name": "KI Grundlagen",
        "total_units": 22,
        "min_session_units": 3,
        "max_session_units": 5,
        "cohort": "Business SW Dev 2026",
        "study_type": "Part-time",
        "current_semester": "Fall 2026",
        "revision": 3,
    },
    {
        "name": "SOD 2",
        "total_units": 24,
        "min_session_units": 3,
        "max_session_units": 4,
        "cohort": "Business Informatics 2026",
        "study_type": "Full-time",
        "current_semester": "Fall 2026",
        "revision": 3,
    },
    {
        "name": "SSY",
        "total_units": 28,
        "min_session_units": 3,
        "max_session_units": 5,
        "cohort": "Business SW Dev 2026",
        "study_type": "Full-time",
        "current_semester": "Fall 2026",
        "revision": 1,
    },
    {
        "name": "VSY",
        "total_units": 34,
        "min_session_units": 3,
        "max_session_units": 5,
        "cohort": "Business Informatics 2026",
        "study_type": "Part-time",
        "current_semester": "Fall 2026",
        "revision": 1,
    },
    {
        "name": "Mathematik 1",
        "total_units": 28,
        "min_session_units": 2,
        "max_session_units": 4,
        "cohort": "AI and Business Analitics 2026",
        "study_type": "Full-time",
        "current_semester": "Fall 2026",
        "revision": 1,
    },
    {
        "name": "Data Visualization",
        "total_units": 24,
        "min_session_units": 3,
        "max_session_units": 6,
        "cohort": "AI and Business Analitics 2026",
        "study_type": "Full-time",
        "current_semester": "Fall 2026",
        "revision": 1,
    },
]

ELIGIBLE_LECTURERS = [
    ("Operations Planning", "Prof. Elena Fischer"),
    ("KI Grundlagen", "Prof. Martin Novak"),
    ("KI Grundlagen", "Prof. Daniel Resanovic"),
    ("SOD 2", "Prof. Elena Fischer"),
    ("SSY", "Prof. Martin Novak"),
    ("VSY", "Prof. Daniel Resanovic"),
    ("Mathematik 1", "Eva Schirgi"),
    ("Data Visualization", "Prof. Selver Softic"),
]

ELIGIBLE_ROOMS = [
    ("Operations Planning", "Room CZ-103"),
    ("KI Grundlagen", "Room CR-402"),
    ("SOD 2", "Room CZ-103"),
    ("SSY", "Room CR-402"),
    ("VSY", "Room CZ-103"),
    ("Mathematik 1", "Room CZ-106"),
    ("Data Visualization", "Room CZ-106"),
]

INSTITUTION_HOLIDAYS = [
    (date(2026, 12, 25), "Weihnachten", 1),
    (date(2026, 11, 2), "Allerseelen", 1),
    (date(2026, 10, 26), "Österreichischer Nationalfeiertag (gesetzlicher Feiertag)", 1),
    (date(2026, 12, 8), "Mariä Empfängnis (gesetzlicher Feiertag)", 1),
    (date(2026, 12, 24), "Weihnachtsferien", 1),
    (date(2026, 12, 28), "Weihnachtsferien", 1),
    (date(2026, 12, 29), "Weihnachtsferien", 1),
    (date(2026, 12, 30), "Weihnachtsferien", 1),
    (date(2026, 12, 31), "Weihnachtsferien", 1),
    (date(2027, 1, 1), "Neujahr (gesetzlicher Feiertag)", 1),
    (date(2027, 1, 4), "Weihnachtsferien", 1),
    (date(2027, 1, 5), "Weihnachtsferien", 1),
    (date(2027, 1, 6), "Heilige Drei Könige (gesetzlicher Feiertag)", 1),
]


def one_by_name(db: Session, model: type[ModelT], name: str) -> ModelT | None:
    return db.execute(select(model).where(model.name == name)).scalars().first()


def require_by_name(db: Session, model: type[ModelT], name: str) -> ModelT:
    record = one_by_name(db, model, name)
    if record is None:
        raise RuntimeError(f"Missing seeded {model.__name__}: {name}")
    return record


def normalized_name_values(name: str) -> dict[str, object]:
    canonical = name.strip().casefold()
    return {
        "normalized_name": canonical,
        "normalized_name_key": canonical,
        "name_repair_required": False,
    }


def upsert_named(db: Session, model: type[ModelT], name: str, **values: object) -> ModelT:
    if hasattr(model, "normalized_name"):
        values = {**normalized_name_values(name), **values}
    values.setdefault("is_active", True)

    record = one_by_name(db, model, name)
    if record is None:
        record = model(name=name, **values)
        db.add(record)
    else:
        for key, value in values.items():
            setattr(record, key, value)
    return record


def upsert_resource(
    db: Session,
    model: type[ModelT],
    name: str,
    reference_code: str,
    **values: object,
) -> ModelT:
    values = {
        "reference_code": reference_code.strip(),
        "normalized_reference_code": reference_code.strip().casefold(),
        "is_active": True,
        **values,
    }
    return upsert_named(db, model, name, **values)


def ensure_eligibility(
    db: Session,
    model: type[ModelT],
    *,
    course_id: int,
    resource_field: str,
    resource_id: int,
) -> ModelT:
    record = (
        db.execute(
            select(model).where(
                model.course_id == course_id,
                getattr(model, resource_field) == resource_id,
            )
        )
        .scalars()
        .first()
    )
    if record is None:
        record = model(course_id=course_id, **{resource_field: resource_id})
        db.add(record)
    return record


def upsert_time_window(
    db: Session,
    study_type: StudyType,
    *,
    weekday: int,
    start_time: time,
    end_time: time,
    sort_order: int,
    is_active: bool,
    revision: int,
) -> StudyTypeTimeWindow:
    record = (
        db.execute(
            select(StudyTypeTimeWindow).where(
                StudyTypeTimeWindow.study_type_id == study_type.id,
                StudyTypeTimeWindow.weekday == weekday,
                StudyTypeTimeWindow.start_time == start_time,
                StudyTypeTimeWindow.end_time == end_time,
            )
        )
        .scalars()
        .first()
    )
    if record is None:
        record = StudyTypeTimeWindow(
            study_type_id=study_type.id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            sort_order=sort_order,
            is_active=is_active,
            revision=revision,
        )
        db.add(record)
    else:
        record.sort_order = sort_order
        record.is_active = is_active
        record.revision = revision
    return record


def upsert_holiday(db: Session, holiday_date: date, name: str, revision: int) -> InstitutionHoliday:
    record = (
        db.execute(
            select(InstitutionHoliday).where(InstitutionHoliday.date == holiday_date)
        )
        .scalars()
        .first()
    )
    if record is None:
        record = InstitutionHoliday(date=holiday_date, name=name, revision=revision)
        db.add(record)
    else:
        record.name = name
        record.revision = revision
    return record


def database_target_label() -> str:
    database = engine.url.database
    if database is None:
        return str(engine.url)
    return str(Path(database).resolve())


def seed() -> None:
    initialize_database(engine)

    with Session(engine) as db:
        for lecturer in LECTURERS:
            upsert_resource(db, Lecturer, **lecturer)

        for room in ROOMS:
            upsert_resource(db, Room, **room)

        for cohort in COHORTS:
            upsert_named(db, Cohort, **cohort)

        for semester in SEMESTERS:
            upsert_named(db, Semester, **semester)

        for study_type in STUDY_TYPES:
            upsert_named(db, StudyType, **study_type)

        db.flush()

        for window in STUDY_TYPE_TIME_WINDOWS:
            study_type = require_by_name(db, StudyType, window["study_type"])
            upsert_time_window(
                db,
                study_type,
                weekday=window["weekday"],
                start_time=window["start_time"],
                end_time=window["end_time"],
                sort_order=window["sort_order"],
                is_active=window["is_active"],
                revision=window["revision"],
            )

        db.flush()

        for course in COURSES:
            cohort = require_by_name(db, Cohort, course["cohort"])
            study_type = require_by_name(db, StudyType, course["study_type"])
            semester = require_by_name(db, Semester, course["current_semester"])
            upsert_named(
                db,
                Course,
                course["name"],
                total_units=course["total_units"],
                min_session_units=course["min_session_units"],
                max_session_units=course["max_session_units"],
                cohort_id=cohort.id,
                study_type_id=study_type.id,
                current_semester_id=semester.id,
                revision=course["revision"],
            )

        db.flush()

        for course_name, lecturer_name in ELIGIBLE_LECTURERS:
            course = require_by_name(db, Course, course_name)
            lecturer = require_by_name(db, Lecturer, lecturer_name)
            ensure_eligibility(
                db,
                CourseEligibleLecturer,
                course_id=course.id,
                resource_field="lecturer_id",
                resource_id=lecturer.id,
            )

        for course_name, room_name in ELIGIBLE_ROOMS:
            course = require_by_name(db, Course, course_name)
            room = require_by_name(db, Room, room_name)
            ensure_eligibility(
                db,
                CourseEligibleRoom,
                course_id=course.id,
                resource_field="room_id",
                resource_id=room.id,
            )

        for holiday_date, name, revision in INSTITUTION_HOLIDAYS:
            upsert_holiday(db, holiday_date, name, revision)

        db.commit()

    print(f"Seeded baseline planning configuration in {database_target_label()}:")
    print(f"- Lecturers: {len(LECTURERS)}")
    print(f"- Rooms: {len(ROOMS)}")
    print(f"- Cohorts: {len(COHORTS)}")
    print(f"- Semesters: {len(SEMESTERS)}")
    print(f"- Study types: {len(STUDY_TYPES)}")
    print(f"- Courses: {len(COURSES)}")
    print(f"- Institution holidays: {len(INSTITUTION_HOLIDAYS)}")


if __name__ == "__main__":
    seed()
