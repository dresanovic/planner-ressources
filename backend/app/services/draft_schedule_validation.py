from dataclasses import dataclass, field
from datetime import date, time
from enum import StrEnum
from calendar import day_name

from app.models.planning import DraftSchedule, DraftSession, Lecturer, ResourceUnavailabilityPeriod, Room
from app.services.resource_rules import resource_is_unavailable
from app.services.draft_schedule_repository import GenerationConstraints
from app.services.holiday_calendar import HolidayReference
from app.services.schedule_generation import TimeWindowPlan


class ValidationAlertCode(StrEnum):
    LECTURER_OVERLAP = "LECTURER_OVERLAP"
    ROOM_OVERLAP = "ROOM_OVERLAP"
    COHORT_OVERLAP = "COHORT_OVERLAP"
    ROOM_CAPACITY = "ROOM_CAPACITY"
    GENERATION_CONSTRAINT_VIOLATION = "GENERATION_CONSTRAINT_VIOLATION"
    STUDY_TYPE_WINDOW_VIOLATION = "STUDY_TYPE_WINDOW_VIOLATION"
    VALIDATION_DATA_MISSING = "VALIDATION_DATA_MISSING"
    LECTURER_UNAVAILABLE = "LECTURER_UNAVAILABLE"
    ROOM_UNAVAILABLE = "ROOM_UNAVAILABLE"
    LECTURER_INELIGIBLE = "LECTURER_INELIGIBLE"
    ROOM_INELIGIBLE = "ROOM_INELIGIBLE"
    INSTITUTION_HOLIDAY = "INSTITUTION_HOLIDAY"


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
    holiday_date: date | None = None
    holiday_name: str | None = None


@dataclass(frozen=True)
class ValidationOccurrenceRecord:
    occurrence_ref: str
    course_ref: str
    date: date
    start_time: time
    end_time: time
    lecturer_refs: tuple[str, ...]
    room_ref: str
    cohort_ref: str
    required_capacity: int


@dataclass(frozen=True)
class EvaluatedValidationFinding:
    category: str
    occurrence_refs: tuple[str, ...]
    subject_ref: str | None = None
    required_capacity: int | None = None
    room_ref: str | None = None
    current_capacity: int | None = None
    holiday_date: date | None = None
    holiday_name: str | None = None
    issue_code: str | None = None


@dataclass(frozen=True)
class TeachingConstraintEvaluation:
    generation_reasons: tuple[str, ...]
    study_type_issue_code: str | None

    @property
    def issue_codes(self) -> tuple[str, ...]:
        codes: list[str] = []
        if self.generation_reasons:
            codes.append(
                ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION.value
            )
        if self.study_type_issue_code is not None:
            codes.append(self.study_type_issue_code)
        return tuple(codes)


def evaluate_occurrence_records(
    occurrences: list[ValidationOccurrenceRecord],
    *,
    room_capacities: dict[str, int],
    holidays_by_date: dict[date, HolidayReference] | None,
    eligible_lecturer_refs_by_course: dict[str, set[str]] | None = None,
    eligible_room_refs_by_course: dict[str, set[str]] | None = None,
    active_lecturer_refs: set[str] | None = None,
    active_room_refs: set[str] | None = None,
    unavailable_lecturer_refs_by_occurrence: dict[str, set[str]] | None = None,
    unavailable_room_refs_by_occurrence: dict[str, set[str]] | None = None,
) -> list[EvaluatedValidationFinding]:
    """Evaluate common current facts without depending on ORM or snapshot shape."""
    findings: list[EvaluatedValidationFinding] = []
    unavailable_lecturer_refs_by_occurrence = (
        unavailable_lecturer_refs_by_occurrence or {}
    )
    unavailable_room_refs_by_occurrence = unavailable_room_refs_by_occurrence or {}
    for index, left in enumerate(occurrences):
        for right in occurrences[index + 1 :]:
            if not _record_overlap(left, right):
                continue
            shared = (
                ("lecturer_conflict", set(left.lecturer_refs) & set(right.lecturer_refs)),
                (
                    "room_conflict",
                    {left.room_ref} if left.room_ref == right.room_ref else set(),
                ),
                (
                    "cohort_conflict",
                    {left.cohort_ref}
                    if left.cohort_ref == right.cohort_ref
                    else set(),
                ),
            )
            for category, subjects in shared:
                for subject in sorted(subjects):
                    findings.append(
                        EvaluatedValidationFinding(
                            category=category,
                            occurrence_refs=tuple(
                                sorted((left.occurrence_ref, right.occurrence_ref))
                            ),
                            subject_ref=subject,
                        )
                    )
    for occurrence in occurrences:
        eligible_lecturers = (
            eligible_lecturer_refs_by_course or {}
        ).get(occurrence.course_ref)
        for lecturer_ref in occurrence.lecturer_refs:
            if (
                eligible_lecturers is not None
                and (
                    lecturer_ref not in eligible_lecturers
                    or (
                        active_lecturer_refs is not None
                        and lecturer_ref not in active_lecturer_refs
                    )
                )
            ):
                findings.append(
                    EvaluatedValidationFinding(
                        category="other",
                        occurrence_refs=(occurrence.occurrence_ref,),
                        subject_ref=lecturer_ref,
                        issue_code="LECTURER_INELIGIBLE",
                    )
                )
            if lecturer_ref in unavailable_lecturer_refs_by_occurrence.get(
                occurrence.occurrence_ref, set()
            ):
                findings.append(
                    EvaluatedValidationFinding(
                        category="other",
                        occurrence_refs=(occurrence.occurrence_ref,),
                        subject_ref=lecturer_ref,
                        issue_code="LECTURER_UNAVAILABLE",
                    )
                )
        eligible_rooms = (eligible_room_refs_by_course or {}).get(
            occurrence.course_ref
        )
        if (
            eligible_rooms is not None
            and (
                occurrence.room_ref not in eligible_rooms
                or (
                    active_room_refs is not None
                    and occurrence.room_ref not in active_room_refs
                )
            )
        ):
            findings.append(
                EvaluatedValidationFinding(
                    category="other",
                    occurrence_refs=(occurrence.occurrence_ref,),
                    subject_ref=occurrence.room_ref,
                    room_ref=occurrence.room_ref,
                    issue_code="ROOM_INELIGIBLE",
                )
            )
        if occurrence.room_ref in unavailable_room_refs_by_occurrence.get(
            occurrence.occurrence_ref, set()
        ):
            findings.append(
                EvaluatedValidationFinding(
                    category="other",
                    occurrence_refs=(occurrence.occurrence_ref,),
                    subject_ref=occurrence.room_ref,
                    room_ref=occurrence.room_ref,
                    issue_code="ROOM_UNAVAILABLE",
                )
            )
        capacity = room_capacities.get(occurrence.room_ref)
        if capacity is None:
            findings.append(
                EvaluatedValidationFinding(
                    category="other",
                    occurrence_refs=(occurrence.occurrence_ref,),
                    room_ref=occurrence.room_ref,
                    issue_code="VALIDATION_DATA_MISSING",
                )
            )
        elif capacity < occurrence.required_capacity:
            findings.append(
                EvaluatedValidationFinding(
                    category="room_capacity",
                    occurrence_refs=(occurrence.occurrence_ref,),
                    required_capacity=occurrence.required_capacity,
                    room_ref=occurrence.room_ref,
                    current_capacity=capacity,
                )
            )
        if holidays_by_date is None:
            findings.append(
                EvaluatedValidationFinding(
                    category="other",
                    occurrence_refs=(occurrence.occurrence_ref,),
                    issue_code="HOLIDAY_DATA_MISSING",
                )
            )
        elif occurrence.date in holidays_by_date:
            holiday = holidays_by_date[occurrence.date]
            findings.append(
                EvaluatedValidationFinding(
                    category="holiday",
                    occurrence_refs=(occurrence.occurrence_ref,),
                    holiday_date=holiday.date,
                    holiday_name=holiday.name,
                )
            )
    return findings


def collect_validation_alerts(
    drafts: list[DraftSchedule],
    *,
    rooms_by_id: dict[int, Room],
    lecturers_by_id: dict[int, Lecturer] | None = None,
    constraints_by_course_id: dict[int, GenerationConstraints],
    study_windows_by_study_type_id: dict[int, list[TimeWindowPlan]],
    unavailability_by_resource: dict[tuple[str, int], list[ResourceUnavailabilityPeriod]] | None = None,
    eligible_lecturer_ids_by_course: dict[int, set[int]] | None = None,
    eligible_room_ids_by_course: dict[int, set[int]] | None = None,
    active_lecturer_ids: set[int] | None = None,
    active_room_ids: set[int] | None = None,
    current_cohort_sizes_by_course: dict[int, int] | None = None,
    holidays_by_date: dict[date, HolidayReference] | None = {},
) -> dict[int, list[ValidationAlert]]:
    alerts: dict[int, list[ValidationAlert]] = {
        session.id: [] for draft in drafts for session in draft.sessions
    }
    sessions = [(draft, session) for draft in drafts for session in draft.sessions]
    unavailability_by_resource = unavailability_by_resource or {}
    eligible_lecturer_ids_by_course = eligible_lecturer_ids_by_course or {}
    eligible_room_ids_by_course = eligible_room_ids_by_course or {}
    lecturers_by_id = lecturers_by_id or {}
    current_cohort_sizes_by_course = current_cohort_sizes_by_course or {}

    session_by_ref = {
        str(session.id): (draft, session) for draft, session in sessions
    }
    common_findings = evaluate_occurrence_records(
        [
            ValidationOccurrenceRecord(
                occurrence_ref=str(session.id),
                course_ref=str(draft.course_id),
                date=session.date,
                start_time=session.start_time,
                end_time=session.end_time,
                lecturer_refs=(str(session.lecturer_id),),
                room_ref=str(session.room_id),
                cohort_ref=str(session.cohort_id),
                required_capacity=current_cohort_sizes_by_course.get(
                    draft.course_id, draft.cohort_size_snapshot
                ),
            )
            for draft, session in sessions
        ],
        room_capacities={
            str(room_id): room.capacity for room_id, room in rooms_by_id.items()
        },
        holidays_by_date=holidays_by_date,
        eligible_lecturer_refs_by_course={
            str(course_id): {str(item) for item in lecturer_ids}
            for course_id, lecturer_ids in eligible_lecturer_ids_by_course.items()
        }
        if eligible_lecturer_ids_by_course
        else None,
        eligible_room_refs_by_course={
            str(course_id): {str(item) for item in room_ids}
            for course_id, room_ids in eligible_room_ids_by_course.items()
        }
        if eligible_room_ids_by_course
        else None,
        active_lecturer_refs={str(item) for item in active_lecturer_ids}
        if active_lecturer_ids is not None
        else None,
        active_room_refs={str(item) for item in active_room_ids}
        if active_room_ids is not None
        else None,
        unavailable_lecturer_refs_by_occurrence={
            str(session.id): {
                str(session.lecturer_id)
                for period in unavailability_by_resource.get(
                    ("lecturer", session.lecturer_id), []
                )
                if resource_is_unavailable(
                    [period],
                    session.date,
                    session.start_time,
                    session.end_time,
                )
            }
            for _draft, session in sessions
        },
        unavailable_room_refs_by_occurrence={
            str(session.id): {
                str(session.room_id)
                for period in unavailability_by_resource.get(
                    ("room", session.room_id), []
                )
                if resource_is_unavailable(
                    [period],
                    session.date,
                    session.start_time,
                    session.end_time,
                )
            }
            for _draft, session in sessions
        },
    )
    conflict_groups: dict[tuple[str, str], set[str]] = {}
    for finding in common_findings:
        if finding.category.endswith("_conflict"):
            for occurrence_ref in finding.occurrence_refs:
                conflict_groups.setdefault(
                    (finding.category, occurrence_ref), set()
                ).update(
                    ref for ref in finding.occurrence_refs if ref != occurrence_ref
                )
            continue
        occurrence_ref = finding.occurrence_refs[0]
        _draft, session = session_by_ref[occurrence_ref]
        if finding.category == "room_capacity":
            alerts[session.id].append(
                ValidationAlert(
                    code=ValidationAlertCode.ROOM_CAPACITY,
                    message=(
                        f"Room capacity {finding.current_capacity} is lower than "
                        f"Cohort size {finding.required_capacity}."
                    ),
                )
            )
        elif finding.category == "holiday":
            alerts[session.id].append(
                ValidationAlert(
                    code=ValidationAlertCode.INSTITUTION_HOLIDAY,
                    message=(
                        f"{finding.holiday_name} on "
                        f"{finding.holiday_date.isoformat()} is an institution holiday."
                    ),
                    holiday_date=finding.holiday_date,
                    holiday_name=finding.holiday_name,
                )
            )
        elif finding.issue_code == "VALIDATION_DATA_MISSING":
            alerts[session.id].append(
                ValidationAlert(
                    code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                    message="Required room or Cohort data is missing for validation.",
                )
            )
        elif finding.issue_code == "HOLIDAY_DATA_MISSING":
            alerts[session.id].append(
                ValidationAlert(
                    code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                    message="Institution holiday data is unavailable for validation.",
                )
            )
        elif finding.issue_code is not None:
            code, message = {
                "LECTURER_INELIGIBLE": (
                    ValidationAlertCode.LECTURER_INELIGIBLE,
                    "Assigned Lecturer is inactive or outside the current Course eligibility set.",
                ),
                "ROOM_INELIGIBLE": (
                    ValidationAlertCode.ROOM_INELIGIBLE,
                    "Assigned Room is inactive or outside the current Course eligibility set.",
                ),
                "LECTURER_UNAVAILABLE": (
                    ValidationAlertCode.LECTURER_UNAVAILABLE,
                    "Lecturer is unavailable during this session.",
                ),
                "ROOM_UNAVAILABLE": (
                    ValidationAlertCode.ROOM_UNAVAILABLE,
                    "Room is unavailable during this session.",
                ),
            }[finding.issue_code]
            alerts[session.id].append(ValidationAlert(code=code, message=message))
    conflict_metadata = {
        "lecturer_conflict": ValidationAlertCode.LECTURER_OVERLAP,
        "room_conflict": ValidationAlertCode.ROOM_OVERLAP,
        "cohort_conflict": ValidationAlertCode.COHORT_OVERLAP,
    }
    for (category, occurrence_ref), related_refs in conflict_groups.items():
        draft, session = session_by_ref[occurrence_ref]
        code = conflict_metadata[category]
        related_by_id = {
            related.session_id: related
            for related in (
            _related_session(*session_by_ref[ref], rooms_by_id, lecturers_by_id)
            for ref in sorted(related_refs)
            )
        }
        related = list(related_by_id.values())
        if category == "lecturer_conflict":
            lecturer = lecturers_by_id.get(session.lecturer_id)
            subject = lecturer.name if lecturer is not None else f"Lecturer {session.lecturer_id}"
            message = f'Lecturer "{subject}" overlaps with {len(related)} related session(s).'
        elif category == "room_conflict":
            room = rooms_by_id.get(session.room_id)
            subject = room.name if room is not None else f"Room {session.room_id}"
            message = f'Room "{subject}" overlaps with {len(related)} related session(s).'
        else:
            subject = draft.cohort_name_snapshot or f"Cohort {draft.cohort_id_snapshot}"
            message = f'Cohort "{subject}" overlaps with {len(related)} related session(s).'
        alerts[session.id].append(
            ValidationAlert(
                code=code,
                message=message,
                related_sessions=related,
            )
        )

    for draft, session in sessions:
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


def _record_overlap(
    left: ValidationOccurrenceRecord, right: ValidationOccurrenceRecord
) -> bool:
    return (
        left.occurrence_ref != right.occurrence_ref
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
    lecturers_by_id: dict[int, Lecturer],
) -> None:
    for draft, session in sessions:
        related = [
            _related_session(other_draft, other_session, rooms_by_id, lecturers_by_id)
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
    current_cohort_size: int,
) -> None:
    room = rooms_by_id.get(session.room_id)
    if room is None:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                message="Required room or Cohort data is missing for validation.",
            )
        )
        return
    if room.capacity < current_cohort_size:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.ROOM_CAPACITY,
                message=f"Room capacity {room.capacity} is lower than Cohort size {current_cohort_size}.",
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
    evaluation = evaluate_teaching_constraints(
        session_date=session.date,
        start_time=session.start_time,
        end_time=session.end_time,
        planning_start_date=constraints.planning_period.start_date,
        planning_end_date=constraints.planning_period.end_date,
        allowed_windows=constraints.allowed_windows,
    )
    if evaluation.generation_reasons:
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION,
                message=(
                    "Generation constraint mismatch: "
                    f"{' '.join(evaluation.generation_reasons)}"
                ),
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
    active_study_type_id = (
        constraints.study_type_id
        if constraints is not None
        else draft.study_type_id_snapshot
    )
    windows = study_windows_by_study_type_id.get(active_study_type_id)
    evaluation = evaluate_teaching_constraints(
        session_date=session.date,
        start_time=session.start_time,
        end_time=session.end_time,
        planning_start_date=(
            constraints.planning_period.start_date
            if constraints is not None
            else session.date
        ),
        planning_end_date=(
            constraints.planning_period.end_date
            if constraints is not None
            else session.date
        ),
        allowed_windows=(
            constraints.allowed_windows
            if constraints is not None
            else windows or []
        ),
        study_type_windows=windows or [],
    )
    if (
        evaluation.study_type_issue_code
        == ValidationAlertCode.VALIDATION_DATA_MISSING.value
    ):
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.VALIDATION_DATA_MISSING,
                message="Study Type Time Window data is missing for validation.",
            )
        )
        return
    if (
        evaluation.study_type_issue_code
        == ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION.value
    ):
        alerts[session.id].append(
            ValidationAlert(
                code=ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION,
                message=(
                    "Study Type window mismatch: "
                    f"{_teaching_window_violation_reason(session, windows)}"
                ),
            )
        )


def _planning_period_violation_reasons_for_values(
    *,
    session_date: date,
    planning_start_date: date,
    planning_end_date: date,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if session_date < planning_start_date:
        reasons.append(
            f"Session date {session_date.isoformat()} is before the allowed planning period "
            f"{planning_start_date.isoformat()}–{planning_end_date.isoformat()}."
        )
    elif session_date > planning_end_date:
        reasons.append(
            f"Session date {session_date.isoformat()} is after the allowed planning period "
            f"{planning_start_date.isoformat()}–{planning_end_date.isoformat()}."
        )
    return tuple(reasons)


def _teaching_window_violation_reason(
    session: DraftSession,
    windows: list[TimeWindowPlan],
) -> str:
    return _teaching_window_violation_reason_for_values(
        session_date=session.date,
        start_time=session.start_time,
        end_time=session.end_time,
        windows=windows,
    )


def _teaching_window_violation_reason_for_values(
    *,
    session_date: date,
    start_time: time,
    end_time: time,
    windows: list[TimeWindowPlan],
) -> str:
    if not windows:
        return "No allowed teaching windows are configured."

    weekday = session_date.weekday()
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

    actual_time = f"{_format_time(start_time)}–{_format_time(end_time)}"
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


def fits_any_validation_window(
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


def evaluate_teaching_constraints(
    *,
    session_date: date,
    start_time: time,
    end_time: time,
    planning_start_date: date,
    planning_end_date: date,
    allowed_windows: list[TimeWindowPlan],
    study_type_windows: list[TimeWindowPlan] | None = None,
) -> TeachingConstraintEvaluation:
    """Evaluate established teaching constraints for live or captured facts."""
    generation_reasons = _planning_period_violation_reasons_for_values(
        session_date=session_date,
        planning_start_date=planning_start_date,
        planning_end_date=planning_end_date,
    )
    effective_study_windows = (
        allowed_windows if study_type_windows is None else study_type_windows
    )
    study_type_issue_code = None
    if not effective_study_windows:
        study_type_issue_code = (
            ValidationAlertCode.VALIDATION_DATA_MISSING.value
        )
    elif not fits_any_validation_window(
        session_date,
        start_time,
        end_time,
        effective_study_windows,
    ):
        study_type_issue_code = (
            ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION.value
        )
    return TeachingConstraintEvaluation(
        generation_reasons=generation_reasons,
        study_type_issue_code=study_type_issue_code,
    )


def _related_session(
    draft: DraftSchedule,
    session: DraftSession,
    rooms_by_id: dict[int, Room],
    lecturers_by_id: dict[int, Lecturer],
) -> RelatedSession:
    room = rooms_by_id.get(session.room_id)
    lecturer = lecturers_by_id.get(session.lecturer_id)
    return RelatedSession(
        session_id=session.id,
        draft_schedule_id=draft.id,
        course_id=draft.course_id,
        course_name=draft.course_name_snapshot,
        date=session.date,
        start_time=session.start_time.strftime("%H:%M"),
        end_time=session.end_time.strftime("%H:%M"),
        cohort_name=draft.cohort_name_snapshot,
        lecturer_name=lecturer.name if lecturer is not None else f"Lecturer {session.lecturer_id}",
        room_name=room.name if room is not None else f"Room {session.room_id}",
    )
