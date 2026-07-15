from __future__ import annotations

from datetime import date, time
from typing import Any

from app.models import planning


def _mapped_kwargs(model: type[Any], values: dict[str, Any]) -> dict[str, Any]:
    """Keep shared fixtures usable before and after the FS-008 model migration."""

    mapped = {column.key for column in model.__table__.columns}
    return {key: value for key, value in values.items() if key in mapped}


def make_lecturer(**overrides: Any):
    values = {
        "id": 1,
        "name": "Ada Lovelace",
        "reference_code": "LECT-ADA",
        "normalized_reference_code": "lect-ada",
        "is_active": True,
        "revision": 1,
    }
    values.update(overrides)
    return planning.Lecturer(**_mapped_kwargs(planning.Lecturer, values))


def make_room(**overrides: Any):
    values = {
        "id": 1,
        "name": "Room 101",
        "reference_code": "ROOM-101",
        "normalized_reference_code": "room-101",
        "capacity": 40,
        "is_active": True,
        "revision": 1,
    }
    values.update(overrides)
    return planning.Room(**_mapped_kwargs(planning.Room, values))


def make_course(**overrides: Any):
    values = {
        "id": 1,
        "name": "Planning 101",
        "total_units": 8,
        "min_session_units": 2,
        "max_session_units": 4,
        "lecturer_id": 1,
        "cohort_id": 1,
        "room_id": 1,
        "study_type_id": 1,
        "current_semester_id": 1,
        "is_active": True,
        "revision": 1,
    }
    values.update(overrides)
    return planning.Course(**_mapped_kwargs(planning.Course, values))


def make_course_eligible_lecturer(**overrides: Any):
    model = getattr(planning, "CourseEligibleLecturer")
    values = {"course_id": 1, "lecturer_id": 1}
    values.update(overrides)
    return model(**_mapped_kwargs(model, values))


def make_course_eligible_room(**overrides: Any):
    model = getattr(planning, "CourseEligibleRoom")
    values = {"course_id": 1, "room_id": 1}
    values.update(overrides)
    return model(**_mapped_kwargs(model, values))


def make_recurring_unavailability(**overrides: Any):
    model = getattr(planning, "ResourceUnavailabilityPeriod")
    values = {
        "id": 1,
        "lecturer_id": 1,
        "room_id": None,
        "kind": "recurring",
        "start_date": None,
        "end_date": None,
        "start_time": time(9),
        "end_time": time(11),
        "revision": 1,
    }
    values.update(overrides)
    return model(**_mapped_kwargs(model, values))


def make_dated_unavailability(**overrides: Any):
    model = getattr(planning, "ResourceUnavailabilityPeriod")
    values = {
        "id": 2,
        "lecturer_id": None,
        "room_id": 1,
        "kind": "dated",
        "start_date": date(2026, 10, 12),
        "end_date": date(2026, 10, 13),
        "start_time": time(15),
        "end_time": time(10),
        "revision": 1,
    }
    values.update(overrides)
    return model(**_mapped_kwargs(model, values))


def make_unavailability_weekday(**overrides: Any):
    model = getattr(planning, "ResourceUnavailabilityWeekday")
    values = {"period_id": 1, "weekday": 0}
    values.update(overrides)
    return model(**_mapped_kwargs(model, values))
