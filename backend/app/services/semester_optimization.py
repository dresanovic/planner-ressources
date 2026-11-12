from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from time import monotonic
from typing import Callable, Iterable, Mapping, Sequence
from threading import Event, Thread
from math import ceil, isfinite

from ortools.sat.python import cp_model

from app.services.resource_rules import resource_is_unavailable
from app.services.holiday_calendar import HolidayReference
from app.services.schedule_generation import (
    GeneratedSession,
    PlanningPeriodPlan,
    ResourceCandidatePlan,
    TimeWindowPlan,
    session_duration_minutes,
    window_applies,
    window_sort_key,
    intensive_instruction_ticks,
    marked_intervals,
    window_has_occurrence,
)


REASON_MESSAGES = {
    "LECTURER_OCCUPIED": "Zulässige Lehrpersonen sind durch feste Termine belegt.",
    "ROOM_OCCUPIED": "Zulässige Räume sind durch feste Termine belegt.",
    "COHORT_OCCUPIED": "Die Kohorte ist durch feste Termine belegt.",
    "ACTIVE_EXAM_BOUNDARY": "Lehrtermine müssen vor Beginn der aktiven Prüfung enden.",
    "COHORT_CALENDAR_WINDOW_UNAVAILABLE": "Kein aktives Kohortenzeitfenster ist lang genug für die minimale Termingröße.",
    "LECTURER_UNAVAILABLE": "Zulässige Lehrpersonen sind in sonst erlaubten Zeitfenstern nicht verfügbar.",
    "ROOM_UNAVAILABLE": "Zulässige Räume sind in sonst erlaubten Zeitfenstern nicht verfügbar.",
    "NO_ELIGIBLE_LECTURER": "Keine aktive zulässige Lehrperson ist zugeordnet.",
    "NO_ELIGIBLE_ROOM": "Kein aktiver zulässiger Raum ist zugeordnet.",
    "INSUFFICIENT_ROOM_CAPACITY": "Kein aktiver zulässiger Raum bietet genügend Plätze für die Kohorte.",
    "UNAVAILABLE_DATE": "Die ausgeschlossenen Tage schränken die sonst erlaubten Termine ein.",
    "NO_ALLOWED_DATE_OR_WINDOW": "Kein erlaubter Tag mit passendem Zeitfenster steht zur Verfügung.",
    "COURSE_CONSTRAINT": "Die Planungsgrenzen verhindern weitere Termine.",
    "SELECTED_COURSE_COMPETITION": "Andere ausgewählte Lehrveranstaltungen nutzen dieselben begrenzten Ressourcen.",
    "INVALID_PLANNING_INPUT": "Die Planungsdaten sind ungültig oder unvollständig.",
}


class OptimalResultNotProven(RuntimeError):
    pass


class OptimizationCancelled(RuntimeError):
    pass


@dataclass(frozen=True)
class OptimizationSearchControl:
    deadline: float
    cancelled: Callable[[], bool] = lambda: False
    clock: Callable[[], float] = monotonic
    progress: Callable[[str], None] = lambda objective: None
    checkpoint: Callable[["SemesterOptimizationResult"], None] | None = None

    def check(self):
        if self.cancelled():
            raise OptimizationCancelled("Optimization cancelled")
        if self.clock() >= self.deadline:
            raise OptimalResultNotProven("The optimization search allowance is exhausted.")


class OptimizationModelInvalid(RuntimeError):
    pass


class NoGeneratedAlternative(RuntimeError):
    def __init__(self, message, *, courses=()):
        super().__init__(message)
        self.courses = courses


def valid_unit_upper_bound(scheduled, required, bound, *, objective_key='total_units', same_problem=True):
    if objective_key != 'total_units' or not same_problem or isinstance(bound, bool) or not isinstance(bound, (int, float)):
        return None
    if (isinstance(bound, float) and not isfinite(bound)) or bound < scheduled:
        return None
    tightened = min(ceil(bound), required)
    return tightened if tightened >= scheduled else None


@dataclass(frozen=True)
class FixedSession:
    course_id: int
    cohort_id: int
    lecturer_id: int
    room_id: int
    date: date
    start_time: time
    end_time: time
    source_kind: str = field(default="teaching_session", kw_only=True)
    source_id: int | None = field(default=None, kw_only=True)
    units: int = field(default=0, kw_only=True)
    cohort_calendar_id: int | None = field(default=None, kw_only=True)
    marked_windows: tuple[TimeWindowPlan, ...] = field(default=(), kw_only=True)


@dataclass(frozen=True)
class CurrentSession(FixedSession):
    units: int = field()
    time_window_id: int | None = None
    constraint_window_index: int = 0


@dataclass(frozen=True)
class OptimizationCourse:
    course_id: int
    course_name: str | None
    total_units: int
    min_session_units: int
    max_session_units: int
    cohort_id: int
    cohort_size: int
    planning_period: PlanningPeriodPlan
    windows: tuple[TimeWindowPlan, ...]
    lecturers: tuple[ResourceCandidatePlan, ...]
    rooms: tuple[ResourceCandidatePlan, ...]
    current_sessions: tuple[CurrentSession, ...] = ()
    latest_teaching_end: datetime | None = None
    latest_teaching_source_id: int | None = None
    preferred_session_units: float | None = None
    explicit_lecturer_portions: tuple[tuple[int, int], ...] | None = None

    @property
    def preferred_size_twice(self) -> int:
        return (round(2 * self.preferred_session_units) if self.preferred_session_units is not None
                else self.min_session_units + self.max_session_units)


@dataclass(frozen=True)
class TemporalCandidate:
    candidate_id: int
    course_id: int
    cohort_id: int
    date: date
    start_time: time
    end_time: time
    units: int
    time_window_id: int | None
    constraint_window_index: int
    lecturer_ids: tuple[int, ...]
    room_ids: tuple[int, ...]
    canonical_rank: int


@dataclass(frozen=True)
class BlockingEvidence:
    code: str
    count: int
    message: str
    holiday_date: date | None = None
    holiday_name: str | None = None
    source_kind: str | None = None
    source_id: int | None = None


@dataclass(frozen=True)
class CandidateSet:
    candidates: tuple[TemporalCandidate, ...]
    evidence: tuple[BlockingEvidence, ...]


@dataclass(frozen=True)
class CourseOptimization:
    course_id: int
    sessions: tuple[GeneratedSession, ...]
    retained_current: bool
    scheduled_units: int
    lecturer_changes: int
    room_changes: int
    evidence: tuple[BlockingEvidence, ...]


@dataclass(frozen=True)
class ObjectiveEvidence:
    objective_key: str
    direction: str
    proof_status: str
    value: int | None


@dataclass(frozen=True)
class SemesterOptimizationResult:
    courses: tuple[CourseOptimization, ...]
    total_units: int
    conflicts: int
    lecturer_changes: int
    room_changes: int
    retained_drafts: int
    elapsed_milliseconds: int
    optimal: bool = True
    objectives: tuple[ObjectiveEvidence, ...] = ()
    unit_upper_bound: int | None = None
    search_exhausted: bool = False
    intensive_teaching_time: int = 0
    daily_variety: int = 0
    termination: str | None = None
    repair_attempts: int = 0


@dataclass
class _CourseVariables:
    course: OptimizationCourse
    candidate_set: CandidateSet
    temporal: dict[int, cp_model.IntVar] = field(default_factory=dict)
    lecturer: dict[tuple[int, int], cp_model.IntVar] = field(default_factory=dict)
    room: dict[tuple[int, int], cp_model.IntVar] = field(default_factory=dict)
    retain: cp_model.IntVar | None = None
    weekly_concentration: list[cp_model.IntVar] = field(default_factory=list)
    lecturer_changes: list[cp_model.IntVar] = field(default_factory=list)
    room_changes: list[cp_model.IntVar] = field(default_factory=list)


def canonical_minute(value: date, at: time) -> int:
    return value.toordinal() * 1440 + at.hour * 60 + at.minute


def week_start(value: date) -> date:
    return value - timedelta(days=value.weekday())


def weekly_concentration_cost(values: Sequence[date]) -> int:
    sessions_per_week = Counter(week_start(value) for value in values)
    return sum(count * (count - 1) // 2 for count in sessions_per_week.values())


def intervals_overlap(
    first_date: date,
    first_start: time,
    first_end: time,
    second_date: date,
    second_start: time,
    second_end: time,
) -> bool:
    return first_date == second_date and first_start < second_end and second_start < first_end


def _time_ticks(value: time) -> int:
    return ((value.hour * 60 + value.minute) * 60 + value.second) * 1_000_000 + value.microsecond


def _candidate_start_times(courses, fixed_sessions, day, control=None) -> tuple[time, ...]:
    """Event closure contains a left-shifted representative of every feasible packing.

    A session can move earlier until a window, fixed/retained session or resource
    availability boundary, or the end of another chosen session. Close all such
    boundaries under every allowed session duration. No arbitrary time grid or
    rounding excludes sub-minute availability boundaries.
    """
    windows = []
    seeds = set()
    durations = set()
    for course in courses:
        if control is not None: control.check()
        if not course.planning_period.start_date <= day <= course.planning_period.end_date:
            continue
        matching = [w for w in course.windows if window_applies(w, day, course.windows)]
        windows.extend(matching)
        seeds.update(_time_ticks(w.start_time) for w in matching)
        for units in range(max(1, course.min_session_units), course.max_session_units + 1):
            if control is not None: control.check()
            duration = session_duration_minutes(units) * 60_000_000
            if any(duration <= _time_ticks(w.end_time) - _time_ticks(w.start_time) for w in matching):
                durations.add(duration)
        for current in course.current_sessions:
            if current.date == day:
                seeds.update((_time_ticks(current.start_time), _time_ticks(current.end_time)))
        for resource in (*course.lecturers, *course.rooms):
            for period in resource.unavailable_periods:
                if ((period.kind == 'recurring' and day.weekday() in {w.weekday for w in period.weekdays})
                    or (period.kind != 'recurring' and period.end_date == day)):
                    seeds.add(_time_ticks(period.end_time))
    if not windows or not durations:
        return ()
    for fixed in fixed_sessions:
        if control is not None: control.check()
        if fixed.date == day:
            seeds.add(_time_ticks(fixed.end_time))
    intensive = any(marked_intervals(day,c.windows) for c in courses
                    if c.planning_period.start_date <= day <= c.planning_period.end_date)
    if intensive:
        # Intensive time is piecewise linear in session start. Its breakpoints
        # align marked boundaries with instructional starts/ends. Variety also
        # distinguishes positive overlap from endpoint contact, hence ±1 tick.
        for course in courses:
            if not course.planning_period.start_date <= day <= course.planning_period.end_date:
                continue
            for a,b in marked_intervals(day,course.windows):
                for unit in range(course.max_session_units):
                    if control is not None: control.check()
                    for offset in (unit*55*60_000_000,(unit*55+45)*60_000_000):
                        for boundary in (a,b):
                            seeds.update(boundary-offset+delta for delta in (-1,0,1))
        seeds.update(_time_ticks(w.end_time) for w in windows)
        seeds.update(_time_ticks(f.start_time) for f in fixed_sessions if f.date == day)
        # A right-shifted intensive optimum can end exactly when a resource
        # becomes unavailable. Reverse duration closure derives that start.
        for course in courses:
            if not course.planning_period.start_date <= day <= course.planning_period.end_date:
                continue
            for resource in (*course.lecturers, *course.rooms):
                for period in resource.unavailable_periods:
                    if control is not None:
                        control.check()
                    if ((period.kind == 'recurring' and day.weekday() in {w.weekday for w in period.weekdays})
                        or (period.kind != 'recurring' and period.start_date == day)):
                        seeds.add(_time_ticks(period.start_time))
    latest = max(_time_ticks(w.end_time) for w in windows) - min(durations)
    # End boundaries may lie after the latest feasible *start*. Retain them
    # through reverse closure before filtering the returned start candidates.
    closure_limit = max(_time_ticks(w.end_time) for w in windows) if intensive else latest
    starts = {value for value in seeds if 0 <= value <= closure_limit}
    pending = deque(sorted(starts))
    ordered_durations = sorted(durations)
    while pending:
        if control is not None: control.check()
        start = pending.popleft()
        for duration in ordered_durations:
            for value in ((start-duration,start+duration) if intensive else (start+duration,)):
                if 0 <= value <= closure_limit and value not in starts:
                    starts.add(value)
                    pending.append(value)
    midnight = datetime.combine(day, time.min)
    return tuple((midnight + timedelta(microseconds=value)).time() for value in sorted(starts) if value <= latest)


def generate_candidates(
    course: OptimizationCourse,
    fixed_sessions: Sequence[FixedSession],
    unavailable_dates: frozenset[date],
    holidays: Mapping[date, HolidayReference] | None = None,
    *,
    control: OptimizationSearchControl | None = None,
    start_times_for_date: Callable[[date], tuple[time, ...]] | None = None,
) -> CandidateSet:
    holidays = holidays or {}
    counts: Counter[str] = Counter()
    protected_sources: Counter[tuple[str, str, int | None]] = Counter()
    holiday_counts: Counter[tuple[date, str]] = Counter()
    candidates: list[TemporalCandidate] = []
    active_lecturers = tuple(sorted((item for item in course.lecturers if item.active), key=lambda item: (item.normalized_code, item.id)))
    active_rooms = tuple(sorted((item for item in course.rooms if item.active), key=lambda item: (item.normalized_code, item.id)))
    capacity_rooms = tuple(item for item in active_rooms if (item.capacity or 0) >= course.cohort_size)

    if not active_lecturers:
        counts["NO_ELIGIBLE_LECTURER"] += 1
    if not active_rooms:
        counts["NO_ELIGIBLE_ROOM"] += 1
    elif not capacity_rooms:
        counts["INSUFFICIENT_ROOM_CAPACITY"] += 1
    if course.min_session_units <= 0 or course.max_session_units < course.min_session_units:
        counts["INVALID_PLANNING_INPUT"] += 1
    if course.planning_period.start_date > course.planning_period.end_date or not course.windows:
        counts["NO_ALLOWED_DATE_OR_WINDOW"] += 1
    elif not any(
        datetime.combine(date.min, window.end_time)
        - datetime.combine(date.min, window.start_time)
        >= timedelta(minutes=session_duration_minutes(course.min_session_units))
        for window in course.windows
    ):
        counts["COHORT_CALENDAR_WINDOW_UNAVAILABLE"] += 1

    if (
        counts.get("INVALID_PLANNING_INPUT")
        or counts.get("COHORT_CALENDAR_WINDOW_UNAVAILABLE")
        or not active_lecturers
        or not capacity_rooms
    ):
        return CandidateSet((), _evidence(counts, protected_sources))

    ordered_windows = sorted(
        course.windows,
        key=window_sort_key,
    )
    cursor = course.planning_period.start_date
    raw: list[tuple] = []
    permitted_temporal_slot_found = False
    while cursor <= course.planning_period.end_date:
        if control is not None:
            control.check()
        matching = [window for window in ordered_windows if window_applies(window, cursor, ordered_windows)]
        starts = (start_times_for_date(cursor) if start_times_for_date else
            _candidate_start_times((course,), fixed_sessions, cursor, control)) if matching else ()
        if cursor in holidays:
            if _holiday_removes_feasible_candidate(
                course,
                fixed_sessions,
                cursor,
                matching,
                active_lecturers,
                capacity_rooms,
                starts,
                control,
            ):
                holiday_counts[(cursor, holidays[cursor].name)] = 1
            cursor += timedelta(days=1)
            continue
        if cursor in unavailable_dates:
            if matching:
                counts["UNAVAILABLE_DATE"] += 1
            cursor += timedelta(days=1)
            continue
        for window in matching:
            for start_time in starts:
                if not window.start_time <= start_time < window.end_time:
                    continue
                for units in range(course.min_session_units, course.max_session_units + 1):
                    if control is not None:
                        control.check()
                    end_dt = datetime.combine(cursor, start_time) + timedelta(minutes=session_duration_minutes(units))
                    end_time = end_dt.time()
                    if end_dt.date() != cursor or end_time > window.end_time:
                        counts["COURSE_CONSTRAINT"] += 1
                        continue
                    if course.latest_teaching_end is not None and end_dt > course.latest_teaching_end:
                        counts["ACTIVE_EXAM_BOUNDARY"] += 1
                        if course.latest_teaching_source_id is not None:
                            protected_sources[("ACTIVE_EXAM_BOUNDARY", "active_exam", course.latest_teaching_source_id)] += 1
                        continue
                    permitted_temporal_slot_found = True
                    cohort_blocked, lecturers, rooms = _candidate_resources(
                        course, fixed_sessions, cursor, start_time, end_time,
                        active_lecturers, capacity_rooms, counts, protected_sources)
                    if not cohort_blocked and lecturers and rooms:
                        raw.append((cursor, start_time, end_time, units, window, lecturers, rooms))
        cursor += timedelta(days=1)

    if not raw and not permitted_temporal_slot_found:
        counts["NO_ALLOWED_DATE_OR_WINDOW"] += 1
    for rank, item in enumerate(sorted(raw, key=lambda value: (value[0], value[1], value[3], value[4].sort_order, value[5], value[6]))):
        session_date, start, end, units, window, lecturers, rooms = item
        candidates.append(TemporalCandidate(
            candidate_id=rank,
            course_id=course.course_id,
            cohort_id=course.cohort_id,
            date=session_date,
            start_time=start,
            end_time=end,
            units=units,
            time_window_id=window.id,
            constraint_window_index=window.constraint_window_index,
            lecturer_ids=lecturers,
            room_ids=rooms,
            canonical_rank=rank + 1,
        ))
    holiday_evidence = tuple(
        BlockingEvidence(
            "INSTITUTION_HOLIDAY",
            count,
            f"Der unterrichtsfreie Tag „{name}“ am {day:%d.%m.%Y} wurde als mögliche Terminoption ausgeschlossen.",
            day,
            name,
        )
        for (day, name), count in sorted(holiday_counts.items())
    )
    return CandidateSet(tuple(candidates), (*_evidence(counts, protected_sources), *holiday_evidence))


def _holiday_removes_feasible_candidate(
    course: OptimizationCourse,
    fixed_sessions: Sequence[FixedSession],
    candidate_date: date,
    windows: Sequence[TimeWindowPlan],
    active_lecturers: Sequence[ResourceCandidatePlan],
    capacity_rooms: Sequence[ResourceCandidatePlan],
    starts: Sequence[time],
    control=None,
) -> bool:
    for window in windows:
        for start_time in starts:
            if not window.start_time <= start_time < window.end_time:
                continue
            for units in range(course.min_session_units, course.max_session_units + 1):
                if control is not None: control.check()
                end_dt = datetime.combine(candidate_date, start_time) + timedelta(minutes=session_duration_minutes(units))
                if (end_dt.date() != candidate_date or end_dt.time() > window.end_time
                    or (course.latest_teaching_end is not None and end_dt > course.latest_teaching_end)):
                    continue
                cohort_blocked, lecturers, rooms = _candidate_resources(
                    course, fixed_sessions, candidate_date, start_time, end_dt.time(),
                    active_lecturers, capacity_rooms)
                if not cohort_blocked and lecturers and rooms:
                    return True
    return False


def _candidate_resources(
    course: OptimizationCourse,
    fixed_sessions: Sequence[FixedSession],
    candidate_date: date,
    start_time: time,
    end_time: time,
    active_lecturers: Sequence[ResourceCandidatePlan],
    capacity_rooms: Sequence[ResourceCandidatePlan],
    counts: Counter[str] | None = None,
    protected_sources: Counter[tuple[str, str, int | None]] | None = None,
) -> tuple[bool, tuple[int, ...], tuple[int, ...]]:
    cohort_conflicts = [
        fixed
        for fixed in fixed_sessions
        if (
        fixed.cohort_id == course.cohort_id
        and intervals_overlap(candidate_date, start_time, end_time, fixed.date, fixed.start_time, fixed.end_time)
        )
    ]
    cohort_blocked = bool(cohort_conflicts)
    if cohort_blocked and counts is not None:
        counts["COHORT_OCCUPIED"] += 1
        _record_protected_sources(protected_sources, "COHORT_OCCUPIED", cohort_conflicts)

    lecturers = []
    for lecturer in active_lecturers:
        if resource_is_unavailable(lecturer.unavailable_periods, candidate_date, start_time, end_time):
            if counts is not None:
                counts["LECTURER_UNAVAILABLE"] += 1
            continue
        lecturer_conflicts = [
            fixed
            for fixed in fixed_sessions
            if (
            fixed.lecturer_id == lecturer.id
            and intervals_overlap(candidate_date, start_time, end_time, fixed.date, fixed.start_time, fixed.end_time)
            )
        ]
        if lecturer_conflicts:
            if counts is not None:
                counts["LECTURER_OCCUPIED"] += 1
                _record_protected_sources(protected_sources, "LECTURER_OCCUPIED", lecturer_conflicts)
            continue
        lecturers.append(lecturer.id)

    rooms = []
    for room in capacity_rooms:
        if resource_is_unavailable(room.unavailable_periods, candidate_date, start_time, end_time):
            if counts is not None:
                counts["ROOM_UNAVAILABLE"] += 1
            continue
        room_conflicts = [
            fixed
            for fixed in fixed_sessions
            if (
            fixed.room_id == room.id
            and intervals_overlap(candidate_date, start_time, end_time, fixed.date, fixed.start_time, fixed.end_time)
            )
        ]
        if room_conflicts:
            if counts is not None:
                counts["ROOM_OCCUPIED"] += 1
                _record_protected_sources(protected_sources, "ROOM_OCCUPIED", room_conflicts)
            continue
        rooms.append(room.id)

    return cohort_blocked, tuple(lecturers), tuple(rooms)


def _record_protected_sources(
    protected_sources: Counter[tuple[str, str, int | None]] | None,
    code: str,
    conflicts: Sequence[FixedSession],
) -> None:
    if protected_sources is None:
        return
    for fixed in conflicts:
        protected_sources[(code, fixed.source_kind, fixed.source_id)] += 1


def _evidence(
    counts: Counter[str],
    protected_sources: Counter[tuple[str, str, int | None]] | None = None,
) -> tuple[BlockingEvidence, ...]:
    sources = protected_sources or Counter()
    sourced_codes = {code for code, _kind, source_id in sources if source_id is not None}
    evidence = [
        BlockingEvidence(code, count, REASON_MESSAGES[code])
        for code, count in sorted(counts.items())
        if count > 0 and code in REASON_MESSAGES and code not in sourced_codes
    ]
    evidence.extend(
        BlockingEvidence(
            code,
            count,
            REASON_MESSAGES[code],
            source_kind=source_kind if source_id is not None else None,
            source_id=source_id,
        )
        for (code, source_kind, source_id), count in sorted(
            sources.items(), key=lambda item: (item[0][0], item[0][1], item[0][2] or 0)
        )
        if count > 0 and code in REASON_MESSAGES
    )
    return tuple(evidence)


def _current_sessions_respect_hard_constraints(
    course: OptimizationCourse,
    unavailable_dates: frozenset[date],
    holidays: Mapping[date, HolidayReference],
) -> bool:
    active_lecturers = {item.id: item for item in course.lecturers if item.active}
    active_rooms = {
        item.id: item
        for item in course.rooms
        if item.active and (item.capacity or 0) >= course.cohort_size
    }
    for session in course.current_sessions:
        if not course.planning_period.start_date <= session.date <= course.planning_period.end_date:
            return False
        if session.date in unavailable_dates or session.date in holidays:
            return False
        if session.cohort_id != course.cohort_id:
            return False
        if not any(
            window_applies(window, session.date, course.windows)
            and window.start_time <= session.start_time
            and session.end_time <= window.end_time
            for window in course.windows
        ):
            return False
        if (
            course.latest_teaching_end is not None
            and datetime.combine(session.date, session.end_time) > course.latest_teaching_end
        ):
            return False
        lecturer = active_lecturers.get(session.lecturer_id)
        if lecturer is None or resource_is_unavailable(
            lecturer.unavailable_periods,
            session.date,
            session.start_time,
            session.end_time,
        ):
            return False
        room = active_rooms.get(session.room_id)
        if room is None or resource_is_unavailable(
            room.unavailable_periods,
            session.date,
            session.start_time,
            session.end_time,
        ):
            return False
    return True


def optimize_semester(
    courses: Sequence[OptimizationCourse],
    fixed_sessions: Sequence[FixedSession],
    unavailable_dates: Iterable[date] = (),
    *,
    holidays: Mapping[date, HolidayReference] | None = None,
    deadline_seconds: float = 60.0,
    generated_only: bool = False,
    control: OptimizationSearchControl | None = None,
    allow_unproven: bool = False,
    incumbent: SemesterOptimizationResult | None = None,
) -> SemesterOptimizationResult:
    started = monotonic()
    control = control or OptimizationSearchControl(deadline=started + deadline_seconds)
    control.check()
    unavailable = frozenset(unavailable_dates)
    model = cp_model.CpModel()
    course_vars: dict[int, _CourseVariables] = {}
    all_temporal: list[tuple[TemporalCandidate, cp_model.IntVar]] = []
    lecturer_assignments: dict[int, list[tuple[TemporalCandidate, cp_model.IntVar]]] = defaultdict(list)
    room_assignments: dict[int, list[tuple[TemporalCandidate, cp_model.IntVar]]] = defaultdict(list)
    starts_by_date = {}
    def start_times_for_date(day):
        if day not in starts_by_date:
            starts_by_date[day] = _candidate_start_times(courses, fixed_sessions, day, control)
        return starts_by_date[day]

    for course in sorted(courses, key=lambda item: item.course_id):
        control.check()
        candidate_set = generate_candidates(course, fixed_sessions, unavailable, holidays, control=control,
            start_times_for_date=start_times_for_date)
        variables = _CourseVariables(course=course, candidate_set=candidate_set)
        course_vars[course.course_id] = variables
        by_date: dict[date, list[cp_model.IntVar]] = defaultdict(list)
        for candidate in candidate_set.candidates:
            control.check()
            selected = model.new_bool_var(f"course_{course.course_id}_candidate_{candidate.candidate_id}")
            variables.temporal[candidate.candidate_id] = selected
            all_temporal.append((candidate, selected))
            by_date[candidate.date].append(selected)
            lecturer_vars = []
            for lecturer_id in candidate.lecturer_ids:
                assigned = model.new_bool_var(f"candidate_{course.course_id}_{candidate.candidate_id}_lecturer_{lecturer_id}")
                variables.lecturer[(candidate.candidate_id, lecturer_id)] = assigned
                lecturer_assignments[lecturer_id].append((candidate, assigned))
                lecturer_vars.append(assigned)
            room_vars = []
            for room_id in candidate.room_ids:
                assigned = model.new_bool_var(f"candidate_{course.course_id}_{candidate.candidate_id}_room_{room_id}")
                variables.room[(candidate.candidate_id, room_id)] = assigned
                room_assignments[room_id].append((candidate, assigned))
                room_vars.append(assigned)
            model.add(sum(lecturer_vars) == selected)
            model.add(sum(room_vars) == selected)
        for date_vars in by_date.values():
            model.add(sum(date_vars) <= 1)
        dates_by_week: dict[date, list[tuple[date, list[cp_model.IntVar]]]] = defaultdict(list)
        for session_date, date_vars in by_date.items():
            dates_by_week[week_start(session_date)].append((session_date, date_vars))
        for week_index, week_dates in enumerate(sorted(dates_by_week.values())):
            ordered_dates = sorted(week_dates)
            for first_index, (_, first_vars) in enumerate(ordered_dates):
                for second_index, (_, second_vars) in enumerate(ordered_dates[first_index + 1:], start=first_index + 1):
                    same_week_pair = model.new_bool_var(
                        f"course_{course.course_id}_week_{week_index}_pair_{first_index}_{second_index}"
                    )
                    first_selected = sum(first_vars)
                    second_selected = sum(second_vars)
                    model.add(same_week_pair <= first_selected)
                    model.add(same_week_pair <= second_selected)
                    model.add(same_week_pair >= first_selected + second_selected - 1)
                    variables.weekly_concentration.append(same_week_pair)

        generated_units = sum(
            candidate.units * variables.temporal[candidate.candidate_id]
            for candidate in candidate_set.candidates
        )
        model.add(generated_units <= course.total_units)
        if course.current_sessions and not generated_only:
            retain = model.new_bool_var(f"course_{course.course_id}_retain_current")
            variables.retain = retain
            if variables.temporal:
                model.add(sum(variables.temporal.values()) <= len(variables.temporal) * (1 - retain))
            current_units = sum(session.units for session in course.current_sessions)
            if not _current_sessions_respect_hard_constraints(
                course,
                unavailable,
                holidays or {},
            ):
                model.add(retain == 0)
            elif current_units > course.total_units:
                model.add(retain == 1)
            else:
                model.add(generated_units >= current_units * (1 - retain))
        _add_continuity(model, variables, lecturer=True, control=control)
        _add_continuity(model, variables, lecturer=False, control=control)

    _add_selected_conflict_constraints(model, all_temporal, lecturer_assignments, room_assignments, control=control)
    conflict_terms = _add_retained_alternatives(model, course_vars, fixed_sessions, control=control)

    total_units_terms = []
    lecturer_change_terms = []
    room_change_terms = []
    retain_terms = []
    session_size_deviation_terms = []
    weekly_concentration_terms = []
    canonical_temporal_terms = []
    canonical_resource_terms = []
    max_session_size_deviation = 0
    for variables in course_vars.values():
        control.check()
        preferred_size_twice = variables.course.preferred_size_twice
        max_generated_sessions = (
            variables.course.total_units // variables.course.min_session_units
            if variables.course.min_session_units > 0
            else 0
        )
        course_size_deviation_bound = max_generated_sessions * max(
            abs(2 * variables.course.min_session_units - preferred_size_twice),
            abs(2 * variables.course.max_session_units - preferred_size_twice),
        )
        for candidate in variables.candidate_set.candidates:
            selected = variables.temporal[candidate.candidate_id]
            total_units_terms.append(candidate.units * selected)
            session_size_deviation_terms.append(
                abs(2 * candidate.units - preferred_size_twice) * selected
            )
            canonical_temporal_terms.append(
                candidate.canonical_rank * selected
            )
            canonical_resource_terms.extend(
                (rank + 1) * variables.lecturer[(candidate.candidate_id, lecturer_id)]
                for rank, lecturer_id in enumerate(candidate.lecturer_ids)
            )
            canonical_resource_terms.extend(
                (rank + 1) * variables.room[(candidate.candidate_id, room_id)]
                for rank, room_id in enumerate(candidate.room_ids)
            )
        lecturer_change_terms.extend(variables.lecturer_changes)
        room_change_terms.extend(variables.room_changes)
        weekly_concentration_terms.extend(variables.weekly_concentration)
        if variables.retain is not None:
            current_units = sum(session.units for session in variables.course.current_sessions)
            total_units_terms.append(current_units * variables.retain)
            current_size_deviation = sum(
                abs(2 * session.units - preferred_size_twice)
                for session in variables.course.current_sessions
            )
            course_size_deviation_bound = max(
                course_size_deviation_bound,
                current_size_deviation,
            )
            current_weekly_concentration = weekly_concentration_cost(
                [session.date for session in variables.course.current_sessions]
            )
            session_size_deviation_terms.append(
                current_size_deviation * variables.retain
            )
            weekly_concentration_terms.append(
                current_weekly_concentration * variables.retain
            )
            lecturer_change_terms.append(_count_current_changes(variables.course.current_sessions, "lecturer_id") * variables.retain)
            room_change_terms.append(_count_current_changes(variables.course.current_sessions, "room_id") * variables.retain)
            retain_terms.append(variables.retain)
        max_session_size_deviation += course_size_deviation_bound

    room_change_terms.extend(_cohort_day_room_penalties(model, course_vars, room_assignments, fixed_sessions, control))
    schedule_shape_terms = (
        sum(weekly_concentration_terms) * (max_session_size_deviation + 1)
        + sum(session_size_deviation_terms)
    )

    intensive_time, daily_variety = _intensive_objectives(model,course_vars,fixed_sessions,control)
    objectives = [
        ("total_units", "max", sum(total_units_terms)),
        ("intensive_teaching_time", "max", intensive_time),
        ("daily_variety", "max", daily_variety),
        ("conflicts", "min", sum(conflict_terms)),
        ("schedule_shape", "min", schedule_shape_terms),
        ("lecturer_changes", "min", sum(lecturer_change_terms)),
        ("room_changes", "min", sum(room_change_terms)),
        ("retained_drafts", "max", sum(retain_terms)),
        ("canonical_temporal", "min", sum(canonical_temporal_terms)),
        ("canonical_resource", "min", sum(canonical_resource_terms)),
    ]
    def decode(solver, proofs, stage, fully_proven=False, unit_bound=None):
        values = {key: int(solver.value(expression)) for key, _direction, expression in objectives}
        results: list[CourseOptimization] = []
        for course_id, variables in sorted(course_vars.items()):
            retained = variables.retain is not None and bool(solver.value(variables.retain))
            sessions: list[GeneratedSession] = []
            if retained:
                sessions = [
                    GeneratedSession(
                        date=item.date,
                        start_time=item.start_time,
                        end_time=item.end_time,
                        units=item.units,
                        time_window_id=item.time_window_id,
                        constraint_window_index=item.constraint_window_index,
                        lecturer_id=item.lecturer_id,
                        room_id=item.room_id,
                    )
                    for item in sorted(variables.course.current_sessions, key=lambda session: (session.date, session.start_time, session.lecturer_id, session.room_id))
                ]
            else:
                for candidate in variables.candidate_set.candidates:
                    if not solver.value(variables.temporal[candidate.candidate_id]):
                        continue
                    lecturer_id = next(item for item in candidate.lecturer_ids if solver.value(variables.lecturer[(candidate.candidate_id, item)]))
                    room_id = next(item for item in candidate.room_ids if solver.value(variables.room[(candidate.candidate_id, item)]))
                    sessions.append(GeneratedSession(
                        date=candidate.date,
                        start_time=candidate.start_time,
                        end_time=candidate.end_time,
                        units=candidate.units,
                        time_window_id=candidate.time_window_id,
                        constraint_window_index=candidate.constraint_window_index,
                        lecturer_id=lecturer_id,
                        room_id=room_id,
                    ))
            sessions.sort(key=lambda item: (item.date, item.start_time, item.lecturer_id or 0, item.room_id or 0))
            evidence = list(variables.candidate_set.evidence)
            scheduled = sum(item.units for item in sessions)
            results.append(CourseOptimization(
                course_id=course_id,
                sessions=tuple(sessions),
                retained_current=retained,
                scheduled_units=scheduled,
                lecturer_changes=_count_generated_changes(sessions, "lecturer_id"),
                room_changes=_count_generated_changes(sessions, "room_id"),
                evidence=tuple(_deduplicate_evidence(evidence)),
            ))
        result_by_course = {item.course_id: item for item in results}
        for index, course_result in enumerate(results):
            variables = course_vars[course_result.course_id]
            if course_result.scheduled_units >= variables.course.total_units:
                continue
            evidence = list(course_result.evidence)
            competing = any(
                candidate.course_id == course_result.course_id
                and any(
                    other_id != course_result.course_id
                    and any(
                        intervals_overlap(candidate.date, candidate.start_time, candidate.end_time, session.date, session.start_time, session.end_time)
                        and (
                            candidate.cohort_id == course_vars[other_id].course.cohort_id
                            or session.lecturer_id in candidate.lecturer_ids
                            or session.room_id in candidate.room_ids
                        )
                        for session in other_result.sessions
                    )
                    for other_id, other_result in result_by_course.items()
                )
                for candidate in variables.candidate_set.candidates
            )
            if competing:
                evidence.append(BlockingEvidence(
                    "SELECTED_COURSE_COMPETITION",
                    1,
                    REASON_MESSAGES["SELECTED_COURSE_COMPETITION"],
                ))
            if not evidence and fully_proven:
                evidence.append(BlockingEvidence(
                    "COURSE_CONSTRAINT",
                    1,
                    REASON_MESSAGES["COURSE_CONSTRAINT"],
                ))
            results[index] = replace(
                course_result,
                evidence=tuple(_deduplicate_evidence(evidence)),
            )
        if generated_only and values["total_units"] <= 0:
            course_details = []
            for course_result in results:
                course = course_vars[course_result.course_id].course
                name = course.course_name or f"Course {course.course_id}"
                reasons = ", ".join(item.message for item in course_result.evidence)
                course_details.append(f"{name}: {reasons}")
            raise NoGeneratedAlternative(
                "No non-empty valid generated alternative exists. "
                + "; ".join(course_details), courses=tuple(results)
            )
        return SemesterOptimizationResult(
            courses=tuple(results),
            optimal=fully_proven,
            objectives=tuple(ObjectiveEvidence(key, direction, 'proven' if key in proofs else 'unfinished' if index == stage else 'not_attempted', values[key])
                for index,(key,direction,_expression) in enumerate(objectives)),
            unit_upper_bound=(values['total_units'] if 'total_units' in proofs else
                valid_unit_upper_bound(values['total_units'], sum(c.total_units for c in courses), unit_bound)),
            total_units=values["total_units"],
            intensive_teaching_time=values['intensive_teaching_time'],
            daily_variety=values['daily_variety'],
            conflicts=values["conflicts"],
            lecturer_changes=values["lecturer_changes"],
            room_changes=values["room_changes"],
            retained_drafts=values["retained_drafts"],
            elapsed_milliseconds=max(int((monotonic() - started) * 1000), 0),
            search_exhausted=control.clock() >= control.deadline,
        )

    solver: cp_model.CpSolver | None = None
    tracked_vars = [var for variables in course_vars.values() for var in (
        list(variables.temporal.values()) + list(variables.lecturer.values()) + list(variables.room.values()) + ([variables.retain] if variables.retain is not None else [])
    )]
    if incumbent is None and generated_only and any(_needs_completion_hint(course) for course in courses):
        _add_completion_hint(model, course_vars, control)
    objective_values: dict[str, int] = {}
    # Try the course's preferred size first, then fall back without excluding any
    # allowed size. Keep canonical ranks and the coverage-first objectives intact.
    preferred_decisions = sorted(all_temporal, key=lambda item: (
        abs(2 * item[0].units - course_vars[item[0].course_id].course.preferred_size_twice),
        item[0].date, item[0].start_time, item[0].course_id, item[0].units,
    ))
    if preferred_decisions:
        model.add_decision_strategy([var for _, var in preferred_decisions],
                                    cp_model.CHOOSE_FIRST, cp_model.SELECT_MAX_VALUE)
    last_candidate = incumbent
    unit_bound = incumbent.unit_upper_bound if incumbent else None
    coverage_upper = sum(c.total_units if generated_only else
        max(c.total_units, sum(s.units for s in c.current_sessions)) for c in courses)
    if incumbent is not None:
        from app.services.optimization_incumbent import seed_incumbent
        last_candidate, objective_values = seed_incumbent(model, course_vars, objectives,
            incumbent, control, coverage_upper)
        unit_bound = last_candidate.unit_upper_bound
    def unfinished(candidate, stage):
        candidate = replace(candidate, optimal=False, objectives=tuple(
            replace(evidence, proof_status='unfinished') if index == stage else evidence
            for index, evidence in enumerate(candidate.objectives)))
        if control.checkpoint is not None:
            control.checkpoint(candidate)
        return candidate
    for stage, (objective_name, direction, expression) in enumerate(objectives):
        if objective_name in objective_values:
            continue
        if stage not in (0,len(objectives)-1) and isinstance(expression,int):
            objective_values[objective_name] = expression
            if last_candidate is not None:
                last_candidate = replace(last_candidate,objectives=tuple(
                    replace(evidence,proof_status='proven',value=expression) if index == stage else evidence
                    for index,evidence in enumerate(last_candidate.objectives)))
            continue
        try:
            control.check()
        except OptimalResultNotProven:
            if allow_unproven and last_candidate is not None:
                return unfinished(last_candidate, stage)
            raise
        control.progress(objective_name)
        remaining = control.deadline - control.clock()
        model.clear_objective()
        if direction == "max":
            model.maximize(expression)
        else:
            model.minimize(expression)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = remaining
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0
        solver.parameters.cp_model_presolve = True
        if stage == 0:
            solver.parameters.search_branching = cp_model.FIXED_SEARCH
        finished = Event()
        def watch_search(active_solver=solver):
            while not finished.wait(.05):
                if control.cancelled() or control.clock() >= control.deadline:
                    active_solver.stop_search()
                    return
        watcher = Thread(target=watch_search, daemon=True)
        watcher.start()
        class Checkpoint(cp_model.CpSolverSolutionCallback):
            last_sent = -float('inf')
            def on_solution_callback(self):
                nonlocal last_candidate
                if control.cancelled():
                    self.stop_search()
                    return
                complete = stage == 0 and int(self.value(expression)) == coverage_upper
                if monotonic() - self.last_sent < .25 and not complete:
                    return
                self.last_sent = monotonic()
                try:
                    proofs = {**objective_values, 'total_units': coverage_upper} if complete else objective_values
                    last_candidate = decode(self, proofs, stage,
                        unit_bound=coverage_upper if complete else unit_bound)
                    if control.checkpoint is not None:
                        control.checkpoint(last_candidate)
                except NoGeneratedAlternative:
                    pass
                if complete:
                    self.stop_search()
        try:
            status = solver.solve(model, Checkpoint()) if allow_unproven and control.checkpoint is not None else solver.solve(model)
        finally:
            finished.set()
            watcher.join()
        if control.cancelled():
            raise OptimizationCancelled("Optimization cancelled")
        if status == cp_model.MODEL_INVALID:
            raise OptimizationModelInvalid("The semester optimization model is invalid.")
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            value = int(solver.value(expression))
            if objective_name == 'total_units':
                unit_bound = solver.best_objective_bound
            coverage_complete = stage == 0 and value == coverage_upper
            if status == cp_model.OPTIMAL or coverage_complete:
                objective_values[objective_name] = value
            if allow_unproven or stage == len(objectives)-1:
                last_candidate = decode(solver, objective_values, stage,
                    fully_proven=status == cp_model.OPTIMAL and stage == len(objectives)-1,
                    unit_bound=unit_bound)
                if control.checkpoint is not None:
                    control.checkpoint(last_candidate)
        if status != cp_model.OPTIMAL and not (status == cp_model.FEASIBLE and coverage_complete):
            if allow_unproven and last_candidate is not None:
                return unfinished(last_candidate, stage)
            raise OptimalResultNotProven(
                f"A fully optimal semester result was not proven for {objective_name} within the operation deadline."
            )
        model.add(expression == value)
        model.clear_hints()
        for variable in tracked_vars:
            model.add_hint(variable, solver.value(variable))


    assert last_candidate is not None
    return last_candidate


def _needs_completion_hint(course: OptimizationCourse) -> bool:
    preferred_twice = course.preferred_size_twice
    preferred = preferred_twice // 2
    return (preferred_twice % 2 == 0 and preferred > 0
            and 0 < course.total_units % preferred < course.min_session_units)


def _construct_completion(course_vars, control, *, date_order=None):
    """Construct a generated arrangement; never constrain or prove preferences.

    Prefer the usual session size unless that would leave an unfillable tail.
    Scarce-date courses go first only in this constructive hint, not in an
    objective or constraint. Native search can replace every suggested choice.
    """
    dates_by_course = {}
    for course_id, variables in course_vars.items():
        dates = defaultdict(list)
        for candidate in variables.candidate_set.candidates:
            control.check()
            dates[candidate.date].append(candidate)
        dates_by_course[course_id] = dates
    occupied = defaultdict(list)
    selected = {}

    def free(kind, resource_id, candidate):
        return all(candidate.end_time <= start or end <= candidate.start_time
                   for start, end in occupied[(kind, resource_id, candidate.date)])

    for course_id in sorted(course_vars, key=lambda key: (len(dates_by_course[key]), key)):
        variables = course_vars[course_id]
        course = variables.course
        remaining = course.total_units
        dates = sorted(dates_by_course[course_id].items())
        if date_order is not None:
            dates = date_order(course, dates)
        for index, (_day, candidates) in enumerate(dates):
            control.check()
            if remaining < course.min_session_units:
                break
            future_dates = len(dates) - index - 1
            best = None
            best_key = None
            for candidate in candidates:
                control.check()
                if candidate.units > remaining or not free('cohort', course.cohort_id, candidate):
                    continue
                lecturer = next((key for key in candidate.lecturer_ids if free('lecturer', key, candidate)), None)
                room = next((key for key in candidate.room_ids if free('room', key, candidate)), None)
                if lecturer is None or room is None:
                    continue
                tail = remaining - candidate.units
                # Whole sessions of any allowed size can represent the tail
                # only if some session count fits both its LE and date bounds.
                can_complete = (tail == 0 or
                    (tail + course.max_session_units - 1) // course.max_session_units
                    <= min(future_dates, tail // course.min_session_units))
                preference = abs(2 * candidate.units - course.preferred_size_twice)
                key = (not can_complete, preference if can_complete else -candidate.units,
                       candidate.canonical_rank, lecturer, room)
                if best_key is None or key < best_key:
                    best_key, best = key, (candidate, lecturer, room)
            if best is None:
                continue
            candidate, lecturer, room = best
            selected[(course_id, candidate.candidate_id)] = (lecturer, room)
            remaining -= candidate.units
            for kind, resource in (('cohort', course.cohort_id), ('lecturer', lecturer), ('room', room)):
                occupied[(kind, resource, candidate.date)].append((candidate.start_time, candidate.end_time))

    return selected


def _add_completion_hint(model, course_vars, control):
    selected = _construct_completion(course_vars, control)
    if not selected:
        return
    for course_id, variables in course_vars.items():
        for candidate_id, variable in variables.temporal.items():
            control.check()
            model.add_hint(variable, int((course_id, candidate_id) in selected))
        for kind, assignments in (('lecturer', variables.lecturer), ('room', variables.room)):
            resource_index = 0 if kind == 'lecturer' else 1
            for (candidate_id, resource_id), variable in assignments.items():
                control.check()
                choice = selected.get((course_id, candidate_id))
                model.add_hint(variable, int(choice is not None and choice[resource_index] == resource_id))



def _add_selected_conflict_constraints(model, all_temporal, lecturer_assignments, room_assignments, *, control=None):
    cohorts = defaultdict(list)
    for candidate, selected in all_temporal:
        cohorts[candidate.cohort_id].append((candidate, selected))
    for kind, assignments in (('cohort', cohorts), ('lecturer', lecturer_assignments), ('room', room_assignments)):
        for resource_id, items in assignments.items():
            days = defaultdict(list)
            for candidate, selected in items:
                if control is not None: control.check()
                start = _time_ticks(candidate.start_time)
                duration = _time_ticks(candidate.end_time) - start
                interval = model.new_optional_fixed_size_interval_var(start, duration, selected,
                    f'{kind}_{resource_id}_{candidate.date}_{candidate.course_id}_{candidate.candidate_id}')
                days[candidate.date].append(interval)
            for intervals in days.values():
                if control is not None: control.check()
                model.add_no_overlap(intervals)


def _add_retained_alternatives(model, course_vars, fixed_sessions, *, control=None):
    conflict_terms = []
    retained = [item for item in course_vars.values() if item.retain is not None]
    for variables in retained:
        if control is not None:
            control.check()
        assert variables.retain is not None
        fixed_conflicts = 0
        for current in variables.course.current_sessions:
            for fixed in fixed_sessions:
                if not intervals_overlap(current.date, current.start_time, current.end_time, fixed.date, fixed.start_time, fixed.end_time):
                    continue
                fixed_conflicts += int(current.lecturer_id == fixed.lecturer_id)
                fixed_conflicts += int(current.room_id == fixed.room_id)
                fixed_conflicts += int(current.cohort_id == fixed.cohort_id)
        if fixed_conflicts:
            conflict_terms.append(fixed_conflicts * variables.retain)
        for other in course_vars.values():
            if other.course.course_id == variables.course.course_id:
                continue
            for current in variables.course.current_sessions:
                for candidate in other.candidate_set.candidates:
                    if not intervals_overlap(current.date, current.start_time, current.end_time, candidate.date, candidate.start_time, candidate.end_time):
                        continue
                    if current.cohort_id == candidate.cohort_id:
                        model.add(variables.retain + other.temporal[candidate.candidate_id] <= 1)
                    for lecturer_id in candidate.lecturer_ids:
                        if current.lecturer_id == lecturer_id:
                            model.add(variables.retain + other.lecturer[(candidate.candidate_id, lecturer_id)] <= 1)
                    for room_id in candidate.room_ids:
                        if current.room_id == room_id:
                            model.add(variables.retain + other.room[(candidate.candidate_id, room_id)] <= 1)
    for index, first in enumerate(retained):
        for second in retained[index + 1:]:
            pair_count = 0
            for one in first.course.current_sessions:
                for two in second.course.current_sessions:
                    if intervals_overlap(one.date, one.start_time, one.end_time, two.date, two.start_time, two.end_time):
                        pair_count += int(one.lecturer_id == two.lecturer_id)
                        pair_count += int(one.room_id == two.room_id)
                        pair_count += int(one.cohort_id == two.cohort_id)
            if pair_count:
                pair = model.new_bool_var(f"retain_conflict_{first.course.course_id}_{second.course.course_id}")
                model.add(pair <= first.retain)
                model.add(pair <= second.retain)
                model.add(pair >= first.retain + second.retain - 1)
                conflict_terms.append(pair_count * pair)
    return conflict_terms


def intensive_arrangement(courses, fixed_sessions, sessions_by_course, *, control=None):
    def checked(values):
        for value in values:
            if control:
                control.check()
            yield value
    courses = tuple(checked(courses))
    fixed_sessions = tuple(checked(fixed_sessions))
    cohorts = {c.cohort_id for c in courses}
    applicable = any(w.kind == 'dated' and w.is_intensive and window_has_occurrence(w,c.planning_period)
                     for c in checked(courses) for w in checked(c.windows))
    applicable = applicable or any(f.source_kind == 'teaching_session' and f.cohort_id in cohorts
        and marked_intervals(f.date,f.marked_windows) for f in checked(fixed_sessions))
    if not applicable:
        return None
    total = ticks = 0
    presence = defaultdict(set)
    for course in checked(courses):
        for session in checked(sessions_by_course.get(course.course_id,())):
            total += session.units
            overlap = intensive_instruction_ticks(session.date,session.start_time,session.end_time,session.units,course.windows)
            ticks += overlap
            if overlap:
                presence[(session.date,course.cohort_id)].add(course.course_id)
    for fixed in checked(fixed_sessions):
        if (fixed.source_kind == 'teaching_session' and fixed.cohort_id in cohorts
            and intensive_instruction_ticks(fixed.date,fixed.start_time,fixed.end_time,fixed.units,fixed.marked_windows)):
            presence[(fixed.date,fixed.cohort_id)].add(fixed.course_id)
    rows = [dict(cohortId=cohort,date=day.isoformat(),distinctCourseIds=sorted(ids),
                 distinctLvCount=len(ids),varietyContribution=max(0,len(ids)-1))
            for (day,cohort),ids in checked(sorted(presence.items()))]
    if control:
        control.check()
    return total,ticks,sum(row['varietyContribution'] for row in rows),rows


def _intensive_objectives(model, course_vars, fixed_sessions, control):
    terms = []
    presence = defaultdict(lambda: defaultdict(list))
    for variables in course_vars.values():
        course = variables.course
        for candidate in variables.candidate_set.candidates:
            control.check()
            ticks = intensive_instruction_ticks(candidate.date,candidate.start_time,candidate.end_time,candidate.units,course.windows)
            if ticks:
                selected = variables.temporal[candidate.candidate_id]
                terms.append(ticks * selected)
                presence[(course.cohort_id,candidate.date)][course.course_id].append(selected)
        if variables.retain is not None:
            for session in course.current_sessions:
                ticks = intensive_instruction_ticks(session.date,session.start_time,session.end_time,session.units,course.windows)
                if ticks:
                    terms.append(ticks * variables.retain)
                    presence[(course.cohort_id,session.date)][course.course_id].append(variables.retain)
    cohorts = {v.course.cohort_id for v in course_vars.values()}
    for fixed in fixed_sessions:
        if (fixed.source_kind == 'teaching_session' and fixed.cohort_id in cohorts
            and intensive_instruction_ticks(fixed.date,fixed.start_time,fixed.end_time,fixed.units,fixed.marked_windows)):
            presence[(fixed.cohort_id,fixed.date)][fixed.course_id].append(1)
    contributions = []
    for index,(_pair, courses) in enumerate(sorted(presence.items())):
        control.check()
        if len(courses) < 2:
            continue
        lvs = []
        for course_id, choices in sorted(courses.items()):
            if 1 in [value for value in choices if isinstance(value,int)]:
                lvs.append(1)
            else:
                used = model.new_bool_var(f'intensive_{index}_lv_{course_id}')
                model.add_max_equality(used, choices)
                lvs.append(used)
        extra = model.new_int_var(0,len(courses)-1,f'intensive_{index}_variety')
        model.add_max_equality(extra,[sum(lvs)-1,0])
        contributions.append(extra)
    return sum(terms),sum(contributions)


def _cohort_day_room_penalties(model, course_vars, room_assignments, fixed_sessions, control):
    """Soft cost for each additional room used by a cohort on one date."""
    groups = defaultdict(lambda: defaultdict(list))
    cohorts = {variables.course.cohort_id for variables in course_vars.values()}
    for room_id, assignments in room_assignments.items():
        for candidate, assigned in assignments:
            control.check()
            groups[(candidate.cohort_id, candidate.date)][room_id].append(assigned)
    for variables in course_vars.values():
        if variables.retain is not None:
            for session in variables.course.current_sessions:
                groups[(variables.course.cohort_id, session.date)][session.room_id].append(variables.retain)
    for session in fixed_sessions:
        if session.cohort_id in cohorts:
            groups[(session.cohort_id, session.date)][session.room_id].append(1)
    penalties = []
    for index, rooms in enumerate(groups.values()):
        control.check()
        if len(rooms) < 2:
            continue
        used_rooms = []
        for room_id, assignments in rooms.items():
            used = model.new_bool_var(f'cohort_day_{index}_room_{room_id}_used')
            model.add_max_equality(used, assignments)
            used_rooms.append(used)
        extra = model.new_int_var(0, len(rooms) - 1, f'cohort_day_{index}_extra_rooms')
        model.add_max_equality(extra, [sum(used_rooms) - 1, 0])
        penalties.append(extra)
    return penalties


def _add_continuity(model, variables: _CourseVariables, *, lecturer: bool, control=None):
    candidates = variables.candidate_set.candidates
    if not candidates:
        return
    resource_ids = sorted({resource_id for candidate in candidates for resource_id in (candidate.lecturer_ids if lecturer else candidate.room_ids)})
    if len(resource_ids) < 2:
        return  # Every generated transition is necessarily unchanged.
    resource_index = {resource_id: index + 1 for index, resource_id in enumerate(resource_ids)}
    by_date: dict[date, list[TemporalCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_date[candidate.date].append(candidate)
    previous_seen = None
    previous_value = None
    changes = variables.lecturer_changes if lecturer else variables.room_changes
    assignments = variables.lecturer if lecturer else variables.room
    for date_index, (session_date, date_candidates) in enumerate(sorted(by_date.items())):
        if control is not None:
            control.check()
        has_session = model.new_bool_var(f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_has_{date_index}")
        temporal_vars = [variables.temporal[item.candidate_id] for item in date_candidates]
        model.add(has_session == sum(temporal_vars))
        current_value = model.new_int_var(0, len(resource_ids), f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_value_{date_index}")
        resource_terms = []
        for candidate in date_candidates:
            for resource_id in (candidate.lecturer_ids if lecturer else candidate.room_ids):
                resource_terms.append(resource_index[resource_id] * assignments[(candidate.candidate_id, resource_id)])
        model.add(current_value == sum(resource_terms))
        seen = model.new_bool_var(f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_seen_{date_index}")
        last_value = model.new_int_var(0, len(resource_ids), f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_last_{date_index}")
        if previous_seen is None:
            model.add(seen == has_session)
            model.add(last_value == current_value)
        else:
            model.add(seen >= previous_seen)
            model.add(seen >= has_session)
            model.add(seen <= previous_seen + has_session)
            model.add(last_value == current_value).only_enforce_if(has_session)
            model.add(last_value == previous_value).only_enforce_if(has_session.Not())
            change = model.new_bool_var(f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_change_{date_index}")
            model.add(change <= has_session)
            model.add(change <= previous_seen)
            model.add(current_value != previous_value).only_enforce_if([has_session, previous_seen, change])
            model.add(current_value == previous_value).only_enforce_if([has_session, previous_seen, change.Not()])
            changes.append(change)
        previous_seen = seen
        previous_value = last_value


def _count_current_changes(sessions: Sequence[CurrentSession], field_name: str) -> int:
    ordered = sorted(sessions, key=lambda item: (item.date, item.start_time))
    return sum(getattr(first, field_name) != getattr(second, field_name) for first, second in zip(ordered, ordered[1:]))


def _count_generated_changes(sessions: Sequence[GeneratedSession], field_name: str) -> int:
    ordered = sorted(sessions, key=lambda item: (item.date, item.start_time))
    return sum(getattr(first, field_name) != getattr(second, field_name) for first, second in zip(ordered, ordered[1:]))


def _deduplicate_evidence(items: Sequence[BlockingEvidence]) -> list[BlockingEvidence]:
    combined: dict[tuple[str, date | None, str | None, int | None], BlockingEvidence] = {}
    for item in items:
        key = (item.code, item.holiday_date, item.source_kind, item.source_id)
        existing = combined.get(key)
        combined[key] = BlockingEvidence(
            item.code,
            item.count + (existing.count if existing else 0),
            item.message,
            item.holiday_date,
            item.holiday_name,
            item.source_kind,
            item.source_id,
        )
    return [
        combined[key]
        for key in sorted(
            combined,
            key=lambda value: (value[0], value[1] or date.min, value[2] or "", value[3] or 0),
        )
    ]
