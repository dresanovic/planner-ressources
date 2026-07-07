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
class TimeWindowPlan:
    id: int
    weekday: int
    start_time: time
    end_time: time
    sort_order: int = 0


@dataclass(frozen=True)
class GeneratedSession:
    date: date
    start_time: time
    end_time: time
    units: int
    time_window_id: int


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
    time_windows: list[TimeWindowPlan],
    selected_time_window_id: int,
) -> ScheduleGenerationResult:
    errors = _validate_generation_inputs(course, time_windows, selected_time_window_id)
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
    ordered_windows = _ordered_windows(time_windows, selected_time_window_id)
    sessions: list[GeneratedSession] = []

    for index, units in enumerate(unit_distribution):
        session = _place_session(
            units=units,
            index=index,
            existing_sessions=sessions,
            semester=semester,
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
                else "Semester does not contain enough Study Type Time Window capacity."
            )
            return ScheduleGenerationResult(
                sessions=[],
                errors=[GenerationFailure(code=code, message=message)],
            )
        sessions.append(session)

    return ScheduleGenerationResult(sessions=sessions, errors=[])


def _validate_generation_inputs(
    course: CoursePlan,
    time_windows: list[TimeWindowPlan],
    selected_time_window_id: int,
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
    if selected_time_window_id not in {window.id for window in time_windows}:
        errors.append(
            GenerationFailure(
                code=FailureCode.NO_FITTING_TIME_WINDOW,
                message="Selected Study Type Time Window is not available for this study type.",
            )
        )
    return errors


def _ordered_windows(
    windows: list[TimeWindowPlan],
    selected_time_window_id: int,
) -> list[TimeWindowPlan]:
    selected = [window for window in windows if window.id == selected_time_window_id]
    others = sorted(
        [window for window in windows if window.id != selected_time_window_id],
        key=lambda window: (window.sort_order, window.weekday, window.start_time),
    )
    return selected + others


def _place_session(
    units: int,
    index: int,
    existing_sessions: list[GeneratedSession],
    semester: SemesterPlan,
    ordered_windows: list[TimeWindowPlan],
) -> GeneratedSession | None:
    start_week = semester.start_date + timedelta(weeks=index)
    used_dates = {session.date for session in existing_sessions}

    session = _find_session_on_dates(
        units=units,
        candidate_dates=_candidate_dates(start_week, semester.end_date),
        used_dates=used_dates,
        semester=semester,
        ordered_windows=ordered_windows,
    )
    if session is not None:
        return session
    return _find_session_on_dates(
        units=units,
        candidate_dates=_candidate_dates(semester.start_date, semester.end_date),
        used_dates=used_dates,
        semester=semester,
        ordered_windows=ordered_windows,
    )


def _find_session_on_dates(
    units: int,
    candidate_dates: list[date],
    used_dates: set[date],
    semester: SemesterPlan,
    ordered_windows: list[TimeWindowPlan],
) -> GeneratedSession | None:
    for candidate_date in candidate_dates:
        if candidate_date < semester.start_date or candidate_date > semester.end_date:
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
