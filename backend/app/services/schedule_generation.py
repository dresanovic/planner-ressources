"""Shared normalized teaching-planning value objects.

Teaching placement is performed exclusively by ``semester_optimization``.
This module intentionally contains no independent schedule generator.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta

from app.models.planning import ResourceUnavailabilityPeriod


UNIT_MINUTES = 45
BREAK_MINUTES = 10


def format_clock(value: time | str) -> str:
    """Keep ordinary HH:MM clocks while preserving exact generated boundaries."""
    clock = time.fromisoformat(value) if isinstance(value, str) else value
    precision = 'microseconds' if clock.microsecond else 'seconds' if clock.second else 'minutes'
    return clock.isoformat(timespec=precision)


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
    weekday: int | None
    start_time: time
    end_time: time
    sort_order: int = 0
    constraint_window_index: int = 0
    kind: str = 'weekly'
    date: date | None = None
    is_intensive: bool = False
    revision: int = 1


def window_applies(window: TimeWindowPlan, day: date) -> bool:
    return window.date == day if window.kind == 'dated' else window.weekday == day.weekday()


def window_sort_key(window):
    return (0 if window.kind == 'weekly' else 1,
            window.weekday if window.kind == 'weekly' else window.date.toordinal(),
            window.start_time, window.end_time, window.sort_order, window.id or 0)


def window_has_occurrence(window, period: PlanningPeriodPlan) -> bool:
    if period.end_date < period.start_date:
        return False
    if window.kind == 'dated':
        return window.date is not None and period.start_date <= window.date <= period.end_date
    return period.start_date + timedelta(days=(window.weekday - period.start_date.weekday()) % 7) <= period.end_date


LE_MICROSECONDS = UNIT_MINUTES * 60_000_000


def time_ticks(value: time) -> int:
    return ((value.hour * 60 + value.minute) * 60 + value.second) * 1_000_000 + value.microsecond


def marked_intervals(day, windows):
    intervals = sorted((time_ticks(w.start_time),time_ticks(w.end_time)) for w in windows
                       if w.kind == 'dated' and w.is_intensive and window_applies(w,day))
    union = []
    for start,end in intervals:
        if union and start <= union[-1][1]:
            union[-1] = (union[-1][0],max(end,union[-1][1]))
        else:
            union.append((start,end))
    return union


def intensive_instruction_ticks(day, start_time, end_time, units, windows) -> int:
    """Actual instructional intersections, never elapsed breaks or source identity."""
    union = marked_intervals(day,windows)
    if not union:
        return 0
    start, end = time_ticks(start_time), time_ticks(end_time)
    total = 0
    for index in range(units):
        begin = start + index * (UNIT_MINUTES + BREAK_MINUTES) * 60_000_000
        finish = min(end,begin + LE_MICROSECONDS)
        if begin >= finish:
            break
        total += sum(max(0,min(finish,b)-max(begin,a)) for a,b in union)
    return total


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
