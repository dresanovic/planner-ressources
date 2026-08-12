"""Shared normalized teaching-planning value objects.

Teaching placement is performed exclusively by ``semester_optimization``.
This module intentionally contains no independent schedule generator.
"""

from dataclasses import dataclass
from datetime import date, time

from app.models.planning import ResourceUnavailabilityPeriod


UNIT_MINUTES = 45
BREAK_MINUTES = 10


@dataclass(frozen=True)
class ResourceCandidatePlan:
    id: int
    normalized_code: str
    active: bool = True
    capacity: int | None = None
    unavailable_periods: tuple[ResourceUnavailabilityPeriod, ...] = ()


@dataclass(frozen=True)
class CoursePlan:
    id: int
    total_units: int
    min_session_units: int
    max_session_units: int
    lecturer_id: int
    cohort_id: int
    room_id: int
    study_type_id: int
    cohort_size: int
    room_capacity: int
    lecturer_candidates: tuple[ResourceCandidatePlan, ...] = ()
    room_candidates: tuple[ResourceCandidatePlan, ...] = ()


@dataclass(frozen=True)
class SemesterPlan:
    id: int
    start_date: date
    end_date: date


@dataclass(frozen=True)
class PlanningPeriodPlan:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class TimeWindowPlan:
    id: int | None
    weekday: int
    start_time: time
    end_time: time
    sort_order: int = 0
    constraint_window_index: int = 0


@dataclass(frozen=True)
class GeneratedSession:
    date: date
    start_time: time
    end_time: time
    units: int
    time_window_id: int | None
    constraint_window_index: int
    lecturer_id: int | None = None
    room_id: int | None = None


def session_duration_minutes(units: int) -> int:
    if units <= 0:
        raise ValueError("units must be positive")
    return units * UNIT_MINUTES + max(0, units - 1) * BREAK_MINUTES
