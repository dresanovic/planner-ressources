from __future__ import annotations

import sys
from datetime import date, time
from pathlib import Path
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.models.planning import (  # noqa: E402
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    Lecturer,
    Room,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)

ModelT = TypeVar("ModelT")


def one_by_name(db: Session, model: type[ModelT], name: str) -> ModelT | None:
    return db.execute(select(model).where(model.name == name)).scalars().first()


def upsert_named(db: Session, model: type[ModelT], name: str, **values: object) -> ModelT:
    if hasattr(model, "normalized_name"):
        canonical = name.strip().casefold()
        values.update(
            normalized_name=canonical,
            normalized_name_key=canonical,
            name_repair_required=False,
            is_active=True,
        )
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
    canonical_code = reference_code.strip().casefold()
    values.update(
        reference_code=reference_code.strip(),
        normalized_reference_code=canonical_code,
        is_active=True,
        revision=1,
    )
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
        )
        db.add(record)
    else:
        record.sort_order = sort_order
    return record


def seed() -> None:
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        lecturer_fischer = upsert_resource(
            db, Lecturer, "Prof. Elena Fischer", "LECT-FISCHER"
        )
        lecturer_novak = upsert_resource(
            db, Lecturer, "Prof. Martin Novak", "LECT-NOVAK"
        )

        cohort_ai = upsert_named(db, Cohort, "AI 2026", student_count=28)
        cohort_ds = upsert_named(db, Cohort, "Data Science 2026", student_count=24)
        cohort_biz = upsert_named(db, Cohort, "Business Informatics 2026", student_count=32)

        room_a = upsert_resource(db, Room, "Room A-101", "ROOM-A-101", capacity=36)
        room_b = upsert_resource(db, Room, "Room B-204", "ROOM-B-204", capacity=30)
        room_lab = upsert_resource(db, Room, "Planning Lab", "ROOM-LAB", capacity=34)

        semester = upsert_named(
            db,
            Semester,
            "Fall 2026",
            start_date=date(2026, 9, 7),
            end_date=date(2026, 12, 20),
        )

        full_time = upsert_named(db, StudyType, "Full-time")
        part_time = upsert_named(db, StudyType, "Part-time")
        db.flush()

        upsert_time_window(
            db,
            full_time,
            weekday=0,
            start_time=time(8, 0),
            end_time=time(12, 0),
            sort_order=1,
        )
        upsert_time_window(
            db,
            full_time,
            weekday=2,
            start_time=time(9, 0),
            end_time=time(13, 0),
            sort_order=2,
        )
        upsert_time_window(
            db,
            part_time,
            weekday=4,
            start_time=time(16, 0),
            end_time=time(20, 0),
            sort_order=1,
        )
        upsert_time_window(
            db,
            part_time,
            weekday=5,
            start_time=time(9, 0),
            end_time=time(13, 0),
            sort_order=2,
        )
        db.flush()

        operations = upsert_named(
            db,
            Course,
            "Operations Planning",
            total_units=20,
            min_session_units=2,
            max_session_units=4,
            cohort_id=cohort_ai.id,
            study_type_id=full_time.id,
            current_semester_id=semester.id,
        )
        resource_scheduling = upsert_named(
            db,
            Course,
            "Resource Scheduling",
            total_units=16,
            min_session_units=2,
            max_session_units=4,
            cohort_id=cohort_ds.id,
            study_type_id=part_time.id,
            current_semester_id=semester.id,
        )
        optimization = upsert_named(
            db,
            Course,
            "Applied Optimization",
            total_units=24,
            min_session_units=3,
            max_session_units=4,
            cohort_id=cohort_biz.id,
            study_type_id=full_time.id,
            current_semester_id=semester.id,
        )
        db.flush()

        for course, lecturer, room in (
            (operations, lecturer_fischer, room_a),
            (resource_scheduling, lecturer_novak, room_b),
            (optimization, lecturer_fischer, room_lab),
        ):
            ensure_eligibility(
                db,
                CourseEligibleLecturer,
                course_id=course.id,
                resource_field="lecturer_id",
                resource_id=lecturer.id,
            )
            ensure_eligibility(
                db,
                CourseEligibleRoom,
                course_id=course.id,
                resource_field="room_id",
                resource_id=room.id,
            )

        db.commit()

        print("Seeded dummy planning data:")
        print(f"- Semester: {semester.name}")
        print(f"- Lecturers: {lecturer_fischer.name}, {lecturer_novak.name}")
        print("- Courses: Operations Planning, Resource Scheduling, Applied Optimization")


if __name__ == "__main__":
    seed()
