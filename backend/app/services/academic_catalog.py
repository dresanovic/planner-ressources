from dataclasses import dataclass
from datetime import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    DraftSession,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)
from app.services.resource_catalog import validate_course_resource_candidates


@dataclass(frozen=True)
class CatalogErrorItem:
    code: str
    message: str
    field: str | None = None
    meta: dict | None = None


class AcademicCatalogError(ValueError):
    def __init__(self, status_code: int, errors: list[CatalogErrorItem]):
        super().__init__(errors[0].message if errors else "Academic catalog error.")
        self.status_code = status_code
        self.errors = errors


def normalize_name(value: str) -> str:
    return value.strip().casefold()


def validate_course_units(total: int, minimum: int, maximum: int) -> None:
    errors: list[CatalogErrorItem] = []
    for field, value in (
        ("totalUnits", total),
        ("minSessionUnits", minimum),
        ("maxSessionUnits", maximum),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(CatalogErrorItem("VALIDATION_ERROR", "Enter a positive whole number.", field))
    if not errors and minimum > maximum:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Minimum session units cannot exceed maximum session units.", "minSessionUnits"))
    if not errors and maximum > total:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Maximum session units cannot exceed total units.", "maxSessionUnits"))
    if errors:
        raise AcademicCatalogError(422, errors)


def course_availability_reasons(
    *,
    course_active: bool,
    semester_assigned: bool,
    semester_active: bool,
    cohort_active: bool,
    study_type_active: bool,
    has_active_window: bool,
    resources_valid: bool,
) -> list[str]:
    reasons: list[str] = []
    if not course_active:
        reasons.append("RECORD_INACTIVE")
    if not semester_assigned:
        reasons.append("SEMESTER_ASSIGNMENT_REQUIRED")
    elif not semester_active:
        reasons.append("SEMESTER_INACTIVE")
    if not cohort_active:
        reasons.append("COHORT_INACTIVE")
    if not study_type_active:
        reasons.append("STUDY_TYPE_INACTIVE")
    if not has_active_window:
        reasons.append("MISSING_ACTIVE_TIME_WINDOW")
    if not resources_valid:
        reasons.append("RESOURCE_RELATIONSHIP_INVALID")
    return reasons


NAMED_MODELS = (Semester, Cohort, Course, StudyType)


def validate_and_prepare_name(db: Session, model, value: str, *, exclude_id: int | None = None) -> tuple[str, str]:
    display = value.strip()
    errors: list[CatalogErrorItem] = []
    if not display:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Enter a name.", "name"))
    elif len(display) > 200:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Name cannot exceed 200 characters.", "name"))
    canonical = normalize_name(display)
    if display:
        candidates = db.execute(select(model.id, model.name)).all()
        duplicate = next((row for row in candidates if row.id != exclude_id and normalize_name(row.name) == canonical), None)
        if duplicate is not None:
            raise AcademicCatalogError(409, [CatalogErrorItem(
                "DUPLICATE_NORMALIZED_NAME",
                f"Another {model.__name__} already uses this name.",
                "name",
                {"conflictingRecordId": duplicate.id},
            )])
    if errors:
        raise AcademicCatalogError(422, errors)
    return display, canonical


def create_semester(db: Session, *, name: str, start_date, end_date) -> Semester:
    display = name.strip()
    errors: list[CatalogErrorItem] = []
    if not display:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Enter a name.", "name"))
        canonical = ""
    else:
        display, canonical = validate_and_prepare_name(db, Semester, name)
    if end_date < start_date:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "End date cannot be earlier than start date.", "endDate"))
    if errors:
        raise AcademicCatalogError(422, errors)
    row = Semester(name=display, normalized_name=canonical, normalized_name_key=canonical, start_date=start_date, end_date=end_date)
    db.add(row)
    db.flush()
    return row


def create_cohort(db: Session, *, name: str, student_count: int) -> Cohort:
    errors = []
    if not isinstance(student_count, int) or isinstance(student_count, bool) or student_count <= 0:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Enter a positive whole number.", "studentCount"))
    name_status = 422
    try:
        display, canonical = validate_and_prepare_name(db, Cohort, name)
    except AcademicCatalogError as exc:
        display, canonical = "", ""
        name_status = exc.status_code
        errors.extend(exc.errors)
    if errors:
        raise AcademicCatalogError(name_status if len(errors) == 1 else 422, errors)
    row = Cohort(name=display, normalized_name=canonical, normalized_name_key=canonical, student_count=student_count)
    db.add(row)
    db.flush()
    return row


def create_study_type(db: Session, *, name: str) -> StudyType:
    display, canonical = validate_and_prepare_name(db, StudyType, name)
    row = StudyType(name=display, normalized_name=canonical, normalized_name_key=canonical)
    db.add(row)
    db.flush()
    return row


def parse_time(value: str, field: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise AcademicCatalogError(422, [CatalogErrorItem("VALIDATION_ERROR", "Enter a valid HH:MM time.", field)]) from exc


def create_time_window(db: Session, study_type_id: int, *, weekday: int, start_time: str, end_time: str, sort_order: int) -> StudyTypeTimeWindow:
    owner = db.get(StudyType, study_type_id)
    if owner is None:
        raise AcademicCatalogError(404, [CatalogErrorItem("NOT_FOUND", "Study Type not found.")])
    errors = []
    start = end = None
    for value, field in ((start_time, "startTime"), (end_time, "endTime")):
        try:
            parsed = parse_time(value, field)
            if field == "startTime":
                start = parsed
            else:
                end = parsed
        except AcademicCatalogError as exc:
            errors.extend(exc.errors)
    if weekday < 0 or weekday > 6:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Weekday must be between 0 and 6.", "weekday"))
    if start is not None and end is not None and end <= start:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "End time must be later than start time.", "endTime"))
    if sort_order < 0:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Sort order cannot be negative.", "sortOrder"))
    if errors:
        raise AcademicCatalogError(422, errors)
    duplicate = db.execute(select(StudyTypeTimeWindow.id).where(
        StudyTypeTimeWindow.study_type_id == study_type_id,
        StudyTypeTimeWindow.weekday == weekday,
        StudyTypeTimeWindow.start_time == start,
        StudyTypeTimeWindow.end_time == end,
    )).scalar_one_or_none()
    if duplicate is not None:
        raise AcademicCatalogError(409, [CatalogErrorItem("DUPLICATE_TIME_WINDOW", "This exact weekly window already exists.", None, {"conflictingRecordId": duplicate})])
    row = StudyTypeTimeWindow(study_type_id=study_type_id, weekday=weekday, start_time=start, end_time=end, sort_order=sort_order)
    db.add(row)
    db.flush()
    return row


def create_course(db: Session, *, name: str, total_units: int, min_session_units: int, max_session_units: int, semester_id: int, cohort_id: int, study_type_id: int, lecturer_id: int, room_id: int) -> Course:
    errors: list[CatalogErrorItem] = []
    name_status = 422
    try:
        validate_course_units(total_units, min_session_units, max_session_units)
    except AcademicCatalogError as exc:
        errors.extend(exc.errors)
    try:
        display, canonical = validate_and_prepare_name(db, Course, name)
    except AcademicCatalogError as exc:
        display, canonical = "", ""
        name_status = exc.status_code
        errors.extend(exc.errors)
    relationships = (
        (Semester, semester_id, "semesterId", "Semester"),
        (Cohort, cohort_id, "cohortId", "Cohort"),
        (StudyType, study_type_id, "studyTypeId", "Study Type"),
    )
    errors.extend(CatalogErrorItem("REQUIRED_RELATIONSHIP_INVALID", f"{label} does not exist.", field) for model, record_id, field, label in relationships if db.get(model, record_id) is None)
    cohort = db.get(Cohort, cohort_id)
    resource_errors = validate_course_resource_candidates(
        db,
        cohort_size=cohort.student_count if cohort is not None else 0,
        lecturer_ids=[lecturer_id],
        room_ids=[room_id],
    )
    resource_fields = {"lecturerIds": "lecturerId", "roomIds": "roomId"}
    errors.extend(CatalogErrorItem(item.code, item.message, resource_fields.get(item.field, item.field), item.meta) for item in resource_errors)
    if errors:
        raise AcademicCatalogError(name_status if len(errors) == 1 else 422, errors)
    row = Course(
        name=display, normalized_name=canonical, normalized_name_key=canonical,
        total_units=total_units, min_session_units=min_session_units, max_session_units=max_session_units,
        current_semester_id=semester_id, cohort_id=cohort_id, study_type_id=study_type_id,
        eligible_lecturers=[CourseEligibleLecturer(lecturer_id=lecturer_id)],
        eligible_rooms=[CourseEligibleRoom(room_id=room_id)],
    )
    db.add(row)
    db.flush()
    return row


def list_records(db: Session, model, *, page: int = 1, page_size: int = 50, status: str = "all", query: str | None = None, options=(), extra_filters=()) -> tuple[list, int]:
    statement = select(model)
    count_statement = select(func.count()).select_from(model)
    filters = list(extra_filters)
    if status == "active":
        filters.append(model.is_active.is_(True))
    elif status == "inactive":
        filters.append(model.is_active.is_(False))
    if query and hasattr(model, "name"):
        filters.append(func.lower(model.name).contains(query.strip().lower()))
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    if options:
        statement = statement.options(*options)
    order = [model.name, model.id] if hasattr(model, "name") else [model.id]
    if model is Semester:
        order = [Semester.start_date, Semester.name, Semester.id]
    statement = statement.order_by(*order).offset((page - 1) * page_size).limit(page_size)
    return list(db.execute(statement).scalars().all()), db.execute(count_statement).scalar_one()


def availability_for_course(
    db: Session,
    course: Course,
    *,
    active_window_study_type_ids: set[int] | None = None,
) -> list[str]:
    has_window = (
        course.study_type_id in active_window_study_type_ids
        if active_window_study_type_ids is not None
        else db.execute(select(StudyTypeTimeWindow.id).where(
            StudyTypeTimeWindow.study_type_id == course.study_type_id,
            StudyTypeTimeWindow.is_active.is_(True),
        ).limit(1)).first() is not None
    )
    reasons = course_availability_reasons(
        course_active=course.is_active,
        semester_assigned=course.current_semester is not None,
        semester_active=bool(course.current_semester and course.current_semester.is_active),
        cohort_active=course.cohort.is_active,
        study_type_active=course.study_type.is_active,
        has_active_window=has_window,
        resources_valid=True,
    )
    if not any(link.lecturer.is_active for link in course.eligible_lecturers):
        reasons.append("NO_ACTIVE_ELIGIBLE_LECTURER")
    if not any(link.room.is_active and link.room.capacity >= course.cohort.student_count for link in course.eligible_rooms):
        reasons.append("NO_USABLE_ELIGIBLE_ROOM")
    return reasons


def planning_eligibility_reasons(db: Session, course: Course, semester_id: int) -> list[str]:
    reasons = availability_for_course(db, course)
    if course.current_semester_id is not None and course.current_semester_id != semester_id:
        reasons.append("COURSE_SEMESTER_MISMATCH")
    return reasons


def require_record(db: Session, model, record_id: int):
    row = db.get(model, record_id)
    if row is None:
        raise AcademicCatalogError(404, [CatalogErrorItem("NOT_FOUND", f"{model.__name__} not found.")])
    return row


def require_revision(row, expected_revision: int) -> None:
    if row.revision != expected_revision:
        raise AcademicCatalogError(409, [CatalogErrorItem(
            "STALE_REVISION", "This record changed. Refresh and review the current values.",
            None, {"expectedRevision": expected_revision, "currentRevision": row.revision},
        )])


def _count(db: Session, statement) -> int:
    return int(db.execute(statement).scalar_one())


def usage_for(db: Session, row) -> dict:
    dependent: list[dict] = []
    saved_count = 0
    if isinstance(row, Semester):
        course_count = _count(db, select(func.count()).select_from(Course).where(Course.current_semester_id == row.id))
        constraint_count = _count(db, select(func.count()).select_from(GenerationConstraintSet).where(GenerationConstraintSet.semester_id == row.id))
        saved_count = _count(db, select(func.count()).select_from(DraftSchedule).where(DraftSchedule.semester_id == row.id))
        dependent.extend(({"type": "course", "count": course_count}, {"type": "generation_constraint_set", "count": constraint_count}))
    elif isinstance(row, Cohort):
        course_count = _count(db, select(func.count()).select_from(Course).where(Course.cohort_id == row.id))
        saved_count = _count(db, select(func.count()).select_from(DraftSchedule).where(DraftSchedule.cohort_id_snapshot == row.id))
        dependent.append({"type": "course", "count": course_count})
    elif isinstance(row, Course):
        constraint_count = _count(db, select(func.count()).select_from(GenerationConstraintSet).where(GenerationConstraintSet.course_id == row.id))
        saved_count = _count(db, select(func.count()).select_from(DraftSchedule).where(DraftSchedule.course_id == row.id))
        dependent.append({"type": "generation_constraint_set", "count": constraint_count})
    elif isinstance(row, StudyType):
        course_count = _count(db, select(func.count()).select_from(Course).where(Course.study_type_id == row.id))
        window_count = _count(db, select(func.count()).select_from(StudyTypeTimeWindow).where(StudyTypeTimeWindow.study_type_id == row.id))
        saved_count = _count(db, select(func.count()).select_from(DraftSchedule).where(DraftSchedule.study_type_id_snapshot == row.id))
        dependent.extend(({"type": "course", "count": course_count}, {"type": "time_window", "count": window_count}))
    elif isinstance(row, StudyTypeTimeWindow):
        constraint_count = _count(db, select(func.count()).select_from(GenerationConstraintWindow).where(GenerationConstraintWindow.source_time_window_id == row.id))
        dependent.append({"type": "generation_constraint_window", "count": constraint_count})
        selected_schedule_ids = set(db.execute(select(DraftSchedule.id).where(DraftSchedule.selected_time_window_id == row.id)).scalars())
        session_schedule_ids = set(db.execute(select(DraftSession.draft_schedule_id).where(DraftSession.time_window_id == row.id)).scalars())
        saved_count = len(selected_schedule_ids | session_schedule_ids)
    dependent = [item for item in dependent if item["count"]]
    blockers = [
        {"kind": "dependent", "type": item["type"], "count": item["count"], "message": f"Used by {item['count']} {item['type']} record(s).", "prerequisiteAction": "Remove or reassign dependent records first."}
        for item in dependent
    ]
    if saved_count:
        blockers.append({"kind": "saved_schedule", "type": "draft_schedule", "count": saved_count, "message": f"Referenced by {saved_count} saved schedule(s).", "prerequisiteAction": None})
    return {"recordId": row.id, "revision": row.revision, "canDelete": not blockers, "dependentRecords": dependent, "savedSchedules": {"type": "draft_schedule", "count": saved_count}, "blockers": blockers}


def update_semester(db: Session, row: Semester, *, name: str, start_date, end_date, expected_revision: int) -> Semester:
    require_revision(row, expected_revision)
    display, canonical = validate_and_prepare_name(db, Semester, name, exclude_id=row.id)
    errors = []
    if end_date < start_date:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "End date cannot be earlier than start date.", "endDate"))
    outside = db.execute(select(DraftSession.date).join(DraftSchedule).where(DraftSchedule.semester_id == row.id, (DraftSession.date < start_date) | (DraftSession.date > end_date)).limit(1)).scalar_one_or_none()
    if outside is not None:
        errors.append(CatalogErrorItem("SAVED_SESSION_OUTSIDE_SEMESTER", "Saved sessions must remain inside the Semester dates.", "startDate", {"sessionDate": outside.isoformat()}))
    if errors:
        raise AcademicCatalogError(422, errors)
    row.name, row.normalized_name, row.normalized_name_key = display, canonical, canonical
    row.name_repair_required = False
    row.start_date, row.end_date, row.revision = start_date, end_date, row.revision + 1
    db.flush(); return row


def update_cohort(db: Session, row: Cohort, *, name: str, student_count: int, expected_revision: int) -> Cohort:
    require_revision(row, expected_revision)
    errors = []
    if not isinstance(student_count, int) or isinstance(student_count, bool) or student_count <= 0:
        errors.append(CatalogErrorItem("VALIDATION_ERROR", "Enter a positive whole number.", "studentCount"))
    name_status = 422
    try:
        display, canonical = validate_and_prepare_name(db, Cohort, name, exclude_id=row.id)
    except AcademicCatalogError as exc:
        display, canonical = "", ""
        name_status = exc.status_code
        errors.extend(exc.errors)
    if errors:
        raise AcademicCatalogError(name_status if len(errors) == 1 else 422, errors)
    row.name, row.normalized_name, row.normalized_name_key = display, canonical, canonical
    row.name_repair_required = False
    row.student_count, row.revision = student_count, row.revision + 1
    db.flush(); return row


def update_cohort_with_capacity_impact(db: Session, row: Cohort, *, name: str, student_count: int, expected_revision: int) -> tuple[Cohort, dict]:
    previous_count = row.student_count
    updated = update_cohort(db, row, name=name, student_count=student_count, expected_revision=expected_revision)
    removed: list[dict] = []
    courses_without_rooms: list[dict] = []
    if student_count > previous_count:
        courses = db.execute(
            select(Course)
            .where(Course.cohort_id == row.id)
            .options(selectinload(Course.eligible_rooms).selectinload(CourseEligibleRoom.room))
            .order_by(Course.id)
        ).scalars().all()
        for course in courses:
            insufficient = [link for link in course.eligible_rooms if link.room.capacity < student_count]
            if not insufficient:
                continue
            for link in insufficient:
                removed.append({"courseId": course.id, "roomId": link.room_id, "courseRevision": course.revision + 1})
                course.eligible_rooms.remove(link)
            course.revision += 1
            if not course.eligible_rooms:
                courses_without_rooms.append({"id": course.id, "name": course.name})
        db.flush()
    return updated, {"removedRelationships": removed, "coursesWithoutRooms": courses_without_rooms}


def update_study_type(db: Session, row: StudyType, *, name: str, expected_revision: int) -> StudyType:
    require_revision(row, expected_revision)
    display, canonical = validate_and_prepare_name(db, StudyType, name, exclude_id=row.id)
    row.name, row.normalized_name, row.normalized_name_key = display, canonical, canonical
    row.name_repair_required = False; row.revision += 1
    db.flush(); return row


def update_time_window(db: Session, row: StudyTypeTimeWindow, *, weekday: int, start_time: str, end_time: str, sort_order: int, expected_revision: int) -> StudyTypeTimeWindow:
    require_revision(row, expected_revision)
    errors = []
    start = end = None
    for value, field in ((start_time, "startTime"), (end_time, "endTime")):
        try:
            parsed = parse_time(value, field)
            if field == "startTime": start = parsed
            else: end = parsed
        except AcademicCatalogError as exc:
            errors.extend(exc.errors)
    if weekday < 0 or weekday > 6: errors.append(CatalogErrorItem("VALIDATION_ERROR", "Weekday must be between 0 and 6.", "weekday"))
    if start is not None and end is not None and end <= start: errors.append(CatalogErrorItem("VALIDATION_ERROR", "End time must be later than start time.", "endTime"))
    if sort_order < 0: errors.append(CatalogErrorItem("VALIDATION_ERROR", "Sort order cannot be negative.", "sortOrder"))
    if errors: raise AcademicCatalogError(422, errors)
    duplicate = db.execute(select(StudyTypeTimeWindow.id).where(StudyTypeTimeWindow.study_type_id == row.study_type_id, StudyTypeTimeWindow.weekday == weekday, StudyTypeTimeWindow.start_time == start, StudyTypeTimeWindow.end_time == end, StudyTypeTimeWindow.id != row.id)).scalar_one_or_none()
    if duplicate is not None: raise AcademicCatalogError(409, [CatalogErrorItem("DUPLICATE_TIME_WINDOW", "This exact weekly window already exists.", None, {"conflictingRecordId": duplicate})])
    row.weekday, row.start_time, row.end_time, row.sort_order = weekday, start, end, sort_order
    row.revision += 1; db.flush(); return row


def update_course(db: Session, row: Course, *, name: str, total_units: int, min_session_units: int, max_session_units: int, semester_id: int, cohort_id: int, study_type_id: int, expected_revision: int) -> Course:
    require_revision(row, expected_revision)
    errors: list[CatalogErrorItem] = []
    name_status = 422
    try:
        validate_course_units(total_units, min_session_units, max_session_units)
    except AcademicCatalogError as exc:
        errors.extend(exc.errors)
    try:
        display, canonical = validate_and_prepare_name(db, Course, name, exclude_id=row.id)
    except AcademicCatalogError as exc:
        display, canonical = "", ""
        name_status = exc.status_code
        errors.extend(exc.errors)
    relationships = ((Semester, semester_id, "semesterId", "Semester"), (Cohort, cohort_id, "cohortId", "Cohort"), (StudyType, study_type_id, "studyTypeId", "Study Type"))
    errors.extend(CatalogErrorItem("REQUIRED_RELATIONSHIP_INVALID", f"{label} does not exist.", field) for model, record_id, field, label in relationships if db.get(model, record_id) is None)
    if errors: raise AcademicCatalogError(name_status if len(errors) == 1 else 422, errors)
    row.name, row.normalized_name, row.normalized_name_key = display, canonical, canonical
    row.name_repair_required = False
    row.total_units, row.min_session_units, row.max_session_units = total_units, min_session_units, max_session_units
    row.current_semester_id, row.cohort_id, row.study_type_id = semester_id, cohort_id, study_type_id
    row.revision += 1; db.flush(); return row


def set_lifecycle(db: Session, row, *, active: bool, expected_revision: int):
    require_revision(row, expected_revision)
    if active and getattr(row, "name_repair_required", False):
        raise AcademicCatalogError(409, [CatalogErrorItem("NAME_REPAIR_REQUIRED", "Rename this record to a unique name before reactivation.", "name")])
    if active and isinstance(row, Course):
        reasons = availability_for_course(db, row)
        blocking = [reason for reason in reasons if reason != "RECORD_INACTIVE" and reason != "MISSING_ACTIVE_TIME_WINDOW"]
        if blocking: raise AcademicCatalogError(409, [CatalogErrorItem("REACTIVATION_BLOCKED", "Required relationships must be active before reactivation.", None, {"reasons": blocking})])
    if active and isinstance(row, StudyTypeTimeWindow) and not row.study_type.is_active:
        raise AcademicCatalogError(409, [CatalogErrorItem("REACTIVATION_BLOCKED", "Reactivate the Study Type first.")])
    row.is_active = active; row.revision += 1; db.flush(); return row


def delete_record(db: Session, row, *, expected_revision: int) -> None:
    require_revision(row, expected_revision)
    usage = usage_for(db, row)
    if not usage["canDelete"]:
        raise AcademicCatalogError(409, [CatalogErrorItem("DELETE_PROTECTED", "This record is still referenced and cannot be deleted.", None, {"usage": usage})])
    db.delete(row); db.flush()
