import hashlib
import json
from datetime import date, datetime, time, timezone
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Course,
    CourseExamConfiguration,
    DraftSchedule,
    DraftSession,
    ExamSession,
    Lecturer,
    ResourceUnavailabilityPeriod,
    Room,
    ScheduleRevision,
    ScheduleRevisionEvent,
    Semester,
)
from app.services.draft_schedule_repository import (
    load_course_plan,
    load_generation_constraints,
    load_semester_plan,
    load_time_windows,
)
from app.services.draft_schedule_validation import collect_validation_alerts
from app.services.exam_scheduling import _current_validity_issues
from app.services.holiday_calendar import holiday_snapshot


WORKING_STATES = {"draft", "ready_for_review"}


class LifecycleFailure(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        field: str | None = None,
        meta: dict[str, Any] | None = None,
        current_overview: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        self.meta = meta
        self.current_overview = current_overview


class LifecycleConflict(LifecycleFailure):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str | None = None,
        meta: dict[str, Any] | None = None,
        current_overview: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code,
            message,
            status_code=409,
            field=field,
            meta=meta,
            current_overview=current_overview,
        )


def get_lifecycle_overview(db: Session, semester_id: int) -> dict[str, Any]:
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise LifecycleFailure(
            "semester_not_found",
            "The selected semester does not exist.",
            status_code=404,
        )
    revisions = _revisions_for_semester(db, semester_id)
    active = next((row for row in revisions if row.state in WORKING_STATES), None)
    current = next((row for row in revisions if row.state == "published"), None)
    state_token = _state_token(semester_id, revisions)
    return {
        "semesterId": semester.id,
        "semesterName": semester.name,
        "stateToken": state_token,
        "activeWorkingRevision": _summary(active, active, current) if active else None,
        "currentPublication": _summary(current, active, current) if current else None,
        "revisions": [
            _summary(row, active, current)
            for row in sorted(revisions, key=lambda item: item.revision_number, reverse=True)
        ],
        "allowedActions": {"createWorkingRevision": active is None},
    }


def create_working_revision(
    db: Session, semester_id: int, expected_state_token: str
) -> dict[str, Any]:
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise LifecycleFailure(
            "semester_not_found",
            "The selected semester does not exist.",
            status_code=404,
        )
    _claim_semester(db, semester_id)
    overview = get_lifecycle_overview(db, semester_id)
    if overview["stateToken"] != expected_state_token:
        raise LifecycleConflict(
            "stale_lifecycle_state",
            "The semester lifecycle changed. Review the current state and retry.",
            current_overview=overview,
        )
    if overview["activeWorkingRevision"] is not None:
        raise LifecycleConflict(
            "active_working_revision_exists",
            "This semester already has an active working revision.",
            current_overview=overview,
        )
    current = next((row for row in _revisions_for_semester(db, semester_id) if row.state == "published"), None)
    if current is not None:
        _materialize_snapshot(db, semester_id, current.snapshot_document)

    revision = ScheduleRevision(
        semester_id=semester_id,
        revision_number=_next_revision_number(db, semester_id),
        state="draft",
        origin_revision_id=current.id if current else None,
        row_version=1,
    )
    db.add(revision)
    try:
        db.flush()
    except IntegrityError as exc:
        raise LifecycleConflict(
            "active_working_revision_exists",
            "Another request established the semester working revision.",
        ) from exc
    _append_event(db, revision, "created", None, "draft")
    db.flush()
    return get_lifecycle_overview(db, semester_id)


def prepare_publication(
    db: Session,
    revision_id: int,
    expected_revision_version: int,
    expected_state_token: str,
) -> dict[str, Any]:
    revision = _revision_or_404(db, revision_id)
    overview = get_lifecycle_overview(db, revision.semester_id)
    _require_current_expectations(
        revision, overview, expected_revision_version, expected_state_token
    )
    if revision.state not in WORKING_STATES:
        raise LifecycleConflict(
            "revision_not_editable",
            "Only the active Draft or Ready for review revision can be published.",
            current_overview=overview,
        )
    prepared_at = _now()
    snapshot = _build_snapshot(db, revision.semester_id, prepared_at)
    totals = _snapshot_totals(snapshot)
    token = _publication_token(overview["stateToken"], revision, snapshot)
    return {
        "preparationToken": token,
        "preparedAt": _iso(prepared_at),
        "semesterId": overview["semesterId"],
        "semesterName": overview["semesterName"],
        "targetRevision": overview["activeWorkingRevision"],
        "consequence": (
            "replacement_publication"
            if overview["currentPublication"] is not None
            else "first_publication"
        ),
        "currentPublication": overview["currentPublication"],
        **totals,
        "conditions": snapshot["capturedConditions"],
    }


def transition_revision(
    db: Session,
    revision_id: int,
    *,
    action: str,
    expected_revision_version: int,
    expected_state_token: str,
    confirmed: bool,
    publication_token: str | None = None,
) -> dict[str, Any]:
    revision = _revision_or_404(db, revision_id)
    _claim_semester(db, revision.semester_id)
    db.refresh(revision)
    overview = get_lifecycle_overview(db, revision.semester_id)
    _require_current_expectations(
        revision, overview, expected_revision_version, expected_state_token
    )
    if action in {"mark_ready", "return_to_draft"}:
        expected_state = "draft" if action == "mark_ready" else "ready_for_review"
        target_state = "ready_for_review" if action == "mark_ready" else "draft"
        event_type = "marked_ready" if action == "mark_ready" else "returned_to_draft"
        if revision.state != expected_state:
            raise LifecycleConflict("invalid_transition", "The requested lifecycle transition is not available from the current state.", current_overview=overview)
        changed_at = _now()
        revision.state = target_state
        revision.state_changed_at = changed_at
        revision.updated_at = changed_at
        revision.row_version += 1
        _append_event(db, revision, event_type, expected_state, target_state, changed_at)
        db.flush()
        return get_lifecycle_overview(db, revision.semester_id)
    if action == "abandon":
        if revision.state not in WORKING_STATES:
            raise LifecycleConflict("invalid_transition", "Only the active working revision can be abandoned.", current_overview=overview)
        if not confirmed:
            raise LifecycleFailure("confirmation_required", "Explicit abandonment confirmation is required.", status_code=422)
        changed_at = _now()
        snapshot = _build_snapshot(db, revision.semester_id, changed_at)
        from_state = revision.state
        revision.state = "abandoned"
        revision.snapshot_schema_version = 1
        revision.snapshot_document = snapshot
        revision.state_changed_at = changed_at
        revision.updated_at = changed_at
        revision.row_version += 1
        _append_event(db, revision, "abandoned", from_state, "abandoned", changed_at)
        db.flush()
        return get_lifecycle_overview(db, revision.semester_id)
    if action == "restore":
        if revision.state != "abandoned":
            raise LifecycleConflict("invalid_transition", "Only an abandoned revision can be restored.", current_overview=overview)
        if overview["activeWorkingRevision"] is not None:
            raise LifecycleConflict("active_working_revision_exists", "Abandon the active working revision before restoring another revision.", current_overview=overview)
        _materialize_snapshot(db, revision.semester_id, revision.snapshot_document)
        changed_at = _now()
        revision.state = "draft"
        revision.state_changed_at = changed_at
        revision.updated_at = changed_at
        revision.row_version += 1
        _append_event(db, revision, "restored", "abandoned", "draft", changed_at)
        db.flush()
        return get_lifecycle_overview(db, revision.semester_id)
    if action != "publish":
        raise LifecycleConflict("invalid_transition", "The requested lifecycle transition is not available.", current_overview=overview)
    if revision.state not in WORKING_STATES:
        raise LifecycleConflict(
            "revision_not_editable",
            "Published and historical revisions cannot be changed in place.",
            current_overview=overview,
        )
    if not confirmed:
        raise LifecycleFailure(
            "confirmation_required",
            "Explicit publication confirmation is required.",
            status_code=422,
        )
    captured_at = _now()
    snapshot = _build_snapshot(db, revision.semester_id, captured_at)
    expected_token = _publication_token(overview["stateToken"], revision, snapshot)
    if publication_token != expected_token:
        raise LifecycleConflict(
            "stale_publication_preparation",
            "The schedule or publication context changed. Prepare publication again.",
            current_overview=overview,
        )
    from_state = revision.state
    current = next((row for row in _revisions_for_semester(db, revision.semester_id) if row.state == "published" and row.id != revision.id), None)
    if current is not None:
        current.state = "superseded"
        current.state_changed_at = captured_at
        current.updated_at = captured_at
        current.row_version += 1
        _append_event(db, current, "superseded", "published", "superseded", captured_at)
    revision.state = "published"
    revision.snapshot_schema_version = 1
    revision.snapshot_document = snapshot
    revision.published_at = captured_at
    revision.state_changed_at = captured_at
    revision.updated_at = captured_at
    revision.row_version += 1
    _append_event(db, revision, "published", from_state, "published", captured_at)
    db.flush()
    return get_lifecycle_overview(db, revision.semester_id)


def get_revision_content(db: Session, revision_id: int) -> dict[str, Any]:
    revision = _revision_or_404(db, revision_id)
    overview = get_lifecycle_overview(db, revision.semester_id)
    active = next(
        (row for row in _revisions_for_semester(db, revision.semester_id) if row.state in WORKING_STATES),
        None,
    )
    current = next(
        (row for row in _revisions_for_semester(db, revision.semester_id) if row.state == "published"),
        None,
    )
    if revision.state in WORKING_STATES:
        snapshot = _build_snapshot(db, revision.semester_id, _now())
        source = "active_working"
    else:
        snapshot = revision.snapshot_document
        source = "captured_snapshot"
    if snapshot is None:
        raise LifecycleFailure(
            "snapshot_materialization_failed",
            "The selected revision has no readable schedule snapshot.",
            status_code=422,
        )
    return {
        "revision": _summary(revision, active, current),
        "contentSource": source,
        "snapshot": snapshot,
        "stateToken": overview["stateToken"],
    }


def require_active_working_revision(
    db: Session, semester_id: int, schedule_revision_id: int
) -> ScheduleRevision:
    revision = db.get(ScheduleRevision, schedule_revision_id)
    overview = get_lifecycle_overview(db, semester_id)
    if revision is None or revision.semester_id != semester_id:
        raise LifecycleConflict(
            "working_revision_required",
            "Choose the semester's active working revision before changing its schedule.",
            current_overview=overview,
        )
    active = overview["activeWorkingRevision"]
    if revision.state not in WORKING_STATES:
        raise LifecycleConflict(
            "revision_not_editable",
            "Published and historical revisions cannot be edited in place.",
            current_overview=overview,
        )
    if active is None or active["revisionId"] != revision.id:
        raise LifecycleConflict(
            "stale_lifecycle_state",
            "The selected revision is no longer the active working revision.",
            current_overview=overview,
        )
    return revision


def _build_snapshot(
    db: Session, semester_id: int, captured_at: datetime
) -> dict[str, Any]:
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise LifecycleFailure(
            "semester_not_found", "The selected semester does not exist.", status_code=404
        )
    drafts = list(
        db.scalars(
            select(DraftSchedule)
            .where(DraftSchedule.semester_id == semester_id)
            .options(selectinload(DraftSchedule.sessions))
            .order_by(DraftSchedule.course_id)
        )
    )
    drafts_by_course = {row.course_id: row for row in drafts}
    teaching_alerts = _teaching_validation_alerts(db, drafts, semester)
    draft_course_ids = list(drafts_by_course)
    course_filter = Course.current_semester_id == semester_id
    if draft_course_ids:
        course_filter = or_(course_filter, Course.id.in_(draft_course_ids))
    courses = list(
        db.scalars(
            select(Course)
            .where(course_filter)
            .options(
                selectinload(Course.cohort),
                selectinload(Course.study_type),
            )
            .order_by(Course.id)
        ).unique()
    )
    conditions: list[dict[str, Any]] = []
    captured_courses: list[dict[str, Any]] = []
    for course in courses:
        draft = drafts_by_course.get(course.id)
        sessions = list(draft.sessions) if draft else []
        scheduled = sum(item.units for item in sessions)
        remaining = max(course.total_units - scheduled, 0)
        if remaining:
            conditions.append(
                {
                    "code": "course_units_remaining",
                    "message": f"{course.name} has {remaining} teaching units remaining.",
                    "courseId": course.id,
                    "sessionKind": "teaching",
                    "sourceSessionId": None,
                    "details": {"remainingUnits": remaining},
                }
            )
        captured_sessions = []
        for session in sorted(
            sessions, key=lambda item: (item.date, item.start_time, item.id or 0)
        ):
            lecturer = db.get(Lecturer, session.lecturer_id)
            room = db.get(Room, session.room_id)
            session_alerts = [
                {
                    "code": str(alert.code),
                    "message": alert.message,
                    "details": {
                        "relatedSessionIds": [
                            related.session_id for related in alert.related_sessions
                        ],
                        "holidayDate": (
                            alert.holiday_date.isoformat()
                            if alert.holiday_date is not None
                            else None
                        ),
                        "holidayName": alert.holiday_name,
                    },
                }
                for alert in teaching_alerts.get(session.id, [])
            ]
            for alert in session_alerts:
                conditions.append(
                    {
                        "code": "teaching_validation_alert",
                        "message": f"{course.name}: {alert['message']}",
                        "courseId": course.id,
                        "sessionKind": "teaching",
                        "sourceSessionId": session.id,
                        "details": {
                            "alertCode": alert["code"],
                            **alert["details"],
                        },
                    }
                )
            captured_sessions.append(
                {
                    "sourceSessionId": session.id,
                    "date": session.date.isoformat(),
                    "startTime": session.start_time.isoformat(),
                    "endTime": session.end_time.isoformat(),
                    "units": session.units,
                    "timeWindowId": session.time_window_id,
                    "constraintWindowIndex": session.constraint_window_index,
                    "lecturer": {
                        "sourceId": lecturer.id,
                        "name": lecturer.name,
                        "referenceCode": lecturer.reference_code,
                        "capacity": None,
                    },
                    "room": {
                        "sourceId": room.id,
                        "name": room.name,
                        "referenceCode": room.reference_code,
                        "capacity": room.capacity,
                    },
                    "validationAlerts": session_alerts,
                }
            )
        captured_courses.append(
            {
                "sourceCourseId": course.id,
                "name": course.name,
                "cohort": {
                    "sourceId": course.cohort.id,
                    "name": course.cohort.name,
                    "size": course.cohort.student_count,
                },
                "studyType": {
                    "sourceId": course.study_type.id,
                    "name": course.study_type.name,
                },
                "totalUnits": course.total_units,
                "scheduledUnits": scheduled,
                "remainingUnits": remaining,
                "draftStatus": draft.status if draft else None,
                "teachingSessions": captured_sessions,
            }
        )

    exams = list(
        db.scalars(
            select(ExamSession)
            .where(ExamSession.semester_id == semester_id)
            .options(
                selectinload(ExamSession.course),
                selectinload(ExamSession.cohort),
                selectinload(ExamSession.lecturer),
                selectinload(ExamSession.room),
            )
            .order_by(ExamSession.exam_date, ExamSession.start_time, ExamSession.id)
        )
    )
    captured_exams = []
    for exam in exams:
        validity_issues = [
            {
                "code": issue["code"],
                "message": issue["message"],
                "details": {
                    key: (
                        value.isoformat()
                        if isinstance(value, (date, datetime))
                        else value
                    )
                    for key, value in issue.items()
                    if key not in {"code", "message"} and value is not None
                },
            }
            for issue in _current_validity_issues(db, exam)
        ]
        for issue in validity_issues:
            conditions.append(
                {
                    "code": "exam_validity_issue",
                    "message": f"{exam.course.name}: {issue['message']}",
                    "courseId": exam.course_id,
                    "sessionKind": "exam",
                    "sourceSessionId": exam.id,
                    "details": {
                        "issueCode": issue["code"],
                        **issue["details"],
                    },
                }
            )
        outside = not (
            exam.recommended_start_date <= exam.exam_date <= exam.recommended_end_date
        )
        if outside:
            conditions.append(
                {
                    "code": "exam_outside_recommendation",
                    "message": f"{exam.course.name} exam is outside its recommendation.",
                    "courseId": exam.course_id,
                    "sessionKind": "exam",
                    "sourceSessionId": exam.id,
                    "details": {
                        "recommendedStartDate": exam.recommended_start_date.isoformat(),
                        "recommendedEndDate": exam.recommended_end_date.isoformat(),
                    },
                }
            )
        captured_exams.append(
            {
                "sourceExamId": exam.id,
                "course": {"sourceId": exam.course_id, "name": exam.course.name},
                "cohort": {"sourceId": exam.cohort_id, "name": exam.cohort.name},
                "lecturer": {
                    "sourceId": exam.lecturer_id,
                    "name": exam.lecturer.name,
                    "referenceCode": exam.lecturer.reference_code,
                    "capacity": None,
                },
                "room": {
                    "sourceId": exam.room_id,
                    "name": exam.room.name,
                    "referenceCode": exam.room.reference_code,
                    "capacity": exam.room.capacity,
                },
                "examDate": exam.exam_date.isoformat(),
                "startTime": exam.start_time.isoformat(),
                "endTime": exam.end_time.isoformat(),
                "source": exam.source,
                "configurationIdentifier": exam.configuration_identifier,
                "configurationRevision": exam.configuration_revision,
                "durationMinutes": exam.duration_minutes,
                "examType": exam.exam_type,
                "requiredCapacity": exam.required_capacity,
                "recommendedStartDate": exam.recommended_start_date.isoformat(),
                "recommendedEndDate": exam.recommended_end_date.isoformat(),
                "recommendationWasOverridden": exam.recommendation_was_overridden,
                "finalTeachingDate": exam.final_teaching_date.isoformat(),
                "finalTeachingEndTime": exam.final_teaching_end_time.isoformat(),
                "finalTeachingSessionId": exam.final_teaching_session_id_snapshot,
                "validityIssues": validity_issues,
                "outsideRecommendedWindow": outside,
            }
        )

    exam_course_ids = {item.course_id for item in exams}
    configurations = list(
        db.scalars(
            select(CourseExamConfiguration).where(
                CourseExamConfiguration.semester_id == semester_id,
                CourseExamConfiguration.enabled.is_(True),
            )
        )
    )
    course_names = {course.id: course.name for course in courses}
    for configuration in configurations:
        if configuration.course_id not in exam_course_ids:
            conditions.append(
                {
                    "code": "enabled_exam_unscheduled",
                    "message": f"{course_names.get(configuration.course_id, 'Course')} has an enabled unscheduled exam.",
                    "courseId": configuration.course_id,
                    "sessionKind": "exam",
                    "sourceSessionId": None,
                    "details": {"configurationId": configuration.id},
                }
            )

    return {
        "schemaVersion": 1,
        "capturedAt": _iso(captured_at),
        "semester": {
            "sourceId": semester.id,
            "name": semester.name,
            "startDate": semester.start_date.isoformat(),
            "endDate": semester.end_date.isoformat(),
        },
        "courses": captured_courses,
        "examSessions": captured_exams,
        "capturedConditions": conditions,
    }


def _teaching_validation_alerts(
    db: Session,
    drafts: list[DraftSchedule],
    semester: Semester,
):
    if not drafts:
        return {}
    rooms_by_id = {row.id: row for row in db.scalars(select(Room))}
    lecturers_by_id = {row.id: row for row in db.scalars(select(Lecturer))}
    semester_plan = load_semester_plan(db, semester.id)
    constraints_by_course_id = {}
    study_windows_by_study_type_id = {}
    for draft in drafts:
        course_plan = load_course_plan(db, draft.course_id)
        constraints_by_course_id[draft.course_id] = load_generation_constraints(
            db, course_plan, semester_plan
        )
        study_type_id = draft.study_type_id_snapshot
        study_windows_by_study_type_id.setdefault(
            study_type_id, load_time_windows(db, study_type_id)
        )
    unavailability_by_resource = {}
    periods = db.scalars(
        select(ResourceUnavailabilityPeriod).options(
            selectinload(ResourceUnavailabilityPeriod.weekdays)
        )
    )
    for period in periods:
        key = (
            ("lecturer", period.lecturer_id)
            if period.lecturer_id is not None
            else ("room", period.room_id)
        )
        unavailability_by_resource.setdefault(key, []).append(period)
    return collect_validation_alerts(
        drafts,
        rooms_by_id=rooms_by_id,
        lecturers_by_id=lecturers_by_id,
        constraints_by_course_id=constraints_by_course_id,
        study_windows_by_study_type_id=study_windows_by_study_type_id,
        unavailability_by_resource=unavailability_by_resource,
        eligible_lecturer_ids_by_course={
            draft.course_id: {
                link.lecturer_id for link in draft.course.eligible_lecturers
            }
            for draft in drafts
        },
        eligible_room_ids_by_course={
            draft.course_id: {link.room_id for link in draft.course.eligible_rooms}
            for draft in drafts
        },
        active_lecturer_ids=set(
            db.scalars(select(Lecturer.id).where(Lecturer.is_active.is_(True)))
        ),
        active_room_ids={
            room.id for room in rooms_by_id.values() if room.is_active
        },
        current_cohort_sizes_by_course={
            draft.course_id: draft.course.cohort.student_count for draft in drafts
        },
        holidays_by_date=holiday_snapshot(
            db, semester.start_date, semester.end_date
        ).by_date,
    )


def _materialize_snapshot(db: Session, semester_id: int, snapshot: dict[str, Any] | None) -> None:
    if not snapshot:
        raise LifecycleFailure("snapshot_materialization_failed", "The revision has no schedule snapshot to restore.", status_code=422)
    semester = db.get(Semester, semester_id)
    if semester is None or snapshot.get("semester", {}).get("sourceId") != semester_id:
        raise LifecycleFailure("snapshot_materialization_failed", "The snapshot does not belong to the selected semester.", status_code=422)

    course_rows: dict[int, Course] = {}
    for captured in snapshot.get("courses", []):
        course = db.get(Course, captured["sourceCourseId"])
        cohort_id = captured["cohort"]["sourceId"]
        study_type_id = captured["studyType"]["sourceId"]
        if course is None or course.cohort_id != cohort_id or course.study_type_id != study_type_id:
            raise LifecycleConflict("snapshot_reference_missing", f"Course {captured['name']} can no longer be restored from its captured references.", current_overview=get_lifecycle_overview(db, semester_id))
        for session in captured.get("teachingSessions", []):
            if db.get(Lecturer, session["lecturer"]["sourceId"]) is None or db.get(Room, session["room"]["sourceId"]) is None:
                raise LifecycleConflict("snapshot_reference_missing", "A captured teaching resource no longer exists.", current_overview=get_lifecycle_overview(db, semester_id))
        course_rows[course.id] = course
    for exam in snapshot.get("examSessions", []):
        if db.get(Course, exam["course"]["sourceId"]) is None or db.get(Lecturer, exam["lecturer"]["sourceId"]) is None or db.get(Room, exam["room"]["sourceId"]) is None:
            raise LifecycleConflict("snapshot_reference_missing", "A captured exam reference no longer exists.", current_overview=get_lifecycle_overview(db, semester_id))

    db.execute(delete(ExamSession).where(ExamSession.semester_id == semester_id))
    draft_ids = select(DraftSchedule.id).where(DraftSchedule.semester_id == semester_id)
    db.execute(delete(DraftSession).where(DraftSession.draft_schedule_id.in_(draft_ids)))
    db.execute(delete(DraftSchedule).where(DraftSchedule.semester_id == semester_id))
    db.flush()
    teaching_ids: dict[tuple[int, str, str], int] = {}
    for captured in snapshot.get("courses", []):
        course = course_rows[captured["sourceCourseId"]]
        if not captured.get("teachingSessions") and captured.get("draftStatus") is None:
            continue
        draft = DraftSchedule(
            course_id=course.id,
            semester_id=semester_id,
            revision=1,
            selected_time_window_id=None,
            status=captured.get("draftStatus") or "draft",
            course_name_snapshot=captured["name"],
            course_total_units_snapshot=captured["totalUnits"],
            course_min_session_units_snapshot=course.min_session_units,
            course_max_session_units_snapshot=course.max_session_units,
            cohort_id_snapshot=captured["cohort"]["sourceId"],
            cohort_name_snapshot=captured["cohort"]["name"],
            cohort_size_snapshot=captured["cohort"]["size"],
            study_type_id_snapshot=captured["studyType"]["sourceId"],
            study_type_name_snapshot=captured["studyType"]["name"],
            semester_name_snapshot=snapshot["semester"]["name"],
            semester_start_date_snapshot=date.fromisoformat(snapshot["semester"]["startDate"]),
            semester_end_date_snapshot=date.fromisoformat(snapshot["semester"]["endDate"]),
        )
        for item in captured.get("teachingSessions", []):
            draft.sessions.append(DraftSession(
                course_id=course.id,
                lecturer_id=item["lecturer"]["sourceId"],
                cohort_id=captured["cohort"]["sourceId"],
                room_id=item["room"]["sourceId"],
                date=date.fromisoformat(item["date"]),
                start_time=time.fromisoformat(item["startTime"]),
                end_time=time.fromisoformat(item["endTime"]),
                units=item["units"],
                time_window_id=item.get("timeWindowId"),
                constraint_window_index=item.get("constraintWindowIndex", 0),
            ))
        db.add(draft)
        db.flush()
        for item, row in zip(captured.get("teachingSessions", []), draft.sessions):
            teaching_ids[(course.id, item["date"], item["endTime"])] = row.id

    for item in snapshot.get("examSessions", []):
        course_id = item["course"]["sourceId"]
        anchor_id = teaching_ids.get((course_id, item["finalTeachingDate"], item["finalTeachingEndTime"]), item.get("finalTeachingSessionId", 0))
        db.add(ExamSession(
            course_id=course_id,
            semester_id=semester_id,
            cohort_id=item["cohort"]["sourceId"],
            lecturer_id=item["lecturer"]["sourceId"],
            room_id=item["room"]["sourceId"],
            exam_date=date.fromisoformat(item["examDate"]),
            start_time=time.fromisoformat(item["startTime"]),
            end_time=time.fromisoformat(item["endTime"]),
            source=item["source"],
            revision=1,
            configuration_identifier=item["configurationIdentifier"],
            configuration_revision=item["configurationRevision"],
            duration_minutes=item["durationMinutes"],
            exam_type=item["examType"],
            required_capacity=item["requiredCapacity"],
            recommended_start_date=date.fromisoformat(item["recommendedStartDate"]),
            recommended_end_date=date.fromisoformat(item["recommendedEndDate"]),
            recommendation_was_overridden=item["recommendationWasOverridden"],
            final_teaching_date=date.fromisoformat(item["finalTeachingDate"]),
            final_teaching_end_time=time.fromisoformat(item["finalTeachingEndTime"]),
            final_teaching_session_id_snapshot=anchor_id,
            course_name_snapshot=item["course"]["name"],
            semester_name_snapshot=snapshot["semester"]["name"],
            cohort_name_snapshot=item["cohort"]["name"],
            lecturer_name_snapshot=item["lecturer"]["name"],
            lecturer_reference_snapshot=item["lecturer"]["referenceCode"],
            room_name_snapshot=item["room"]["name"],
            room_reference_snapshot=item["room"]["referenceCode"],
        ))
    db.flush()


def _snapshot_totals(snapshot: dict[str, Any]) -> dict[str, int]:
    courses = snapshot["courses"]
    return {
        "courseCount": len(courses),
        "totalUnits": sum(item["totalUnits"] for item in courses),
        "scheduledUnits": sum(item["scheduledUnits"] for item in courses),
        "remainingUnits": sum(item["remainingUnits"] for item in courses),
    }


def _summary(
    revision: ScheduleRevision,
    active: ScheduleRevision | None,
    current: ScheduleRevision | None,
) -> dict[str, Any]:
    state = revision.state
    return {
        "revisionId": revision.id,
        "semesterId": revision.semester_id,
        "revisionNumber": revision.revision_number,
        "revisionVersion": revision.row_version,
        "state": state,
        "originRevisionId": revision.origin_revision_id,
        "isActiveWorking": active is not None and active.id == revision.id,
        "isCurrentPublication": current is not None and current.id == revision.id,
        "createdAt": _iso(revision.created_at),
        "stateChangedAt": _iso(revision.state_changed_at),
        "publishedAt": _iso(revision.published_at) if revision.published_at else None,
        "events": [
            {
                "eventSequence": event.event_sequence,
                "eventType": event.event_type,
                "fromState": event.from_state,
                "toState": event.to_state,
                "occurredAt": _iso(event.occurred_at),
            }
            for event in sorted(revision.events, key=lambda item: item.event_sequence)
        ],
        "allowedActions": {
            "markReady": state == "draft",
            "returnToDraft": state == "ready_for_review",
            "preparePublication": state in WORKING_STATES,
            "abandon": state in WORKING_STATES,
            "restore": state == "abandoned" and active is None,
            "editSchedule": state in WORKING_STATES and active is not None and active.id == revision.id,
        },
    }


def _revisions_for_semester(db: Session, semester_id: int) -> list[ScheduleRevision]:
    return list(
        db.scalars(
            select(ScheduleRevision)
            .where(ScheduleRevision.semester_id == semester_id)
            .options(selectinload(ScheduleRevision.events))
            .order_by(ScheduleRevision.revision_number)
        ).unique()
    )


def _revision_or_404(db: Session, revision_id: int) -> ScheduleRevision:
    revision = db.scalar(
        select(ScheduleRevision)
        .where(ScheduleRevision.id == revision_id)
        .options(selectinload(ScheduleRevision.events))
    )
    if revision is None:
        raise LifecycleFailure(
            "revision_not_found",
            "The selected schedule revision does not exist.",
            status_code=404,
        )
    return revision


def _require_current_expectations(
    revision: ScheduleRevision,
    overview: dict[str, Any],
    expected_revision_version: int,
    expected_state_token: str,
) -> None:
    if (
        revision.row_version != expected_revision_version
        or overview["stateToken"] != expected_state_token
    ):
        raise LifecycleConflict(
            "stale_lifecycle_state",
            "The revision lifecycle changed. Review the current state and retry.",
            current_overview=overview,
        )


def _state_token(semester_id: int, revisions: list[ScheduleRevision]) -> str:
    material = {
        "semesterId": semester_id,
        "revisions": [
            [
                row.id,
                row.revision_number,
                row.row_version,
                row.state,
                row.origin_revision_id,
                max((event.event_sequence for event in row.events), default=0),
            ]
            for row in revisions
        ],
    }
    return _digest(material)


def _publication_token(
    state_token: str, revision: ScheduleRevision, snapshot: dict[str, Any]
) -> str:
    material_snapshot = dict(snapshot)
    material_snapshot.pop("capturedAt", None)
    return _digest(
        {
            "stateToken": state_token,
            "revisionId": revision.id,
            "revisionVersion": revision.row_version,
            "state": revision.state,
            "snapshot": material_snapshot,
        }
    )


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _claim_semester(db: Session, semester_id: int) -> None:
    db.execute(
        update(Semester).where(Semester.id == semester_id).values(id=Semester.id)
    )


def _next_revision_number(db: Session, semester_id: int) -> int:
    return (
        db.scalar(
            select(func.max(ScheduleRevision.revision_number)).where(
                ScheduleRevision.semester_id == semester_id
            )
        )
        or 0
    ) + 1


def _append_event(
    db: Session,
    revision: ScheduleRevision,
    event_type: str,
    from_state: str | None,
    to_state: str,
    occurred_at: datetime | None = None,
) -> None:
    persisted_sequence = (
        db.scalar(
            select(func.max(ScheduleRevisionEvent.event_sequence)).where(
                ScheduleRevisionEvent.semester_id == revision.semester_id
            )
        )
        or 0
    )
    pending_sequence = max(
        (
            item.event_sequence
            for item in db.new
            if isinstance(item, ScheduleRevisionEvent)
            and item.semester_id == revision.semester_id
        ),
        default=0,
    )
    event = ScheduleRevisionEvent(
        semester_id=revision.semester_id,
        schedule_revision=revision,
        event_sequence=max(persisted_sequence, pending_sequence) + 1,
        event_type=event_type,
        from_state=from_state,
        to_state=to_state,
        occurred_at=occurred_at or _now(),
    )
    db.add(event)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
