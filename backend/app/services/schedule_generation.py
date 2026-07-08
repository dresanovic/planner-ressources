from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.schemas.draft_schedule import FailureCode, GenerationFailure


UNIT_MINUTES = 45
BREAK_MINUTES = 10


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
            units=units,
            index=index,
            existing_sessions=sessions,
            planning_period=planning_period,
            ordered_windows=ordered_windows,
        )
        if session is None:
            code = (
                FailureCode.NO_FITTING_TIME_WINDOW
                if not _any_window_can_fit(units, ordered_windows)
                else FailureCode.INSUFFICIENT_SEMESTER_CAPACITY
            )
            message = (
                "No Study Type Time Window can fit the generated session."
                if code == FailureCode.NO_FITTING_TIME_WINDOW
                else "Planning period does not contain enough allowed teaching window capacity."
            )
            return ScheduleGenerationResult(
                sessions=[],
                errors=[GenerationFailure(code=code, message=message)],
            )
        sessions.append(session)

    return ScheduleGenerationResult(sessions=sessions, errors=[])


def _validate_generation_inputs(
    course: CoursePlan,
    semester: SemesterPlan,
    planning_period: PlanningPeriodPlan,
    time_windows: list[TimeWindowPlan],
) -> list[GenerationFailure]:
    errors: list[GenerationFailure] = []
    if course.room_capacity < course.cohort_size:
        errors.append(
            GenerationFailure(
                code=FailureCode.INSUFFICIENT_ROOM_CAPACITY,
                message=(
                    f"Room capacity {course.room_capacity} is lower than "
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
    )
    if session is not None:
        return session
    return _find_session_on_dates(
        units=units,
        candidate_dates=_candidate_dates(planning_period.start_date, planning_period.end_date),
        used_dates=used_dates,
        planning_period=planning_period,
        ordered_windows=ordered_windows,
    )


def _find_session_on_dates(
    units: int,
    candidate_dates: list[date],
    used_dates: set[date],
    planning_period: PlanningPeriodPlan,
    ordered_windows: list[TimeWindowPlan],
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
                return GeneratedSession(
                    date=candidate_date,
                    start_time=window.start_time,
                    end_time=end_time,
                    units=units,
                    time_window_id=window.id,
                    constraint_window_index=window.constraint_window_index,
                )
    return None


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
