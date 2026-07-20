from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from datetime import date, datetime, time

from app.models.planning import (
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSession,
    ExamSession,
    CourseExamConfiguration,
    Lecturer,
    Room,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
)


@dataclass(frozen=True)
class ResourceErrorItem:
    code: str
    message: str
    field: str | None = None
    meta: dict | None = None


class ResourceCatalogError(ValueError):
    def __init__(self, status_code: int, errors: list[ResourceErrorItem]):
        super().__init__(errors[0].message if errors else "Resource catalog error.")
        self.status_code = status_code
        self.errors = errors


def normalize_reference_code(value: str) -> str:
    return value.strip().casefold()


def _validate_fields(
    *,
    name: str,
    reference_code: str,
    capacity: int | None,
    room: bool,
) -> tuple[str, str, int | None]:
    display_name = name.strip()
    display_code = reference_code.strip()
    errors: list[ResourceErrorItem] = []
    if not display_name:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a name.", "name"))
    elif len(display_name) > 200:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Name cannot exceed 200 characters.", "name"))
    if not display_code:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a reference code.", "referenceCode"))
    elif len(display_code) > 100:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Reference code cannot exceed 100 characters.", "referenceCode"))
    if room and (
        not isinstance(capacity, int)
        or isinstance(capacity, bool)
        or capacity <= 0
    ):
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a positive whole-number capacity.", "capacity"))
    if errors:
        raise ResourceCatalogError(422, errors)
    return display_name, display_code, capacity


def _require_supported_model(model):
    if model not in (Lecturer, Room):
        raise TypeError("Resource model must be Lecturer or Room.")


def _ensure_unique_code(
    db: Session,
    model,
    normalized_code: str,
    *,
    exclude_id: int | None = None,
) -> None:
    statement = select(model.id).where(model.normalized_reference_code == normalized_code)
    if exclude_id is not None:
        statement = statement.where(model.id != exclude_id)
    conflict = db.execute(statement.limit(1)).scalar_one_or_none()
    if conflict is not None:
        raise ResourceCatalogError(
            409,
            [
                ResourceErrorItem(
                    "DUPLICATE_REFERENCE_CODE",
                    f"Another {model.__name__} already uses this reference code.",
                    "referenceCode",
                    {"conflictingResourceId": conflict},
                )
            ],
        )


def create_resource(
    db: Session,
    model,
    *,
    name: str,
    reference_code: str,
    capacity: int | None = None,
):
    _require_supported_model(model)
    display_name, display_code, capacity = _validate_fields(
        name=name,
        reference_code=reference_code,
        capacity=capacity,
        room=model is Room,
    )
    normalized_code = normalize_reference_code(display_code)
    _ensure_unique_code(db, model, normalized_code)
    values = {
        "name": display_name,
        "reference_code": display_code,
        "normalized_reference_code": normalized_code,
    }
    if model is Room:
        values["capacity"] = capacity
    row = model(**values)
    db.add(row)
    db.flush()
    return row, []


def list_resources(
    db: Session,
    model,
    *,
    status: str = "active",
    query: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    _require_supported_model(model)
    filters = []
    if status == "active":
        filters.append(model.is_active.is_(True))
    elif status == "inactive":
        filters.append(model.is_active.is_(False))
    elif status != "all":
        raise ResourceCatalogError(422, [ResourceErrorItem("VALIDATION_ERROR", "Unknown resource status.", "status")])
    if query and query.strip():
        needle = query.strip().casefold()
        filters.append(
            or_(
                func.lower(model.name).contains(needle),
                model.normalized_reference_code.contains(needle),
            )
        )
    statement = select(model).where(*filters).order_by(model.name, model.normalized_reference_code, model.id)
    count = select(func.count()).select_from(model).where(*filters)
    rows = db.execute(statement.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return list(rows), int(db.execute(count).scalar_one())


def require_resource(db: Session, model, resource_id: int):
    _require_supported_model(model)
    row = db.get(model, resource_id)
    if row is None:
        raise ResourceCatalogError(404, [ResourceErrorItem("NOT_FOUND", f"{model.__name__} not found.")])
    return row


def require_resource_revision(row, expected_revision: int) -> None:
    if row.revision != expected_revision:
        raise ResourceCatalogError(
            409,
            [
                ResourceErrorItem(
                    "STALE_REVISION",
                    "This resource changed. Refresh and review the current values.",
                    None,
                    {"expectedRevision": expected_revision, "currentRevision": row.revision},
                )
            ],
        )


def _relationship_statuses(db: Session, row) -> list[dict]:
    junction = CourseEligibleLecturer if isinstance(row, Lecturer) else CourseEligibleRoom
    resource_column = junction.lecturer_id if isinstance(row, Lecturer) else junction.room_id
    courses = db.execute(
        select(Course)
        .join(junction, junction.course_id == Course.id)
        .where(resource_column == row.id)
        .order_by(Course.name, Course.id)
    ).scalars().all()
    statuses: list[dict] = []
    for course in courses:
        reasons = []
        if not course.is_active:
            reasons.append("COURSE_INACTIVE")
        if not row.is_active:
            reasons.append("RESOURCE_INACTIVE")
        if isinstance(row, Room) and row.capacity < course.cohort.student_count:
            reasons.append("INSUFFICIENT_CAPACITY")
        statuses.append(
            {
                "course": {"id": course.id, "name": course.name},
                "resourceId": row.id,
                "usable": not reasons,
                "reasons": reasons,
            }
        )
    return statuses


def update_resource(
    db: Session,
    row,
    *,
    name: str,
    reference_code: str,
    expected_revision: int,
    capacity: int | None = None,
):
    require_resource_revision(row, expected_revision)
    display_name, display_code, capacity = _validate_fields(
        name=name,
        reference_code=reference_code,
        capacity=capacity,
        room=isinstance(row, Room),
    )
    normalized_code = normalize_reference_code(display_code)
    _ensure_unique_code(db, type(row), normalized_code, exclude_id=row.id)
    capacity_changed = isinstance(row, Room) and row.capacity != capacity
    row.name = display_name
    row.reference_code = display_code
    row.normalized_reference_code = normalized_code
    if isinstance(row, Room):
        row.capacity = capacity
    row.revision += 1
    db.flush()
    return row, _relationship_statuses(db, row) if capacity_changed else []


def _course_identities(db: Session, row, *, active: bool) -> list[dict]:
    junction = CourseEligibleLecturer if isinstance(row, Lecturer) else CourseEligibleRoom
    resource_column = junction.lecturer_id if isinstance(row, Lecturer) else junction.room_id
    courses = db.execute(
        select(Course)
        .join(junction, junction.course_id == Course.id)
        .where(resource_column == row.id, Course.is_active.is_(active))
        .order_by(Course.name, Course.id)
    ).scalars().all()
    return [{"id": course.id, "name": course.name} for course in courses]


def assess_resource_usage(db: Session, row) -> dict:
    active_courses = _course_identities(db, row, active=True)
    inactive_courses = _course_identities(db, row, active=False)
    resource_column = DraftSession.lecturer_id if isinstance(row, Lecturer) else DraftSession.room_id
    draft_session_count = int(
        db.execute(select(func.count()).select_from(DraftSession).where(resource_column == row.id)).scalar_one()
    )
    draft_schedule_count = int(
        db.execute(select(func.count(func.distinct(DraftSession.draft_schedule_id))).where(resource_column == row.id)).scalar_one()
    )
    exam_column = ExamSession.lecturer_id if isinstance(row, Lecturer) else ExamSession.room_id
    exam_session_count = int(
        db.execute(select(func.count()).select_from(ExamSession).where(exam_column == row.id)).scalar_one()
    )
    configured_count = 0
    if isinstance(row, Lecturer):
        configured_count = int(db.execute(select(func.count()).select_from(CourseExamConfiguration).where(CourseExamConfiguration.responsible_lecturer_id == row.id, CourseExamConfiguration.enabled.is_(True))).scalar_one())
    return {
        "resourceId": row.id,
        "revision": row.revision,
        "disposition": "inactivate" if active_courses or draft_session_count or exam_session_count or configured_count else "delete",
        "activeCourses": active_courses,
        "inactiveCourses": inactive_courses,
        "sessionUsage": {
            "draftSessionCount": draft_session_count,
            "draftScheduleCount": draft_schedule_count,
        },
        "examUsage": {"examSessionCount": exam_session_count, "currentConfigurationCount": configured_count},
    }


def remove_resource(
    db: Session,
    row,
    *,
    expected_revision: int,
    confirmed: bool,
) -> dict:
    require_resource_revision(row, expected_revision)
    if not confirmed:
        raise ResourceCatalogError(409, [ResourceErrorItem("CONFIRMATION_REQUIRED", "Confirm resource removal before continuing.", "confirmed")])
    usage = assess_resource_usage(db, row)
    if usage["disposition"] == "delete":
        resource_id = row.id
        inactive_courses = usage["inactiveCourses"]
        db.delete(row)
        db.flush()
        return {
            "outcome": "deleted",
            "resourceId": resource_id,
            "removedInactiveCourseLinks": inactive_courses,
        }
    row.is_active = False
    row.revision += 1
    db.flush()
    return {
        "outcome": "inactivated",
        "resource": row,
        "activeCourses": usage["activeCourses"],
        "sessionUsage": usage["sessionUsage"],
        "examUsage": usage["examUsage"],
    }


def reactivate_resource(db: Session, row, *, expected_revision: int) -> dict:
    require_resource_revision(row, expected_revision)
    _validate_fields(
        name=row.name,
        reference_code=row.reference_code,
        capacity=row.capacity if isinstance(row, Room) else None,
        room=isinstance(row, Room),
    )
    _ensure_unique_code(db, type(row), row.normalized_reference_code, exclude_id=row.id)
    row.is_active = True
    row.revision += 1
    db.flush()
    statuses = _relationship_statuses(db, row)
    return {
        "resource": row,
        "restoredRelationships": [item["course"] for item in statuses if item["usable"]],
        "unusableRelationships": [item for item in statuses if not item["usable"]],
    }


def _parse_date(value: str | None, field: str, errors: list[ResourceErrorItem]) -> date | None:
    if value is None:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a date.", field))
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a valid date.", field))
        return None


def _parse_time(value: str | None, field: str, errors: list[ResourceErrorItem]) -> time | None:
    if value is None:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a time.", field))
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Enter a valid time.", field))
        return None


def _canonical_unavailability(
    *,
    kind: str,
    weekdays: list[int] | None = None,
    start_date_value: str | None = None,
    end_date_value: str | None = None,
    start_time_value: str | None = None,
    end_time_value: str | None = None,
) -> dict:
    errors: list[ResourceErrorItem] = []
    start = _parse_time(start_time_value, "startTime", errors)
    end = _parse_time(end_time_value, "endTime", errors)
    if kind == "recurring":
        canonical_weekdays = sorted(set(weekdays or []))
        if not canonical_weekdays or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 6 for value in canonical_weekdays):
            errors.append(ResourceErrorItem("VALIDATION_ERROR", "Select at least one valid weekday.", "weekdays"))
        if start is not None and end is not None and end <= start:
            errors.append(ResourceErrorItem("VALIDATION_ERROR", "End time must be later than start time.", "endTime"))
        result = {"kind": kind, "weekdays": canonical_weekdays, "start_date": None, "end_date": None, "start_time": start, "end_time": end}
    elif kind == "dated":
        start_date = _parse_date(start_date_value, "startDate", errors)
        end_date = _parse_date(end_date_value, "endDate", errors)
        if start_date is not None and end_date is not None and start is not None and end is not None and datetime.combine(end_date, end) <= datetime.combine(start_date, start):
            errors.append(ResourceErrorItem("VALIDATION_ERROR", "End date and time must be later than the start.", "endTime"))
        result = {"kind": kind, "weekdays": [], "start_date": start_date, "end_date": end_date, "start_time": start, "end_time": end}
    else:
        errors.append(ResourceErrorItem("VALIDATION_ERROR", "Kind must be recurring or dated.", "kind"))
        result = {"kind": kind, "weekdays": [], "start_date": None, "end_date": None, "start_time": start, "end_time": end}
    if errors:
        raise ResourceCatalogError(422, errors)
    return result


def _unavailability_signature(period: ResourceUnavailabilityPeriod) -> tuple:
    owner = ("lecturer", period.lecturer_id) if period.lecturer_id is not None else ("room", period.room_id)
    if period.kind == "recurring":
        return owner + (period.kind, tuple(item.weekday for item in period.weekdays), period.start_time, period.end_time)
    return owner + (period.kind, period.start_date, period.start_time, period.end_date, period.end_time)


def list_unavailability(db: Session, row) -> list[ResourceUnavailabilityPeriod]:
    owner_filter = ResourceUnavailabilityPeriod.lecturer_id == row.id if isinstance(row, Lecturer) else ResourceUnavailabilityPeriod.room_id == row.id
    return list(db.execute(select(ResourceUnavailabilityPeriod).where(owner_filter).options(selectinload(ResourceUnavailabilityPeriod.weekdays)).order_by(ResourceUnavailabilityPeriod.start_date, ResourceUnavailabilityPeriod.start_time, ResourceUnavailabilityPeriod.id)).scalars().all())


def unavailability_record(period: ResourceUnavailabilityPeriod) -> dict:
    resource_type = "lecturer" if period.lecturer_id is not None else "room"
    record = {
        "id": period.id,
        "resourceType": resource_type,
        "resourceId": period.lecturer_id if period.lecturer_id is not None else period.room_id,
        "kind": period.kind,
        "startTime": period.start_time.strftime("%H:%M"),
        "endTime": period.end_time.strftime("%H:%M"),
        "revision": period.revision,
    }
    if period.kind == "recurring":
        record["weekdays"] = [item.weekday for item in period.weekdays]
    else:
        record.update(
            startDate=period.start_date.isoformat(),
            endDate=period.end_date.isoformat(),
        )
    return record


def _ensure_unique_unavailability(db: Session, row, candidate: ResourceUnavailabilityPeriod, *, exclude_id: int | None = None) -> None:
    signature = _unavailability_signature(candidate)
    duplicate = next((period for period in list_unavailability(db, row) if period.id != exclude_id and _unavailability_signature(period) == signature), None)
    if duplicate is not None:
        raise ResourceCatalogError(409, [ResourceErrorItem("DUPLICATE_UNAVAILABILITY", "This exact unavailable period already exists.", None, {"conflictingPeriodId": duplicate.id})])


def create_unavailability(db: Session, row, **payload) -> ResourceUnavailabilityPeriod:
    values = _canonical_unavailability(**payload)
    owner = {"lecturer_id": row.id} if isinstance(row, Lecturer) else {"room_id": row.id}
    period = ResourceUnavailabilityPeriod(**owner, kind=values["kind"], start_date=values["start_date"], end_date=values["end_date"], start_time=values["start_time"], end_time=values["end_time"])
    period.weekdays = [ResourceUnavailabilityWeekday(weekday=value) for value in values["weekdays"]]
    _ensure_unique_unavailability(db, row, period)
    db.add(period); db.flush()
    return period


def _require_owned_period(db: Session, row, period_id: int) -> ResourceUnavailabilityPeriod:
    period = db.get(ResourceUnavailabilityPeriod, period_id, options=[selectinload(ResourceUnavailabilityPeriod.weekdays)])
    owned = period is not None and ((isinstance(row, Lecturer) and period.lecturer_id == row.id) or (isinstance(row, Room) and period.room_id == row.id))
    if not owned:
        raise ResourceCatalogError(404, [ResourceErrorItem("NOT_FOUND", "Unavailable period not found.")])
    return period


def update_unavailability(db: Session, row, period_id: int, *, expected_revision: int, **payload) -> ResourceUnavailabilityPeriod:
    period = _require_owned_period(db, row, period_id)
    require_resource_revision(period, expected_revision)
    values = _canonical_unavailability(**payload)
    candidate = ResourceUnavailabilityPeriod(lecturer_id=period.lecturer_id, room_id=period.room_id, kind=values["kind"], start_date=values["start_date"], end_date=values["end_date"], start_time=values["start_time"], end_time=values["end_time"])
    candidate.weekdays = [ResourceUnavailabilityWeekday(weekday=value) for value in values["weekdays"]]
    _ensure_unique_unavailability(db, row, candidate, exclude_id=period.id)
    period.kind, period.start_date, period.end_date = values["kind"], values["start_date"], values["end_date"]
    period.start_time, period.end_time = values["start_time"], values["end_time"]
    period.weekdays = [ResourceUnavailabilityWeekday(weekday=value) for value in values["weekdays"]]
    period.revision += 1; db.flush()
    return period


def delete_unavailability(db: Session, row, period_id: int, *, expected_revision: int) -> None:
    period = _require_owned_period(db, row, period_id)
    require_resource_revision(period, expected_revision)
    db.delete(period); db.flush()


def resource_candidate(resource, *, kind: str, eligible: bool, cohort_size: int) -> dict:
    reasons = []
    if not resource.is_active:
        reasons.append("RESOURCE_INACTIVE")
    if isinstance(resource, Room) and resource.capacity < cohort_size:
        reasons.append("ROOM_CAPACITY_INSUFFICIENT")
    return {
        "id": resource.id,
        "name": resource.name,
        "referenceCode": resource.reference_code,
        "kind": kind,
        "capacity": resource.capacity if isinstance(resource, Room) else None,
        "isActive": resource.is_active,
        "isEligible": eligible,
        "isUsable": not reasons,
        "reasons": reasons,
    }


def _course_session_usage_by_resource(
    db: Session,
    *,
    course_id: int,
    resource_column,
    resource_ids: list[int],
) -> dict[int, dict]:
    if not resource_ids:
        return {}
    rows = db.execute(
        select(
            resource_column,
            func.count(DraftSession.id),
            func.count(func.distinct(DraftSession.draft_schedule_id)),
        )
        .where(
            DraftSession.course_id == course_id,
            resource_column.in_(resource_ids),
        )
        .group_by(resource_column)
    ).all()
    return {
        resource_id: {
            "draftSessionCount": int(session_count),
            "draftScheduleCount": int(schedule_count),
        }
        for resource_id, session_count, schedule_count in rows
    }


def _course_resource_candidate(
    resource,
    *,
    kind: str,
    eligible: bool,
    cohort_size: int,
    session_usage: dict | None,
) -> dict:
    candidate = resource_candidate(
        resource,
        kind=kind,
        eligible=eligible,
        cohort_size=cohort_size,
    )
    periods = sorted(
        resource.unavailability_periods,
        key=lambda period: (
            0 if period.kind == "recurring" else 1,
            min((item.weekday for item in period.weekdays), default=-1)
            if period.kind == "recurring"
            else period.start_date.toordinal(),
            period.start_time,
            period.id,
        ),
    )
    candidate.update(
        unavailabilityPeriods=[unavailability_record(period) for period in periods],
        courseSessionUsage=session_usage or {
            "draftSessionCount": 0,
            "draftScheduleCount": 0,
        },
    )
    return candidate


def validate_course_resource_candidates(
    db: Session,
    *,
    cohort_size: int,
    lecturer_ids: list[int],
    room_ids: list[int],
    current_lecturer_ids: set[int] | None = None,
    current_room_ids: set[int] | None = None,
) -> list[ResourceErrorItem]:
    current_lecturer_ids = current_lecturer_ids or set()
    current_room_ids = current_room_ids or set()
    lecturer_id_set = set(lecturer_ids)
    room_id_set = set(room_ids)
    lecturers = {
        resource.id: resource
        for resource in db.execute(select(Lecturer).where(Lecturer.id.in_(lecturer_id_set))).scalars()
    } if lecturer_id_set else {}
    rooms = {
        resource.id: resource
        for resource in db.execute(select(Room).where(Room.id.in_(room_id_set))).scalars()
    } if room_id_set else {}
    errors: list[ResourceErrorItem] = []
    for resource_id in dict.fromkeys(lecturer_ids):
        resource = lecturers.get(resource_id)
        if resource is None:
            errors.append(ResourceErrorItem("RESOURCE_NOT_FOUND", f"Lecturer {resource_id} does not exist.", "lecturerIds", {"resourceId": resource_id}))
        elif not resource.is_active and resource_id not in current_lecturer_ids:
            errors.append(ResourceErrorItem("RESOURCE_INACTIVE", f"Lecturer {resource.name} is inactive.", "lecturerIds", {"resourceId": resource_id}))
    for resource_id in dict.fromkeys(room_ids):
        resource = rooms.get(resource_id)
        if resource is None:
            errors.append(ResourceErrorItem("RESOURCE_NOT_FOUND", f"Room {resource_id} does not exist.", "roomIds", {"resourceId": resource_id}))
        elif not resource.is_active and resource_id not in current_room_ids:
            errors.append(ResourceErrorItem("RESOURCE_INACTIVE", f"Room {resource.name} is inactive.", "roomIds", {"resourceId": resource_id}))
        elif resource.capacity < cohort_size and resource_id not in current_room_ids:
            errors.append(ResourceErrorItem("ROOM_CAPACITY_INSUFFICIENT", f"Room {resource.name} has capacity {resource.capacity}; this Course requires {cohort_size}.", "roomIds", {"resourceId": resource_id, "capacity": resource.capacity, "requiredCapacity": cohort_size}))
    return errors


def get_course_resource_configuration(db: Session, course: Course) -> dict:
    lecturer_ids = sorted(item.lecturer_id for item in course.eligible_lecturers)
    room_ids = sorted(item.room_id for item in course.eligible_rooms)
    assigned_lecturer_ids = set(db.execute(
        select(DraftSession.lecturer_id)
        .where(DraftSession.course_id == course.id)
        .distinct()
    ).scalars())
    assigned_room_ids = set(db.execute(
        select(DraftSession.room_id)
        .where(DraftSession.course_id == course.id)
        .distinct()
    ).scalars())
    preserved_lecturer_ids = set(lecturer_ids) | assigned_lecturer_ids
    preserved_room_ids = set(room_ids) | assigned_room_ids
    lecturers = db.execute(
        select(Lecturer)
        .where(or_(Lecturer.is_active.is_(True), Lecturer.id.in_(preserved_lecturer_ids or {-1})))
        .options(
            selectinload(Lecturer.unavailability_periods).selectinload(
                ResourceUnavailabilityPeriod.weekdays
            )
        )
        .order_by(Lecturer.normalized_reference_code, Lecturer.id)
    ).scalars().all()
    rooms = db.execute(
        select(Room)
        .where(or_(Room.is_active.is_(True), Room.id.in_(preserved_room_ids or {-1})))
        .options(
            selectinload(Room.unavailability_periods).selectinload(
                ResourceUnavailabilityPeriod.weekdays
            )
        )
        .order_by(Room.normalized_reference_code, Room.id)
    ).scalars().all()
    cohort_size = course.cohort.student_count
    lecturer_usage = _course_session_usage_by_resource(
        db,
        course_id=course.id,
        resource_column=DraftSession.lecturer_id,
        resource_ids=[resource.id for resource in lecturers],
    )
    room_usage = _course_session_usage_by_resource(
        db,
        course_id=course.id,
        resource_column=DraftSession.room_id,
        resource_ids=[resource.id for resource in rooms],
    )
    return {
        "courseId": course.id,
        "courseRevision": course.revision,
        "cohortSize": cohort_size,
        "eligibleLecturerIds": lecturer_ids,
        "eligibleRoomIds": room_ids,
        "lecturerCandidates": [
            _course_resource_candidate(
                resource,
                kind="lecturer",
                eligible=resource.id in lecturer_ids,
                cohort_size=cohort_size,
                session_usage=lecturer_usage.get(resource.id),
            )
            for resource in lecturers
        ],
        "roomCandidates": [
            _course_resource_candidate(
                resource,
                kind="room",
                eligible=resource.id in room_ids,
                cohort_size=cohort_size,
                session_usage=room_usage.get(resource.id),
            )
            for resource in rooms
        ],
        "preferences": {"minimizeLecturerChanges": True, "minimizeRoomChanges": True},
    }


def replace_course_eligibility(
    db: Session,
    course: Course,
    *,
    expected_revision: int,
    lecturer_ids: list[int],
    room_ids: list[int],
) -> dict:
    require_resource_revision(course, expected_revision)
    errors: list[ResourceErrorItem] = []
    if not lecturer_ids:
        errors.append(ResourceErrorItem("LAST_ELIGIBLE_RESOURCE_REQUIRED", "Keep at least one eligible Lecturer.", "lecturerIds"))
    elif len(set(lecturer_ids)) != len(lecturer_ids):
        errors.append(ResourceErrorItem("DUPLICATE_RESOURCE_ID", "Lecturer IDs must be distinct.", "lecturerIds"))
    if not room_ids:
        errors.append(ResourceErrorItem("LAST_ELIGIBLE_RESOURCE_REQUIRED", "Keep at least one eligible Room.", "roomIds"))
    elif len(set(room_ids)) != len(room_ids):
        errors.append(ResourceErrorItem("DUPLICATE_RESOURCE_ID", "Room IDs must be distinct.", "roomIds"))
    current_lecturers = {item.lecturer_id for item in course.eligible_lecturers}
    current_rooms = {item.room_id for item in course.eligible_rooms}
    errors.extend(validate_course_resource_candidates(
        db,
        cohort_size=course.cohort.student_count,
        lecturer_ids=lecturer_ids,
        room_ids=room_ids,
        current_lecturer_ids=current_lecturers,
        current_room_ids=current_rooms,
    ))
    if errors:
        raise ResourceCatalogError(422, errors)
    course.eligible_lecturers = [CourseEligibleLecturer(lecturer_id=value) for value in sorted(set(lecturer_ids))]
    course.eligible_rooms = [CourseEligibleRoom(room_id=value) for value in sorted(set(room_ids))]
    course.revision += 1
    db.flush()
    return get_course_resource_configuration(db, course)
