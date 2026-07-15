from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.models.planning import ResourceUnavailabilityPeriod
from app.schemas.draft_schedule import FailureCode, GenerationFailure
from app.services.resource_rules import ResourceChoice, assign_resource_sequence, resource_is_unavailable


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


@dataclass(frozen=True)
class ScheduleGenerationResult:
    sessions: list[GeneratedSession]
    errors: list[GenerationFailure]

    @property
    def ok(self) -> bool:
        return not self.errors


def session_duration_minutes(units: int) -> int:
    if units <= 0:
        raise ValueError("units must be positive")
    return units * UNIT_MINUTES + max(0, units - 1) * BREAK_MINUTES


def distribute_units(total_units: int, min_units: int, max_units: int) -> list[int] | None:
    if total_units <= 0 or min_units <= 0 or max_units < min_units:
        return None
    if total_units < min_units:
        return None
    units: list[int] = []
    remaining = total_units
    while remaining > max_units:
        units.append(max_units)
        remaining -= max_units
    if remaining == 0:
        return units
    if remaining >= min_units:
        units.append(remaining)
        return units
    if not units:
        return None
    needed = min_units - remaining
    previous = units[-1]
    if previous - needed < min_units:
        return None
    units[-1] = previous - needed
    units.append(remaining + needed)
    return units


def generate_schedule(
    course: CoursePlan,
    semester: SemesterPlan,
    planning_period: PlanningPeriodPlan,
    time_windows: list[TimeWindowPlan],
) -> ScheduleGenerationResult:
    errors = _validate_generation_inputs(course, semester, planning_period, time_windows)
    unit_distribution: list[int] | None = None
    if not any(error.code == FailureCode.INVALID_SESSION_PREFERENCE for error in errors):
        unit_distribution = distribute_units(
            course.total_units,
            course.min_session_units,
            course.max_session_units,
        )
        if unit_distribution is None:
            errors.append(
                GenerationFailure(
                    code=FailureCode.INVALID_SESSION_PREFERENCE,
                    message="Course units cannot be split into valid session sizes.",
                )
            )

    if errors:
        return ScheduleGenerationResult(sessions=[], errors=errors)

    assert unit_distribution is not None
    ordered_windows = _ordered_windows(time_windows)
    sessions: list[GeneratedSession] = []

    for index, units in enumerate(unit_distribution):
        session = _place_session(
            course=course,
            units=units,
            index=index,
            existing_sessions=sessions,
            planning_period=planning_period,
            ordered_windows=ordered_windows,
        )
        if session is None:
            if not _any_window_can_fit(units, ordered_windows):
                code = FailureCode.NO_FITTING_TIME_WINDOW
                message = "No Study Type Time Window can fit the generated session."
            elif not _any_resource_feasible_slot(course, units, planning_period, ordered_windows):
                code = FailureCode.NO_FEASIBLE_RESOURCE
                message = "No eligible active Lecturer and capacity-sufficient Room are available in the allowed teaching windows."
            else:
                code = FailureCode.INSUFFICIENT_SEMESTER_CAPACITY
                message = "Planning period does not contain enough allowed teaching window capacity."
            return ScheduleGenerationResult(
                sessions=[],
                errors=[GenerationFailure(code=code, message=message)],
            )
        sessions.append(session)

    lecturer_candidates = _lecturer_candidates(course)
    room_candidates = _room_candidates(course)
    lecturer_assignments = assign_resource_sequence(
        [ResourceChoice(item.id, item.normalized_code) for item in lecturer_candidates],
        [_feasible_lecturer_ids(lecturer_candidates, session) for session in sessions],
    )
    room_assignments = assign_resource_sequence(
        [ResourceChoice(item.id, item.normalized_code) for item in room_candidates],
        [_feasible_room_ids(room_candidates, session, course.cohort_size) for session in sessions],
    )
    if lecturer_assignments is None or room_assignments is None:
        return ScheduleGenerationResult(
            sessions=[],
            errors=[GenerationFailure(code=FailureCode.NO_FEASIBLE_RESOURCE, message="No eligible active Lecturer and capacity-sufficient Room are available for every session.")],
        )
    sessions = [
        GeneratedSession(
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
            units=session.units,
            time_window_id=session.time_window_id,
            constraint_window_index=session.constraint_window_index,
            lecturer_id=lecturer_assignments[index],
            room_id=room_assignments[index],
        )
        for index, session in enumerate(sessions)
    ]

    return ScheduleGenerationResult(sessions=sessions, errors=[])


def _validate_generation_inputs(
    course: CoursePlan,
    semester: SemesterPlan,
    planning_period: PlanningPeriodPlan,
    time_windows: list[TimeWindowPlan],
) -> list[GenerationFailure]:
    errors: list[GenerationFailure] = []
    usable_capacity = [
        candidate.capacity
        for candidate in _room_candidates(course)
        if candidate.active and candidate.capacity is not None and candidate.capacity >= course.cohort_size
    ]
    if not usable_capacity:
        capacities = [candidate.capacity or 0 for candidate in _room_candidates(course) if candidate.active]
        best_capacity = max(capacities, default=0)
        errors.append(
            GenerationFailure(
                code=FailureCode.INSUFFICIENT_ROOM_CAPACITY,
                message=(
                    f"Best eligible active Room capacity {best_capacity} is lower than "
                    f"Cohort size {course.cohort_size}."
                ),
            )
        )
    if course.min_session_units <= 0 or course.max_session_units < course.min_session_units:
        errors.append(
            GenerationFailure(
                code=FailureCode.INVALID_SESSION_PREFERENCE,
                message="Session preference must have a positive minimum not greater than maximum.",
            )
        )
    if planning_period.start_date > planning_period.end_date:
        errors.append(
            GenerationFailure(
                code=FailureCode.INVALID_PLANNING_PERIOD,
                message="Planning period start date must not be after the end date.",
            )
        )
    elif planning_period.start_date < semester.start_date or planning_period.end_date > semester.end_date:
        errors.append(
            GenerationFailure(
                code=FailureCode.INVALID_PLANNING_PERIOD,
                message="Planning period must stay within the selected semester dates.",
            )
        )
    if not time_windows:
        errors.append(
            GenerationFailure(
                code=FailureCode.MISSING_TEACHING_WINDOW,
                message="At least one allowed teaching window is required.",
            )
        )
    for window in time_windows:
        if window.weekday < 0 or window.weekday > 6 or window.start_time >= window.end_time:
            errors.append(
                GenerationFailure(
                    code=FailureCode.INVALID_TEACHING_WINDOW,
                    message="Allowed teaching windows require weekday 0-6 and start time before end time.",
                )
            )
            break
    return errors


def _ordered_windows(windows: list[TimeWindowPlan]) -> list[TimeWindowPlan]:
    return sorted(
        windows,
        key=lambda window: (window.sort_order, window.weekday, window.start_time),
    )


def _place_session(
    course: CoursePlan,
    units: int,
    index: int,
    existing_sessions: list[GeneratedSession],
    planning_period: PlanningPeriodPlan,
    ordered_windows: list[TimeWindowPlan],
) -> GeneratedSession | None:
    start_week = planning_period.start_date + timedelta(weeks=index)
    used_dates = {session.date for session in existing_sessions}

    session = _find_session_on_dates(
        units=units,
        candidate_dates=_candidate_dates(start_week, planning_period.end_date),
        used_dates=used_dates,
        planning_period=planning_period,
        ordered_windows=ordered_windows,
        course=course,
    )
    if session is not None:
        return session
    return _find_session_on_dates(
        units=units,
        candidate_dates=_candidate_dates(planning_period.start_date, planning_period.end_date),
        used_dates=used_dates,
        planning_period=planning_period,
        ordered_windows=ordered_windows,
        course=course,
    )


def _find_session_on_dates(
    units: int,
    candidate_dates: list[date],
    used_dates: set[date],
    planning_period: PlanningPeriodPlan,
    ordered_windows: list[TimeWindowPlan],
    course: CoursePlan,
) -> GeneratedSession | None:
    for candidate_date in candidate_dates:
        if candidate_date < planning_period.start_date or candidate_date > planning_period.end_date:
            continue
        if candidate_date in used_dates:
            continue
        for window in ordered_windows:
            if candidate_date.weekday() != window.weekday:
                continue
            end_time = _session_end_time(window.start_time, units)
            if end_time <= window.end_time:
                proposed = GeneratedSession(
                    date=candidate_date,
                    start_time=window.start_time,
                    end_time=end_time,
                    units=units,
                    time_window_id=window.id,
                    constraint_window_index=window.constraint_window_index,
                )
                if (
                    _feasible_lecturer_ids(_lecturer_candidates(course), proposed)
                    and _feasible_room_ids(_room_candidates(course), proposed, course.cohort_size)
                ):
                    return proposed
    return None


def _lecturer_candidates(course: CoursePlan) -> tuple[ResourceCandidatePlan, ...]:
    return course.lecturer_candidates or (
        ResourceCandidatePlan(id=course.lecturer_id, normalized_code=f"lecturer-{course.lecturer_id}"),
    )


def _room_candidates(course: CoursePlan) -> tuple[ResourceCandidatePlan, ...]:
    return course.room_candidates or (
        ResourceCandidatePlan(
            id=course.room_id,
            normalized_code=f"room-{course.room_id}",
            capacity=course.room_capacity,
        ),
    )


def _feasible_lecturer_ids(
    candidates: tuple[ResourceCandidatePlan, ...],
    session: GeneratedSession,
) -> set[int]:
    return {
        candidate.id
        for candidate in candidates
        if candidate.active
        and not resource_is_unavailable(
            list(candidate.unavailable_periods),
            session.date,
            session.start_time,
            session.end_time,
        )
    }


def _feasible_room_ids(
    candidates: tuple[ResourceCandidatePlan, ...],
    session: GeneratedSession,
    cohort_size: int,
) -> set[int]:
    return {
        candidate.id
        for candidate in candidates
        if candidate.active
        and candidate.capacity is not None
        and candidate.capacity >= cohort_size
        and not resource_is_unavailable(
            list(candidate.unavailable_periods),
            session.date,
            session.start_time,
            session.end_time,
        )
    }


def _candidate_dates(start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days
    if days < 0:
        return []
    return [start_date + timedelta(days=offset) for offset in range(days + 1)]


def _session_end_time(start_time: time, units: int) -> time:
    anchor = datetime.combine(date(2000, 1, 1), start_time)
    return (anchor + timedelta(minutes=session_duration_minutes(units))).time()


def _any_window_can_fit(units: int, windows: list[TimeWindowPlan]) -> bool:
    duration = session_duration_minutes(units)
    for window in windows:
        start = datetime.combine(date(2000, 1, 1), window.start_time)
        end = datetime.combine(date(2000, 1, 1), window.end_time)
        if start + timedelta(minutes=duration) <= end:
            return True
    return False


def _any_resource_feasible_slot(
    course: CoursePlan,
    units: int,
    planning_period: PlanningPeriodPlan,
    windows: list[TimeWindowPlan],
) -> bool:
    for candidate_date in _candidate_dates(planning_period.start_date, planning_period.end_date):
        for window in windows:
            if candidate_date.weekday() != window.weekday:
                continue
            end_time = _session_end_time(window.start_time, units)
            if end_time > window.end_time:
                continue
            proposed = GeneratedSession(
                date=candidate_date,
                start_time=window.start_time,
                end_time=end_time,
                units=units,
                time_window_id=window.id,
                constraint_window_index=window.constraint_window_index,
            )
            if (
                _feasible_lecturer_ids(_lecturer_candidates(course), proposed)
                and _feasible_room_ids(_room_candidates(course), proposed, course.cohort_size)
            ):
                return True
    return False
