from dataclasses import dataclass, field
from datetime import date, time
from enum import StrEnum
from calendar import day_name

from app.models.planning import DraftSchedule, DraftSession, Room
from app.services.draft_schedule_repository import GenerationConstraints
from app.services.schedule_generation import TimeWindowPlan


class ValidationAlertCode(StrEnum):
    LECTURER_OVERLAP = "LECTURER_OVERLAP"
    ROOM_OVERLAP = "ROOM_OVERLAP"
    COHORT_OVERLAP = "COHORT_OVERLAP"
    ROOM_CAPACITY = "ROOM_CAPACITY"
    GENERATION_CONSTRAINT_VIOLATION = "GENERATION_CONSTRAINT_VIOLATION"
    STUDY_TYPE_WINDOW_VIOLATION = "STUDY_TYPE_WINDOW_VIOLATION"
    VALIDATION_DATA_MISSING = "VALIDATION_DATA_MISSING"


@dataclass(frozen=True)
class RelatedSession:
    session_id: int
    draft_schedule_id: int
    course_id: int
    course_name: str
    date: date
    start_time: str
    end_time: str
    cohort_name: str
    lecturer_name: str
    room_name: str


@dataclass(frozen=True)
class ValidationAlert:
    code: ValidationAlertCode
    message: str
    related_sessions: list[RelatedSession] = field(default_factory=list)


def collect_validation_alerts(
    drafts: list[DraftSchedule],
    *,
    rooms_by_id: dict[int, Room],
    constraints_by_course_id: dict[int, GenerationConstraints],
    study_windows_by_study_type_id: dict[int, list[TimeWindowPlan]],
) -> dict[int, list[ValidationAlert]]:
    alerts: dict[int, list[ValidationAlert]] = {
        session.id: [] for draft in drafts for session in draft.sessions
    }
    sessions = [(draft, session) for draft in drafts for session in draft.sessions]

    for code, attr, label in [
        (ValidationAlertCode.LECTURER_OVERLAP, "lecturer_id", "lecturer"),
        (ValidationAlertCode.ROOM_OVERLAP, "room_id", "room"),
        (ValidationAlertCode.COHORT_OVERLAP, "cohort_id", "Cohort"),
    ]:
        _add_overlap_alerts(alerts, sessions, code=code, attr=attr, label=label, rooms_by_id=rooms_by_id)

    for draft, session in sessions:
        _add_capacity_alert(alerts, draft, session, rooms_by_id)
        _add_generation_constraint_alert(alerts, draft, session, constraints_by_course_id)
        _add_study_type_window_alert(
            alerts,
            draft,
            session,
            study_windows_by_study_type_id,
            constraints_by_course_id,
        )

    return alerts


def sessions_overlap(left: DraftSession, right: DraftSession) -> bool:
    return (
        left.id != right.id
        and left.date == right.date
        and left.start_time < right.end_time
        and left.end_time > right.start_time
    )


def _add_overlap_alerts(
    alerts: dict[int, list[ValidationAlert]],
    sessions: list[tuple[DraftSchedule, DraftSession]],
    *,
    code: ValidationAlertCode,
    attr: str,
    label: str,
    rooms_by_id: dict[int, Room],
) -> None:
    for draft, session in sessions:
        related = [
            _related_session(other_draft, other_session, rooms_by_id)
            for other_draft, other_session in sessions
            if getattr(session, attr) == getattr(other_session, attr)
            and sessions_overlap(session, other_session)
        ]
        if related:
            alerts[session.id].append(
                ValidationAlert(
                    code=code,
                    message=f"{label} overlaps with {len(related)} session(s).",
                    related_sessions=related,
                )
            )


def _add_capacity_alert(
    alerts: dict[int, list[ValidationAlert]],
    draft: DraftSchedule,
    session: DraftSession,
    rooms_by_id: dict[int, Room],
) -> None:
    room = rooms_by_id.get(session.room_id)
    cohort = draft.course.cohort
    if room is None or cohort is None:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                message="Required room or Cohort data is missing for validation.",
            )
        )
        return
    if room.capacity < cohort.student_count:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.ROOM_CAPACITY,
                message=f"Room capacity {room.capacity} is lower than Cohort size {cohort.student_count}.",
            )
        )


def _add_generation_constraint_alert(
    alerts: dict[int, list[ValidationAlert]],
    draft: DraftSchedule,
    session: DraftSession,
    constraints_by_course_id: dict[int, GenerationConstraints],
) -> None:
    constraints = constraints_by_course_id.get(draft.course_id)
    if constraints is None:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                message="Active generation constraints are missing for validation.",
            )
        )
        return
    reasons = _generation_constraint_violation_reasons(session, constraints)
    if reasons:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION,
                message=f"Generation constraint mismatch: {' '.join(reasons)}",
            )
        )


def _add_study_type_window_alert(
    alerts: dict[int, list[ValidationAlert]],
    draft: DraftSchedule,
    session: DraftSession,
    study_windows_by_study_type_id: dict[int, list[TimeWindowPlan]],
    constraints_by_course_id: dict[int, GenerationConstraints],
) -> None:
    constraints = constraints_by_course_id.get(draft.course_id)
    if constraints is not None and constraints.is_custom:
        return

    windows = study_windows_by_study_type_id.get(draft.course.study_type_id)
    if not windows:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                message="Study Type Time Window data is missing for validation.",
            )
        )
        return
    if not _fits_any_window(session.date, session.start_time, session.end_time, windows):
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION,
                message=(
                    "Study Type window mismatch: "
                    f"{_teaching_window_violation_reason(session, windows)}"
                ),
            )
        )


def _generation_constraint_violation_reasons(
    session: DraftSession,
    constraints: GenerationConstraints,
) -> list[str]:
    reasons: list[str] = []
    period = constraints.planning_period
    if session.date < period.start_date:
        reasons.append(
            f"Session date {session.date.isoformat()} is before the allowed planning period "
            f"{period.start_date.isoformat()}–{period.end_date.isoformat()}."
        )
    elif session.date > period.end_date:
        reasons.append(
            f"Session date {session.date.isoformat()} is after the allowed planning period "
            f"{period.start_date.isoformat()}–{period.end_date.isoformat()}."
        )
    if not _fits_any_window(
        session.date,
        session.start_time,
        session.end_time,
        constraints.allowed_windows,
    ):
        reasons.append(_teaching_window_violation_reason(session, constraints.allowed_windows))
    return reasons


def _teaching_window_violation_reason(
    session: DraftSession,
    windows: list[TimeWindowPlan],
) -> str:
    if not windows:
        return "No allowed teaching windows are configured."

    weekday = session.date.weekday()
    weekday_label = day_name[weekday]
    windows_for_day = sorted(
        (window for window in windows if window.weekday == weekday),
        key=lambda window: (window.start_time, window.end_time),
    )
    if not windows_for_day:
        return (
            f"{weekday_label} is not an allowed teaching day. "
            f"Allowed teaching windows: {_format_windows(windows)}."
        )

    actual_time = f"{_format_time(session.start_time)}–{_format_time(session.end_time)}"
    allowed_times = ", ".join(
        f"{_format_time(window.start_time)}–{_format_time(window.end_time)}"
        for window in windows_for_day
    )
    return (
        f"Session time {actual_time} on {weekday_label} is outside the allowed time. "
        f"Allowed on {weekday_label}: {allowed_times}."
    )


def _format_windows(windows: list[TimeWindowPlan]) -> str:
    ordered = sorted(
        windows,
        key=lambda window: (window.weekday, window.start_time, window.end_time),
    )
    return ", ".join(
        f"{day_name[window.weekday]} "
        f"{_format_time(window.start_time)}–{_format_time(window.end_time)}"
        for window in ordered
    )


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _fits_any_window(
    session_date: date,
    start_time: time,
    end_time: time,
    windows: list[TimeWindowPlan],
) -> bool:
    weekday = session_date.weekday()
    return any(
        window.weekday == weekday
        and start_time >= window.start_time
        and end_time <= window.end_time
        for window in windows
    )


def _related_session(
    draft: DraftSchedule,
    session: DraftSession,
    rooms_by_id: dict[int, Room],
) -> RelatedSession:
    course = draft.course
    room = rooms_by_id.get(session.room_id)
    return RelatedSession(
        session_id=session.id,
        draft_schedule_id=draft.id,
        course_id=draft.course_id,
        course_name=course.name,
        date=session.date,
        start_time=session.start_time.strftime("%H:%M"),
        end_time=session.end_time.strftime("%H:%M"),
        cohort_name=course.cohort.name,
        lecturer_name=course.lecturer.name,
        room_name=room.name if room is not None else f"Room {session.room_id}",
    )
