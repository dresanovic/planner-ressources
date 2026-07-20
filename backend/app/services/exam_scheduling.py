from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import hashlib
import json
import os
from time import monotonic
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    CourseExamConfiguration,
    DraftSchedule,
    DraftSession,
    ExamSession,
    InstitutionHoliday,
    Lecturer,
    Room,
    Semester,
    StudyTypeTimeWindow,
)
from app.services.exam_optimization import CandidateInput, ExamCandidate, Occupancy, OptimizationIssue, build_candidates, select_joint_candidates
from app.services.resource_rules import intervals_overlap, resource_is_unavailable


@dataclass(frozen=True)
class ExamErrorItem:
    code: str
    message: str
    field: str | None = None
    meta: dict | None = None


class ExamSchedulingError(ValueError):
    def __init__(self, status_code: int, errors: list[ExamErrorItem], current_state=None):
        super().__init__(errors[0].message if errors else "Exam scheduling error.")
        self.status_code = status_code
        self.errors = errors
        self.current_state = current_state


def institution_today(now: datetime | None = None) -> date:
    timezone = ZoneInfo(os.getenv("INSTITUTION_TIMEZONE", "Europe/Vienna"))
    current = now or datetime.now(timezone)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone)
    return current.astimezone(timezone).date()


def get_exam_planning_overview(db: Session, semester_id: int, *, today: date | None = None) -> dict:
    current_day = today or institution_today()
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise ExamSchedulingError(404, [ExamErrorItem("NOT_FOUND", "Semester not found.")])
    courses = list(db.scalars(select(Course).where(Course.current_semester_id == semester_id).order_by(Course.name, Course.id)))
    return {
        "semesterId": semester_id,
        "institutionToday": current_day,
        "courses": [_course_state(db, course, semester, current_day) for course in courses],
    }


def save_exam_configuration(
    db: Session,
    *,
    course_id: int,
    semester_id: int,
    enabled: bool,
    expected_revision: int | None,
    configuration: dict | None,
    today: date | None = None,
) -> tuple[dict, bool]:
    current_day = today or institution_today()
    course, semester = _require_course_semester(db, course_id, semester_id)
    row = db.scalar(select(CourseExamConfiguration).where(CourseExamConfiguration.course_id == course_id, CourseExamConfiguration.semester_id == semester_id))
    active = _active_exam(db, course_id, semester_id, current_day)
    if active is not None:
        state = _course_state(db, course, semester, current_day)
        raise ExamSchedulingError(409, [ExamErrorItem("ACTIVE_EXAM_EXISTS", "The active exam must become past or be deleted before changing its configuration.")], state)
    if row is None and expected_revision is not None:
        raise ExamSchedulingError(409, [ExamErrorItem("STALE_REVISION", "The exam configuration no longer matches the opened state.")])
    if row is not None and row.revision != expected_revision:
        raise ExamSchedulingError(409, [ExamErrorItem("STALE_REVISION", "The exam configuration changed. Refresh and try again.", meta={"currentRevision": row.revision})], _course_state(db, course, semester, current_day))
    values = _validate_configuration(db, course, enabled, configuration)
    created = row is None
    if row is None:
        row = CourseExamConfiguration(course_id=course_id, semester_id=semester_id, revision=1)
        db.add(row)
    else:
        row.revision += 1
    row.enabled = enabled
    row.configuration_consumed = False
    if values:
        for key, value in values.items():
            setattr(row, key, value)
    db.flush()
    return _course_state(db, course, semester, current_day), created


def prepare_exam_generation(db: Session, semester_id: int, course_ids: list[int], *, today: date | None = None) -> dict:
    if not 1 <= len(course_ids) <= 100 or len(set(course_ids)) != len(course_ids):
        raise ExamSchedulingError(422, [ExamErrorItem("INVALID_SELECTION", "Select 1 to 100 unique courses.", "courseIds")])
    current_day = today or institution_today()
    overview = get_exam_planning_overview(db, semester_id, today=current_day)
    by_id = {item["courseId"]: item for item in overview["courses"]}
    missing = [course_id for course_id in course_ids if course_id not in by_id]
    if missing:
        raise ExamSchedulingError(422, [ExamErrorItem("COURSE_NOT_IN_SEMESTER", f"Course {course_id} is not in the selected semester.", "courseIds") for course_id in missing])
    courses = []
    for course_id in course_ids:
        state = by_id[course_id]
        config = state["configuration"]
        courses.append({
            "courseId": course_id,
            "courseName": state["courseName"],
            "configurationId": config["id"] if config else None,
            "configurationRevision": config["revision"] if config else None,
            "inputSnapshotToken": state["inputSnapshotToken"],
            "eligibility": state["generationEligibility"],
        })
    return {
        "semesterId": semester_id,
        "institutionToday": current_day,
        "sharedSnapshotToken": _digest([semester_id, current_day.isoformat(), sorted(course_ids), sorted((item["courseId"], item["inputSnapshotToken"]) for item in overview["courses"])]),
        "courses": courses,
    }


def generate_exams(db: Session, request: dict, *, today: date | None = None) -> dict:
    started = monotonic()
    current_day = today or institution_today()
    semester_id = request["semesterId"]
    _claim_semester(db, semester_id)
    prepared = prepare_exam_generation(db, semester_id, [item["courseId"] for item in request["courses"]], today=current_day)
    if request["institutionToday"] != current_day or request["sharedSnapshotToken"] != prepared["sharedSnapshotToken"]:
        raise ExamSchedulingError(409, [ExamErrorItem("STALE_INPUT_SNAPSHOT", "Shared exam-planning inputs changed. Prepare again.")])
    fresh_by_id = {item["courseId"]: item for item in prepared["courses"]}
    candidates_by_course: dict[int, list[ExamCandidate]] = {}
    issues_by_course: dict[int, list[dict]] = {}
    outcomes: dict[int, dict] = {}
    for supplied in request["courses"]:
        course_id = supplied["courseId"]
        fresh = fresh_by_id[course_id]
        course = db.get(Course, course_id)
        config = _configuration(db, course_id, semester_id)
        base = _outcome_base(course, config)
        if supplied["inputSnapshotToken"] != fresh["inputSnapshotToken"] or supplied.get("configurationId") != fresh["configurationId"] or supplied.get("configurationRevision") != fresh["configurationRevision"]:
            outcomes[course_id] = {**base, "status": "stale", "saved": False, "exam": None, "reasons": [_issue("STALE_INPUT_SNAPSHOT", "Course exam-planning inputs changed. Prepare again.")]}
            continue
        code = fresh["eligibility"]["code"]
        if code == "DISABLED":
            outcomes[course_id] = {**base, "status": "skipped_disabled", "saved": False, "exam": None, "reasons": []}
            continue
        if code == "ACTIVE_EXAM_EXISTS":
            outcomes[course_id] = {**base, "status": "skipped_active", "saved": False, "exam": None, "reasons": []}
            continue
        if not fresh["eligibility"]["eligible"]:
            outcomes[course_id] = {**base, "status": "failed", "saved": False, "exam": None, "reasons": [_issue(code or "CONFIGURATION_INCOMPLETE", fresh["eligibility"]["message"] or "Exam configuration is not eligible.")]}
            continue
        candidates, issues = _automatic_candidates(db, course, config, semester_id)
        candidates_by_course[course_id] = candidates
        issues_by_course[course_id] = issues
    selected, proven = select_joint_candidates(candidates_by_course)
    if not proven:
        raise ExamSchedulingError(503, [ExamErrorItem("OPTIMAL_RESULT_NOT_PROVEN", "A bounded optimal exam arrangement was not proven; nothing was saved.")])
    for course_id, candidates in candidates_by_course.items():
        if course_id not in selected:
            base = _outcome_base(db.get(Course, course_id), _configuration(db, course_id, semester_id))
            issues = issues_by_course[course_id] or _proposed_conflict_issues(candidates, selected.values())
            reasons = [_optimization_issue_response(db, item) for item in issues]
            outcomes[course_id] = {**base, "status": "failed", "saved": False, "exam": None, "reasons": reasons or [_issue("NO_VALID_EXAM_PLACEMENT", "No conflict-free exam placement is available.")]}
            continue
        candidate = selected[course_id]
        course = db.get(Course, course_id)
        config = _configuration(db, course_id, semester_id)
        anchor = _final_anchor(db, course_id, semester_id)
        row = _new_exam_row(db, course, config, anchor, candidate.date, candidate.start_time, candidate.lecturer_id, candidate.room_id, "generated")
        db.add(row)
        config.configuration_consumed = True
        config.revision += 1
        db.flush()
        exam = _exam_response(db, row, current_day)
        outcomes[course_id] = {**_outcome_base(course, config), "status": "scheduled", "saved": True, "exam": exam, "reasons": []}
    ordered = [outcomes[item["courseId"]] for item in request["courses"]]
    counts = {status: sum(item["status"] == status for item in ordered) for status in ("scheduled", "failed", "stale", "skipped_active", "skipped_disabled")}
    return {
        "semesterId": semester_id,
        "summary": {"total": len(ordered), **counts, "elapsedMilliseconds": min(60000, int((monotonic() - started) * 1000)), "optimalForPreparedSnapshot": True},
        "outcomes": ordered,
    }


def create_manual_exam(db: Session, *, course_id: int, semester_id: int, exam_date: date, start_time: time, lecturer_id: int, room_id: int, expected_configuration_revision: int, input_snapshot_token: str, today: date | None = None) -> dict:
    current_day = today or institution_today()
    _claim_semester(db, semester_id)
    course, semester = _require_course_semester(db, course_id, semester_id)
    state = _course_state(db, course, semester, current_day)
    config = _configuration(db, course_id, semester_id)
    if config is None or not config.enabled:
        raise ExamSchedulingError(422, [ExamErrorItem("CONFIGURATION_INCOMPLETE", "Enable and complete the exam configuration first.")])
    if config.revision != expected_configuration_revision or state["inputSnapshotToken"] != input_snapshot_token:
        raise ExamSchedulingError(409, [ExamErrorItem("STALE_INPUT_SNAPSHOT", "Exam planning inputs changed. Refresh and try again.")], state)
    if _active_exam(db, course_id, semester_id, current_day):
        raise ExamSchedulingError(409, [ExamErrorItem("DUPLICATE_ACTIVE_EXAM", "Only one active exam is allowed for a course.")], state)
    anchor = _final_anchor(db, course_id, semester_id)
    if anchor is None:
        raise ExamSchedulingError(422, [ExamErrorItem("FINAL_TEACHING_SESSION_MISSING", "Save a teaching session before placing the exam.")])
    end_time = _end_time(start_time, config.duration_minutes)
    errors = _placement_errors(db, course, semester, config, exam_date, start_time, end_time, lecturer_id, room_id, anchor, exclude_exam_id=None)
    if errors:
        raise ExamSchedulingError(422, errors)
    row = _new_exam_row(db, course, config, anchor, exam_date, start_time, lecturer_id, room_id, "manual")
    db.add(row)
    config.configuration_consumed = True
    config.revision += 1
    db.flush()
    return _course_state(db, course, semester, current_day)


def update_exam(db: Session, exam_id: int, *, exam_date: date, start_time: time, lecturer_id: int, room_id: int, expected_exam_revision: int, input_snapshot_token: str, today: date | None = None) -> dict:
    current_day = today or institution_today()
    row = db.get(ExamSession, exam_id)
    if row is None:
        raise ExamSchedulingError(404, [ExamErrorItem("NOT_FOUND", "Exam not found.")])
    _claim_semester(db, row.semester_id)
    course, semester = _require_course_semester(db, row.course_id, row.semester_id)
    if row.revision != expected_exam_revision or _exam_token(db, row) != input_snapshot_token:
        raise ExamSchedulingError(409, [ExamErrorItem("STALE_INPUT_SNAPSHOT", "The exam or related planning inputs changed. Refresh and try again.")], _course_state(db, course, semester, current_day))
    config = _configuration(db, row.course_id, row.semester_id)
    anchor = _final_anchor(db, row.course_id, row.semester_id)
    if anchor is None:
        raise ExamSchedulingError(422, [ExamErrorItem("FINAL_TEACHING_SESSION_MISSING", "Save a teaching session before correcting the exam.")])
    end_time = _end_time(start_time, row.duration_minutes)
    errors = _placement_errors(db, course, semester, config, exam_date, start_time, end_time, lecturer_id, room_id, anchor, exclude_exam_id=row.id, required_capacity=row.required_capacity)
    if exam_date >= current_day:
        other = _active_exam(db, row.course_id, row.semester_id, current_day, exclude_id=row.id)
        if other:
            errors.append(ExamErrorItem("DUPLICATE_ACTIVE_EXAM", "Only one active exam is allowed for a course."))
    if errors:
        raise ExamSchedulingError(422, errors)
    lecturer = db.get(Lecturer, lecturer_id)
    room = db.get(Room, room_id)
    row.exam_date, row.start_time, row.end_time = exam_date, start_time, end_time
    row.lecturer_id, row.room_id = lecturer_id, room_id
    row.lecturer_name_snapshot, row.lecturer_reference_snapshot = lecturer.name, lecturer.reference_code
    row.room_name_snapshot, row.room_reference_snapshot = room.name, room.reference_code
    row.final_teaching_date, row.final_teaching_end_time = anchor["date"], anchor["endTime"]
    row.final_teaching_session_id_snapshot = anchor["teachingSessionId"]
    row.revision += 1
    db.flush()
    return _course_state(db, course, semester, current_day)


def delete_exam(db: Session, exam_id: int, *, confirmed: bool, expected_exam_revision: int, input_snapshot_token: str, today: date | None = None) -> dict:
    current_day = today or institution_today()
    row = db.get(ExamSession, exam_id)
    if row is None:
        raise ExamSchedulingError(404, [ExamErrorItem("NOT_FOUND", "Exam not found.")])
    _claim_semester(db, row.semester_id)
    course, semester = _require_course_semester(db, row.course_id, row.semester_id)
    if not confirmed:
        raise ExamSchedulingError(422, [ExamErrorItem("CONFIRMATION_REQUIRED", "Confirm deletion of the selected exam.", "confirmed")])
    if row.revision != expected_exam_revision or _exam_token(db, row) != input_snapshot_token:
        raise ExamSchedulingError(409, [ExamErrorItem("STALE_INPUT_SNAPSHOT", "The exam or related planning inputs changed. Refresh and try again.")], _course_state(db, course, semester, current_day))
    lifecycle = "active" if row.exam_date >= current_day else "past"
    db.delete(row)
    config = _configuration(db, row.course_id, row.semester_id)
    consequence = "historical_exam_only"
    if lifecycle == "active" and config:
        config.configuration_consumed = False
        config.revision += 1
        consequence = "configuration_enabled_unscheduled"
    db.flush()
    return {"deletedExamId": exam_id, "deletedLifecycleStatus": lifecycle, "consequence": consequence, "state": _course_state(db, course, semester, current_day)}


def _course_state(db: Session, course: Course, semester: Semester, today: date) -> dict:
    config = _configuration(db, course.id, semester.id)
    anchor = _final_anchor(db, course.id, semester.id)
    sessions = list(db.scalars(select(ExamSession).where(ExamSession.course_id == course.id, ExamSession.semester_id == semester.id).order_by(ExamSession.exam_date.desc(), ExamSession.start_time.desc(), ExamSession.id.desc())))
    active_rows = [row for row in sessions if row.exam_date >= today]
    past_rows = [row for row in sessions if row.exam_date < today]
    eligibility = _eligibility(db, course, config, anchor, bool(active_rows))
    config_response = _configuration_response(config, anchor) if config and config.enabled else None
    material = [course.id, course.revision, semester.id, semester.revision, anchor, _config_material(config), [(row.id, row.revision, row.exam_date.isoformat()) for row in sessions], _semester_occupancy_material(db, semester.id), _holiday_material(db, semester), _resource_material(db, course)]
    return {
        "courseId": course.id,
        "courseName": course.name,
        "semesterId": semester.id,
        "cohortId": course.cohort_id,
        "cohortName": course.cohort.name,
        "enabled": bool(config and config.enabled),
        "configuration": config_response,
        "finalTeachingAnchor": _anchor_response(anchor),
        "activeExam": _exam_response(db, active_rows[0], today) if active_rows else None,
        "pastExams": [_exam_response(db, row, today) for row in past_rows],
        "generationEligibility": eligibility,
        "inputSnapshotToken": _digest(material),
    }


def _configuration_response(config, anchor):
    start, end = _recommendation(config, anchor)
    return {"id": config.id, "revision": config.revision, "identifier": config.identifier, "durationMinutes": config.duration_minutes, "recommendedStartOverride": config.recommended_start_override, "recommendedEndOverride": config.recommended_end_override, "requiredCapacity": config.required_capacity, "examType": config.exam_type, "responsibleLecturerId": config.responsible_lecturer_id, "configurationConsumed": config.configuration_consumed, "recommendedStartDate": start, "recommendedEndDate": end, "recommendationWasOverridden": config.recommended_start_override is not None}


def _exam_response(db: Session, row: ExamSession, today: date) -> dict:
    issues = _current_validity_issues(db, row)
    return {"id": row.id, "revision": row.revision, "courseId": row.course_id, "semesterId": row.semester_id, "configurationIdentifier": row.configuration_identifier, "examType": row.exam_type, "durationMinutes": row.duration_minutes, "requiredCapacity": row.required_capacity, "recommendedStartDate": row.recommended_start_date, "recommendedEndDate": row.recommended_end_date, "recommendationWasOverridden": row.recommendation_was_overridden, "outsideRecommendedWindow": not row.recommended_start_date <= row.exam_date <= row.recommended_end_date, "finalTeachingAnchor": {"date": row.final_teaching_date, "endTime": row.final_teaching_end_time, "teachingSessionId": row.final_teaching_session_id_snapshot}, "date": row.exam_date, "startTime": row.start_time, "endTime": row.end_time, "lecturer": {"id": row.lecturer_id, "name": row.lecturer_name_snapshot, "referenceCode": row.lecturer_reference_snapshot}, "cohort": {"id": row.cohort_id, "name": row.cohort_name_snapshot, "referenceCode": None}, "room": {"id": row.room_id, "name": row.room_name_snapshot, "referenceCode": row.room_reference_snapshot, "capacity": row.room.capacity}, "lifecycleStatus": "active" if row.exam_date >= today else "past", "source": row.source, "validityIssues": issues, "inputSnapshotToken": _exam_token(db, row)}


def _validate_configuration(db, course, enabled, configuration):
    if not enabled:
        return {}
    errors = []
    if configuration is None:
        errors.append(ExamErrorItem("CONFIGURATION_REQUIRED", "Configuration values are required when exams are enabled.", "configuration"))
        raise ExamSchedulingError(422, errors)
    identifier = str(configuration.get("identifier", "")).strip()
    exam_type = str(configuration.get("exam_type", "")).strip()
    duration = configuration.get("duration_minutes")
    capacity = configuration.get("required_capacity")
    start, end = configuration.get("recommended_start_override"), configuration.get("recommended_end_override")
    if not identifier or len(identifier) > 200: errors.append(ExamErrorItem("INVALID_EXAM_IDENTIFIER", "Enter an exam identifier of at most 200 characters.", "identifier"))
    if not isinstance(duration, int) or duration <= 0: errors.append(ExamErrorItem("INVALID_EXAM_DURATION", "Duration must be a positive whole number.", "durationMinutes"))
    if not isinstance(capacity, int) or capacity <= 0: errors.append(ExamErrorItem("INVALID_REQUIRED_CAPACITY", "Required capacity must be a positive whole number.", "requiredCapacity"))
    if not exam_type or len(exam_type) > 200: errors.append(ExamErrorItem("INVALID_EXAM_TYPE", "Enter an exam type of at most 200 characters.", "examType"))
    if (start is None) != (end is None): errors.append(ExamErrorItem("INVALID_RECOMMENDED_RANGE", "Set both recommended dates or neither.", "recommendedEndOverride"))
    elif start and end < start: errors.append(ExamErrorItem("INVALID_RECOMMENDED_RANGE", "Recommended end cannot be before its start.", "recommendedEndOverride"))
    lecturer_id = configuration.get("responsible_lecturer_id")
    lecturer = db.get(Lecturer, lecturer_id) if isinstance(lecturer_id, int) else None
    eligible = lecturer and lecturer.is_active and db.get(CourseEligibleLecturer, (course.id, lecturer.id)) is not None
    if not eligible: errors.append(ExamErrorItem("RESPONSIBLE_LECTURER_INELIGIBLE", "Choose a current active lecturer eligible for this course.", "responsibleLecturerId"))
    if errors: raise ExamSchedulingError(422, errors)
    return {"identifier": identifier, "duration_minutes": duration, "recommended_start_override": start, "recommended_end_override": end, "required_capacity": capacity, "exam_type": exam_type, "responsible_lecturer_id": lecturer_id}


def _placement_errors(db, course, semester, config, exam_date, start_time, end_time, lecturer_id, room_id, anchor, exclude_exam_id, required_capacity=None):
    errors = []
    capacity_required = required_capacity or config.required_capacity
    lecturer = db.get(Lecturer, lecturer_id)
    room = db.get(Room, room_id)
    if end_time is None: errors.append(ExamErrorItem("INVALID_EXAM_INTERVAL", "The exam must end on the same day.", "startTime"))
    if not semester.start_date <= exam_date <= semester.end_date: errors.append(ExamErrorItem("OUTSIDE_SEMESTER", "The exam date must be inside the semester.", "date"))
    if exam_date < anchor["date"] or (exam_date == anchor["date"] and start_time < anchor["endTime"]): errors.append(ExamErrorItem("BEFORE_FINAL_TEACHING", "The exam cannot start before the final teaching session ends.", "date"))
    if not lecturer or not lecturer.is_active or db.get(CourseEligibleLecturer, (course.id, lecturer_id)) is None: errors.append(ExamErrorItem("RESPONSIBLE_LECTURER_INELIGIBLE", "The lecturer is not active and eligible for this course.", "lecturerId"))
    if not room or not room.is_active or db.get(CourseEligibleRoom, (course.id, room_id)) is None: errors.append(ExamErrorItem("ROOM_INELIGIBLE", "The room is not active and eligible for this course.", "roomId"))
    if room and room.capacity < capacity_required: errors.append(ExamErrorItem("INSUFFICIENT_ROOM_CAPACITY", "The room does not meet the required capacity.", "roomId"))
    if end_time is None: return errors
    if lecturer and resource_is_unavailable(lecturer.unavailability_periods, exam_date, start_time, end_time): errors.append(ExamErrorItem("LECTURER_UNAVAILABLE", "The lecturer is unavailable for the full exam interval.", "lecturerId"))
    if room and resource_is_unavailable(room.unavailability_periods, exam_date, start_time, end_time): errors.append(ExamErrorItem("ROOM_UNAVAILABLE", "The room is unavailable for the full exam interval.", "roomId"))
    holiday = db.scalar(select(InstitutionHoliday).where(InstitutionHoliday.date == exam_date))
    if holiday: errors.append(ExamErrorItem("INSTITUTION_HOLIDAY", f"The exam date is the institution holiday {holiday.name}.", "date", {"holidayName": holiday.name}))
    interval_start, interval_end = datetime.combine(exam_date, start_time), datetime.combine(exam_date, end_time)
    for session in db.scalars(select(DraftSession).join(DraftSchedule).where(DraftSchedule.semester_id == semester.id, DraftSession.date == exam_date)):
        if intervals_overlap(interval_start, interval_end, datetime.combine(exam_date, session.start_time), datetime.combine(exam_date, session.end_time)):
            if session.lecturer_id == lecturer_id: errors.append(ExamErrorItem("LECTURER_OCCUPIED", "The lecturer has a teaching session at this time.", meta={"relatedSessionId": session.id}))
            if session.room_id == room_id: errors.append(ExamErrorItem("ROOM_OCCUPIED", "The room has a teaching session at this time.", meta={"relatedSessionId": session.id}))
            if session.cohort_id == course.cohort_id: errors.append(ExamErrorItem("COHORT_OCCUPIED", "The cohort has a teaching session at this time.", meta={"relatedSessionId": session.id}))
    query = select(ExamSession).where(ExamSession.semester_id == semester.id, ExamSession.exam_date == exam_date)
    if exclude_exam_id is not None: query = query.where(ExamSession.id != exclude_exam_id)
    for existing in db.scalars(query):
        if intervals_overlap(interval_start, interval_end, datetime.combine(exam_date, existing.start_time), datetime.combine(exam_date, existing.end_time)):
            if existing.lecturer_id == lecturer_id: errors.append(ExamErrorItem("LECTURER_OCCUPIED", "The lecturer has another exam at this time.", meta={"relatedSessionId": existing.id}))
            if existing.room_id == room_id: errors.append(ExamErrorItem("ROOM_OCCUPIED", "The room has another exam at this time.", meta={"relatedSessionId": existing.id}))
            if existing.cohort_id == course.cohort_id: errors.append(ExamErrorItem("COHORT_OCCUPIED", "The cohort has another exam at this time.", meta={"relatedSessionId": existing.id}))
    return _unique_errors(errors)


def _automatic_candidates(db, course, config, semester_id):
    semester = db.get(Semester, semester_id)
    anchor = _final_anchor(db, course.id, semester_id)
    start, end = _recommendation(config, anchor)
    active_rooms = [item.room for item in course.eligible_rooms if item.room.is_active]
    eligible_rooms = [room for room in active_rooms if room.capacity >= config.required_capacity]
    if not active_rooms:
        return [], [OptimizationIssue("ROOM_INELIGIBLE", "No active eligible room is configured for this course.")]
    if not eligible_rooms:
        return [], [OptimizationIssue("INSUFFICIENT_ROOM_CAPACITY", "No eligible room meets the configured exam capacity.")]
    proposals = tuple((window.weekday, window.start_time) for window in course.study_type.time_windows if window.is_active)
    holidays = frozenset(db.scalars(select(InstitutionHoliday.date).where(InstitutionHoliday.date.between(semester.start_date, semester.end_date))))
    fixed = tuple(_fixed_occupancy(db, semester_id))
    spec = CandidateInput(course_id=course.id, semester_start=semester.start_date, semester_end=semester.end_date, final_teaching_date=anchor["date"], final_teaching_end_time=anchor["endTime"], recommended_start=start, recommended_end=end, duration_minutes=config.duration_minutes, lecturer_id=config.responsible_lecturer_id, cohort_id=course.cohort_id, room_ids=tuple(room.id for room in eligible_rooms), start_proposals=proposals, holidays=holidays, fixed_occupancy=fixed)
    candidates, issues = build_candidates(spec)
    lecturer = db.get(Lecturer, config.responsible_lecturer_id)
    filtered = []
    availability_issues = []
    for candidate in candidates:
        lecturer_blocked = resource_is_unavailable(lecturer.unavailability_periods, candidate.date, candidate.start_time, candidate.end_time)
        room = db.get(Room, candidate.room_id)
        room_blocked = resource_is_unavailable(room.unavailability_periods, candidate.date, candidate.start_time, candidate.end_time)
        if lecturer_blocked:
            availability_issues.append(OptimizationIssue("LECTURER_UNAVAILABLE", "The responsible lecturer is unavailable for the full exam interval.", candidate.date, "lecturer", lecturer.id))
        if room_blocked:
            availability_issues.append(OptimizationIssue("ROOM_UNAVAILABLE", "The room is unavailable for the full exam interval.", candidate.date, "room", room.id))
        if not lecturer_blocked and not room_blocked:
            filtered.append(candidate)
    if not filtered and not issues:
        issues = _unique_optimization_issues(availability_issues) or [OptimizationIssue("NO_VALID_EXAM_PLACEMENT", "No resource-available conflict-free placement is available.")]
    return filtered, issues


def _proposed_conflict_issues(candidates, selected_candidates):
    issues = []
    for candidate in candidates:
        for selected in selected_candidates:
            if candidate.course_id == selected.course_id or candidate.date != selected.date:
                continue
            if not intervals_overlap(
                datetime.combine(candidate.date, candidate.start_time),
                datetime.combine(candidate.date, candidate.end_time),
                datetime.combine(selected.date, selected.start_time),
                datetime.combine(selected.date, selected.end_time),
            ):
                continue
            if candidate.lecturer_id == selected.lecturer_id:
                issues.append(OptimizationIssue("LECTURER_OCCUPIED", "The responsible lecturer is used by another proposed exam.", candidate.date, "lecturer", candidate.lecturer_id))
            if candidate.room_id == selected.room_id:
                issues.append(OptimizationIssue("ROOM_OCCUPIED", "The room is used by another proposed exam.", candidate.date, "room", candidate.room_id))
            if candidate.cohort_id == selected.cohort_id:
                issues.append(OptimizationIssue("COHORT_OCCUPIED", "The cohort is used by another proposed exam.", candidate.date))
    return _unique_optimization_issues(issues)


def _unique_optimization_issues(issues):
    result = []
    seen = set()
    for issue in issues:
        key = (issue.code, issue.related_resource_kind, issue.related_resource_id)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def _optimization_issue_response(db, issue):
    resource = None
    if issue.related_resource_kind == "lecturer":
        row = db.get(Lecturer, issue.related_resource_id)
    elif issue.related_resource_kind == "room":
        row = db.get(Room, issue.related_resource_id)
    else:
        row = None
    if row is not None:
        resource = {"id": row.id, "name": row.name, "referenceCode": row.reference_code}
    holiday = db.scalar(select(InstitutionHoliday).where(InstitutionHoliday.date == issue.related_date)) if issue.code == "INSTITUTION_HOLIDAY" and issue.related_date else None
    return _issue(
        issue.code,
        issue.message,
        related_date=issue.related_date,
        related_resource=resource,
        meta={"relatedSessionId": issue.related_session_id, "holidayName": holiday.name if holiday else None},
    )


def _new_exam_row(db, course, config, anchor, exam_date, start_time, lecturer_id, room_id, source):
    lecturer, room = db.get(Lecturer, lecturer_id), db.get(Room, room_id)
    recommended_start, recommended_end = _recommendation(config, anchor)
    return ExamSession(course_id=course.id, semester_id=config.semester_id, cohort_id=course.cohort_id, lecturer_id=lecturer_id, room_id=room_id, exam_date=exam_date, start_time=start_time, end_time=_end_time(start_time, config.duration_minutes), source=source, revision=1, configuration_identifier=config.identifier, configuration_revision=config.revision, duration_minutes=config.duration_minutes, exam_type=config.exam_type, required_capacity=config.required_capacity, recommended_start_date=recommended_start, recommended_end_date=recommended_end, recommendation_was_overridden=config.recommended_start_override is not None, final_teaching_date=anchor["date"], final_teaching_end_time=anchor["endTime"], final_teaching_session_id_snapshot=anchor["teachingSessionId"], course_name_snapshot=course.name, semester_name_snapshot=config.semester.name, cohort_name_snapshot=course.cohort.name, lecturer_name_snapshot=lecturer.name, lecturer_reference_snapshot=lecturer.reference_code, room_name_snapshot=room.name, room_reference_snapshot=room.reference_code)


def _current_validity_issues(db, row):
    course, semester = row.course, row.semester
    anchor = _final_anchor(db, row.course_id, row.semester_id)
    if anchor is None: return [_issue("FINAL_TEACHING_SESSION_MISSING", "The final teaching session is no longer available.")]
    config = _configuration(db, row.course_id, row.semester_id)
    errors = _placement_errors(db, course, semester, config, row.exam_date, row.start_time, row.end_time, row.lecturer_id, row.room_id, anchor, row.id, required_capacity=row.required_capacity)
    return [_issue(item.code, item.message, related_date=row.exam_date, meta=item.meta) for item in errors]


def _eligibility(db, course, config, anchor, has_active):
    if config is None or not config.enabled: return {"eligible": False, "code": "DISABLED", "message": None}
    if has_active: return {"eligible": False, "code": "ACTIVE_EXAM_EXISTS", "message": "An active exam already exists."}
    if anchor is None: return {"eligible": False, "code": "FINAL_TEACHING_SESSION_MISSING", "message": "Save the final teaching session before generating an exam."}
    if config.configuration_consumed: return {"eligible": False, "code": "CONFIGURATION_CONSUMED", "message": "Save a fresh next-exam configuration."}
    lecturer = db.get(Lecturer, config.responsible_lecturer_id)
    if lecturer is None or not lecturer.is_active or db.get(CourseEligibleLecturer, (course.id, config.responsible_lecturer_id)) is None:
        return {"eligible": False, "code": "CONFIGURATION_INCOMPLETE", "message": "The responsible lecturer is no longer active and eligible."}
    if not any(window.is_active for window in course.study_type.time_windows): return {"eligible": False, "code": "AUTOMATIC_START_TIME_UNAVAILABLE", "message": "No active Study Type start time is available."}
    return {"eligible": True, "code": "ELIGIBLE", "message": None}


def _final_anchor(db, course_id, semester_id):
    row = db.execute(select(DraftSession).join(DraftSchedule).where(DraftSchedule.course_id == course_id, DraftSchedule.semester_id == semester_id).order_by(DraftSession.date.desc(), DraftSession.end_time.desc(), DraftSession.id.desc()).limit(1)).scalar_one_or_none()
    return {"date": row.date, "endTime": row.end_time, "teachingSessionId": row.id} if row else None


def _recommendation(config, anchor):
    if anchor is None: return None, None
    if config.recommended_start_override is not None: return config.recommended_start_override, config.recommended_end_override
    return anchor["date"] + timedelta(days=7), anchor["date"] + timedelta(days=14)


def _require_course_semester(db, course_id, semester_id):
    course, semester = db.get(Course, course_id), db.get(Semester, semester_id)
    if not course or not semester: raise ExamSchedulingError(404, [ExamErrorItem("NOT_FOUND", "Course or semester not found.")])
    if course.current_semester_id != semester_id: raise ExamSchedulingError(422, [ExamErrorItem("COURSE_NOT_IN_SEMESTER", "The course is not assigned to this semester.", "semesterId")])
    return course, semester


def _claim_semester(db, semester_id):
    value = db.execute(select(Semester.id).where(Semester.id == semester_id).with_for_update()).scalar_one_or_none()
    if value is None:
        raise ExamSchedulingError(404, [ExamErrorItem("NOT_FOUND", "Semester not found.")])


def _configuration(db, course_id, semester_id):
    return db.scalar(select(CourseExamConfiguration).where(CourseExamConfiguration.course_id == course_id, CourseExamConfiguration.semester_id == semester_id))


def _active_exam(db, course_id, semester_id, today, exclude_id=None):
    query = select(ExamSession).where(ExamSession.course_id == course_id, ExamSession.semester_id == semester_id, ExamSession.exam_date >= today).order_by(ExamSession.exam_date, ExamSession.id)
    if exclude_id is not None: query = query.where(ExamSession.id != exclude_id)
    return db.scalar(query.limit(1))


def _end_time(start, duration):
    end = datetime.combine(date(2000, 1, 1), start) + timedelta(minutes=duration)
    return None if end.date() != date(2000, 1, 1) else end.time()


def _fixed_occupancy(db, semester_id):
    for row in db.scalars(select(DraftSession).join(DraftSchedule).where(DraftSchedule.semester_id == semester_id)):
        yield Occupancy(row.date, row.start_time, row.end_time, row.lecturer_id, row.room_id, row.cohort_id, row.id)
    for row in db.scalars(select(ExamSession).where(ExamSession.semester_id == semester_id)):
        yield Occupancy(row.exam_date, row.start_time, row.end_time, row.lecturer_id, row.room_id, row.cohort_id, row.id)


def _exam_token(db, row):
    return _digest([row.id, row.revision, row.exam_date.isoformat(), str(row.start_time), str(row.end_time), row.lecturer_id, row.room_id, _holiday_material(db, row.semester), _resource_material(db, row.course), _final_anchor(db, row.course_id, row.semester_id)])


def _anchor_response(anchor):
    if anchor is None: return None
    return {**anchor, "endTime": anchor["endTime"]}


def _config_material(config):
    if config is None: return None
    return [config.id, config.revision, config.enabled, config.identifier, config.duration_minutes, str(config.recommended_start_override), str(config.recommended_end_override), config.required_capacity, config.exam_type, config.responsible_lecturer_id, config.configuration_consumed]


def _holiday_material(db, semester):
    return [(row.id, row.date.isoformat(), row.name, row.revision) for row in db.scalars(select(InstitutionHoliday).where(InstitutionHoliday.date.between(semester.start_date, semester.end_date)).order_by(InstitutionHoliday.date))]


def _resource_material(db, course):
    resources = [item.lecturer for item in course.eligible_lecturers] + [item.room for item in course.eligible_rooms]
    base = [[item.lecturer_id, item.lecturer.revision, item.lecturer.is_active] for item in course.eligible_lecturers] + [[item.room_id, item.room.revision, item.room.is_active, item.room.capacity] for item in course.eligible_rooms]
    availability = [[resource.id, type(resource).__name__, [(period.id, period.revision, period.kind, str(period.start_date), str(period.end_date), str(period.start_time), str(period.end_time), [weekday.weekday for weekday in period.weekdays]) for period in resource.unavailability_periods]] for resource in resources]
    return [base, availability]


def _semester_occupancy_material(db, semester_id):
    teaching = [(row.id, row.date.isoformat(), str(row.start_time), str(row.end_time), row.lecturer_id, row.room_id, row.cohort_id) for row in db.scalars(select(DraftSession).join(DraftSchedule).where(DraftSchedule.semester_id == semester_id).order_by(DraftSession.id))]
    exams = [(row.id, row.revision, row.exam_date.isoformat(), str(row.start_time), str(row.end_time), row.lecturer_id, row.room_id, row.cohort_id) for row in db.scalars(select(ExamSession).where(ExamSession.semester_id == semester_id).order_by(ExamSession.id))]
    return [teaching, exams]


def _outcome_base(course, config):
    return {"courseId": course.id, "courseName": course.name, "configurationId": config.id if config else None, "configurationIdentifier": config.identifier if config else None}


def _issue(code, message, related_date=None, meta=None, related_resource=None):
    return {"code": code, "message": message, "relatedDate": related_date, "relatedResource": related_resource, "relatedSessionId": (meta or {}).get("relatedSessionId"), "holidayName": (meta or {}).get("holidayName")}


def _unique_errors(errors):
    seen = set()
    result = []
    for item in errors:
        key = (item.code, item.field, json.dumps(item.meta, sort_keys=True))
        if key not in seen:
            seen.add(key); result.append(item)
    return result


def _digest(value):
    return hashlib.sha256(json.dumps(value, default=str, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
