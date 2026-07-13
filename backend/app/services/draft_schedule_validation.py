from dataclasses import dataclass, field
from datetime import date, time
from enum import StrEnum

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
    if (
        session.date < constraints.planning_period.start_date
        or session.date > constraints.planning_period.end_date
        or not _fits_any_window(session.date, session.start_time, session.end_time, constraints.allowed_windows)
    ):
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION,
                message="Session is outside the currently active generation constraints.",
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
                message="Session is outside the Study Type Time Window.",
            )
        )


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
