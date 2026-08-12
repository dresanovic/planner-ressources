from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, time
from pathlib import Path
from typing import Any, TypeVar

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_ROOT / 'planner.db').as_posix()}"
DEFAULT_DATA_FILE = BACKEND_ROOT / "scripts" / "planning_baseline.json"

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
    StudyType,
    StudyTypeTimeWindow,
)

ModelT = TypeVar("ModelT")
JsonObject = dict[str, Any]


def parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def parse_time(value: str) -> time:
    return time.fromisoformat(value)


def serialize_date(value: date | None) -> str | None:
    return value.isoformat() if value else None


def serialize_time(value: time) -> str:
    return value.strftime("%H:%M")


def one_by_name(db: Session, model: type[ModelT], name: str) -> ModelT | None:
    return db.execute(select(model).where(model.name == name)).scalars().first()


def require_by_name(db: Session, model: type[ModelT], name: str) -> ModelT:
    record = one_by_name(db, model, name)
    if record is None:
        raise RuntimeError(f"Missing configured {model.__name__}: {name}")
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
    reference_code = reference_code.strip()
    values = {
        "reference_code": reference_code,
        "normalized_reference_code": reference_code.casefold(),
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


def sync_course_eligibility(
    db: Session,
    course: Course,
    *,
    lecturer_names: list[str],
    room_names: list[str],
) -> None:
    lecturer_ids = {
        require_by_name(db, Lecturer, lecturer_name).id for lecturer_name in lecturer_names
    }
    room_ids = {require_by_name(db, Room, room_name).id for room_name in room_names}

    db.execute(
        delete(CourseEligibleLecturer).where(
            CourseEligibleLecturer.course_id == course.id,
            CourseEligibleLecturer.lecturer_id.not_in(lecturer_ids or {-1}),
        )
    )
    db.execute(
        delete(CourseEligibleRoom).where(
            CourseEligibleRoom.course_id == course.id,
            CourseEligibleRoom.room_id.not_in(room_ids or {-1}),
        )
    )

    for lecturer_id in lecturer_ids:
        ensure_eligibility(
            db,
            CourseEligibleLecturer,
            course_id=course.id,
            resource_field="lecturer_id",
            resource_id=lecturer_id,
        )

    for room_id in room_ids:
        ensure_eligibility(
            db,
            CourseEligibleRoom,
            course_id=course.id,
            resource_field="room_id",
            resource_id=room_id,
        )


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


def load_seed_data(path: Path) -> JsonObject:
    with path.open(encoding="utf-8") as data_file:
        payload = json.load(data_file)
    if not isinstance(payload, dict):
        raise ValueError(f"Seed data must be a JSON object: {path}")
    if payload.get("version") != 1:
        raise ValueError(f"Unsupported seed data version in {path}: {payload.get('version')!r}")
    return payload


def seed_from_data(data: JsonObject) -> dict[str, int]:
    initialize_database(engine)

    with Session(engine) as db:
        for lecturer in data.get("lecturers", []):
            upsert_resource(db, Lecturer, **lecturer)

        for room in data.get("rooms", []):
            upsert_resource(db, Room, **room)

        for cohort in data.get("cohorts", []):
            upsert_named(db, Cohort, **cohort)

        for semester in data.get("semesters", []):
            upsert_named(
                db,
                Semester,
                semester["name"],
                start_date=parse_date(semester["start_date"]),
                end_date=parse_date(semester["end_date"]),
                is_active=semester.get("is_active", True),
                revision=semester.get("revision", 1),
            )

        for study_type in data.get("study_types", []):
            upsert_named(db, StudyType, **study_type)

        db.flush()

        for window in data.get("study_type_time_windows", []):
            study_type = require_by_name(db, StudyType, window["study_type"])
            upsert_time_window(
                db,
                study_type,
                weekday=window["weekday"],
                start_time=parse_time(window["start_time"]),
                end_time=parse_time(window["end_time"]),
                sort_order=window.get("sort_order", 0),
                is_active=window.get("is_active", True),
                revision=window.get("revision", 1),
            )

        db.flush()

        for course in data.get("courses", []):
            cohort = require_by_name(db, Cohort, course["cohort"])
            study_type = require_by_name(db, StudyType, course["study_type"])
            semester = require_by_name(db, Semester, course["current_semester"])
            configured_course = upsert_named(
                db,
                Course,
                course["name"],
                total_units=course["total_units"],
                min_session_units=course["min_session_units"],
                max_session_units=course["max_session_units"],
                cohort_id=cohort.id,
                study_type_id=study_type.id,
                current_semester_id=semester.id,
                is_active=course.get("is_active", True),
                revision=course.get("revision", 1),
            )
            db.flush()
            sync_course_eligibility(
                db,
                configured_course,
                lecturer_names=course.get("eligible_lecturers", []),
                room_names=course.get("eligible_rooms", []),
            )

        for holiday in data.get("institution_holidays", []):
            upsert_holiday(
                db,
                parse_date(holiday["date"]),
                holiday["name"],
                holiday.get("revision", 1),
            )

        if "resource_unavailability_periods" in data:
            db.execute(delete(ResourceUnavailabilityPeriod))
            db.flush()
            for period in data["resource_unavailability_periods"]:
                owner_type = period["owner_type"]
                owner = require_by_name(
                    db,
                    Lecturer if owner_type == "lecturer" else Room,
                    period["owner"],
                )
                configured_period = ResourceUnavailabilityPeriod(
                    lecturer_id=owner.id if owner_type == "lecturer" else None,
                    room_id=owner.id if owner_type == "room" else None,
                    kind=period["kind"],
                    start_date=parse_date(period.get("start_date")),
                    end_date=parse_date(period.get("end_date")),
                    start_time=parse_time(period["start_time"]),
                    end_time=parse_time(period["end_time"]),
                    revision=period.get("revision", 1),
                )
                configured_period.weekdays = [
                    ResourceUnavailabilityWeekday(weekday=weekday)
                    for weekday in period.get("weekdays", [])
                ]
                db.add(configured_period)

        if "course_exam_configurations" in data:
            db.execute(delete(CourseExamConfiguration))
            db.flush()
            for configuration in data["course_exam_configurations"]:
                course = require_by_name(db, Course, configuration["course"])
                semester = require_by_name(db, Semester, configuration["semester"])
                responsible_lecturer = (
                    require_by_name(db, Lecturer, configuration["responsible_lecturer"])
                    if configuration.get("responsible_lecturer")
                    else None
                )
                db.add(
                    CourseExamConfiguration(
                        course_id=course.id,
                        semester_id=semester.id,
                        enabled=configuration.get("enabled", False),
                        identifier=configuration.get("identifier"),
                        duration_minutes=configuration.get("duration_minutes"),
                        recommended_start_override=parse_date(
                            configuration.get("recommended_start_override")
                        ),
                        recommended_end_override=parse_date(
                            configuration.get("recommended_end_override")
                        ),
                        required_capacity=configuration.get("required_capacity"),
                        exam_type=configuration.get("exam_type"),
                        responsible_lecturer_id=responsible_lecturer.id
                        if responsible_lecturer
                        else None,
                        configuration_consumed=configuration.get(
                            "configuration_consumed", False
                        ),
                        revision=configuration.get("revision", 1),
                    )
                )

        db.commit()

    return {
        "lecturers": len(data.get("lecturers", [])),
        "rooms": len(data.get("rooms", [])),
        "cohorts": len(data.get("cohorts", [])),
        "semesters": len(data.get("semesters", [])),
        "study_types": len(data.get("study_types", [])),
        "study_type_time_windows": len(data.get("study_type_time_windows", [])),
        "courses": len(data.get("courses", [])),
        "institution_holidays": len(data.get("institution_holidays", [])),
        "resource_unavailability_periods": len(
            data.get("resource_unavailability_periods", [])
        ),
        "course_exam_configurations": len(data.get("course_exam_configurations", [])),
    }


def export_current_configuration(path: Path) -> None:
    initialize_database(engine)
    with Session(engine) as db:
        payload: JsonObject = {
            "version": 1,
            "lecturers": [
                {
                    "name": lecturer.name,
                    "reference_code": lecturer.reference_code,
                    "is_active": lecturer.is_active,
                    "revision": lecturer.revision,
                }
                for lecturer in db.execute(select(Lecturer).order_by(Lecturer.name)).scalars()
            ],
            "rooms": [
                {
                    "name": room.name,
                    "reference_code": room.reference_code,
                    "capacity": room.capacity,
                    "is_active": room.is_active,
                    "revision": room.revision,
                }
                for room in db.execute(select(Room).order_by(Room.name)).scalars()
            ],
            "cohorts": [
                {
                    "name": cohort.name,
                    "student_count": cohort.student_count,
                    "is_active": cohort.is_active,
                    "revision": cohort.revision,
                }
                for cohort in db.execute(select(Cohort).order_by(Cohort.name)).scalars()
            ],
            "semesters": [
                {
                    "name": semester.name,
                    "start_date": serialize_date(semester.start_date),
                    "end_date": serialize_date(semester.end_date),
                    "is_active": semester.is_active,
                    "revision": semester.revision,
                }
                for semester in db.execute(select(Semester).order_by(Semester.start_date)).scalars()
            ],
            "study_types": [
                {
                    "name": study_type.name,
                    "is_active": study_type.is_active,
                    "revision": study_type.revision,
                }
                for study_type in db.execute(select(StudyType).order_by(StudyType.name)).scalars()
            ],
            "study_type_time_windows": [
                {
                    "study_type": window.study_type.name,
                    "weekday": window.weekday,
                    "start_time": serialize_time(window.start_time),
                    "end_time": serialize_time(window.end_time),
                    "sort_order": window.sort_order,
                    "is_active": window.is_active,
                    "revision": window.revision,
                }
                for window in db.execute(
                    select(StudyTypeTimeWindow).join(StudyType).order_by(
                        StudyType.name,
                        StudyTypeTimeWindow.sort_order,
                        StudyTypeTimeWindow.weekday,
                    )
                ).scalars()
            ],
            "courses": [
                {
                    "name": course.name,
                    "total_units": course.total_units,
                    "min_session_units": course.min_session_units,
                    "max_session_units": course.max_session_units,
                    "cohort": course.cohort.name,
                    "study_type": course.study_type.name,
                    "current_semester": course.current_semester.name
                    if course.current_semester
                    else None,
                    "eligible_lecturers": [
                        item.lecturer.name for item in course.eligible_lecturers
                    ],
                    "eligible_rooms": [item.room.name for item in course.eligible_rooms],
                    "is_active": course.is_active,
                    "revision": course.revision,
                }
                for course in db.execute(select(Course).order_by(Course.name)).scalars()
            ],
            "institution_holidays": [
                {
                    "date": serialize_date(holiday.date),
                    "name": holiday.name,
                    "revision": holiday.revision,
                }
                for holiday in db.execute(
                    select(InstitutionHoliday).order_by(InstitutionHoliday.date)
                ).scalars()
            ],
            "resource_unavailability_periods": [
                {
                    "owner_type": "lecturer" if period.lecturer else "room",
                    "owner": period.lecturer.name if period.lecturer else period.room.name,
                    "kind": period.kind,
                    "start_date": serialize_date(period.start_date),
                    "end_date": serialize_date(period.end_date),
                    "start_time": serialize_time(period.start_time),
                    "end_time": serialize_time(period.end_time),
                    "weekdays": [weekday.weekday for weekday in period.weekdays],
                    "revision": period.revision,
                }
                for period in db.execute(
                    select(ResourceUnavailabilityPeriod).order_by(
                        ResourceUnavailabilityPeriod.kind,
                        ResourceUnavailabilityPeriod.start_time,
                    )
                ).scalars()
            ],
            "course_exam_configurations": [
                {
                    "course": configuration.course.name,
                    "semester": configuration.semester.name,
                    "enabled": configuration.enabled,
                    "identifier": configuration.identifier,
                    "duration_minutes": configuration.duration_minutes,
                    "recommended_start_override": serialize_date(
                        configuration.recommended_start_override
                    ),
                    "recommended_end_override": serialize_date(
                        configuration.recommended_end_override
                    ),
                    "required_capacity": configuration.required_capacity,
                    "exam_type": configuration.exam_type,
                    "responsible_lecturer": configuration.responsible_lecturer.name
                    if configuration.responsible_lecturer
                    else None,
                    "configuration_consumed": configuration.configuration_consumed,
                    "revision": configuration.revision,
                }
                for configuration in db.execute(
                    select(CourseExamConfiguration).order_by(CourseExamConfiguration.id)
                ).scalars()
            ],
        }

        scheduling_counts = {
            "draft_schedules": db.query(DraftSchedule).count(),
            "draft_sessions": db.query(DraftSession).count(),
            "exam_sessions": db.query(ExamSession).count(),
            "generation_constraint_sets": db.query(GenerationConstraintSet).count(),
        }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported planning configuration to {path}")
    print(
        "Excluded scheduling data: "
        + ", ".join(f"{name}={count}" for name, count in scheduling_counts.items())
    )


def database_target_label() -> str:
    database = engine.url.database
    if database is None:
        return str(engine.url)
    return str(Path(database).resolve())


def seed(data_file: Path = DEFAULT_DATA_FILE) -> None:
    data = load_seed_data(data_file)
    counts = seed_from_data(data)

    print(f"Seeded planning configuration from {data_file} in {database_target_label()}:")
    print(f"- Lecturers: {counts['lecturers']}")
    print(f"- Rooms: {counts['rooms']}")
    print(f"- Cohorts: {counts['cohorts']}")
    print(f"- Semesters: {counts['semesters']}")
    print(f"- Study types: {counts['study_types']}")
    print(f"- Time windows: {counts['study_type_time_windows']}")
    print(f"- Courses: {counts['courses']}")
    print(f"- Institution holidays: {counts['institution_holidays']}")
    print(f"- Resource unavailability periods: {counts['resource_unavailability_periods']}")
    print(f"- Course exam configurations: {counts['course_exam_configurations']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import or export editable planning setup data as JSON."
    )
    parser.add_argument(
        "--data-file",
        type=Path,
        default=DEFAULT_DATA_FILE,
        help="JSON planning setup file to import. Defaults to scripts/planning_baseline.json.",
    )
    parser.add_argument(
        "--export-current",
        type=Path,
        default=None,
        help="Write current non-scheduling setup data to this JSON file instead of importing.",
    )
    args = parser.parse_args()

    if args.export_current:
        export_current_configuration(args.export_current)
    else:
        seed(args.data_file)


if __name__ == "__main__":
    main()
