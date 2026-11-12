from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, object_session, selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.db.session import get_db
from app.models.planning import Cohort, Course, CourseEligibleLecturer, CourseEligibleRoom, Semester, CohortCalendar, CohortCalendarTimeWindow
from app.schemas.academic_catalog import (
    AvailabilityResponse,
    CatalogErrorEnvelope,
    CatalogErrorResponseItem,
    CohortInput,
    CohortUpdate,
    CohortResponse,
    CohortMutationResult,
    CourseInput,
    CourseUpdate,
    CourseResponse,
    EntitySummaryResponse,
    PageResponse,
    LifecycleRequest,
    SemesterInput,
    SemesterUpdate,
    SemesterResponse,
    CohortCalendarInput,
    CohortCalendarUpdate,
    CohortCalendarResponse,
    TimeWindowInput,
    TimeWindowUpdate,
    TimeWindowResponse,
    UsageSummaryResponse,
)
from app.services.academic_catalog import (
    AcademicCatalogError,
    CatalogErrorItem,
    availability_for_course,
    create_cohort,
    create_course,
    create_semester,
    create_cohort_calendar,
    create_time_window,
    delete_record,
    list_records,
    require_record,
    set_lifecycle,
    update_cohort,
    update_cohort_with_capacity_impact,
    update_course,
    update_semester,
    update_cohort_calendar,
    update_time_window,
    usage_for,
    window_overlap_notice,
)
from app.services.schedule_generation import format_clock

router = APIRouter(prefix="/api/academic", tags=["academic catalog"])

COURSE_OPTIONS = (
    selectinload(Course.current_semester),
    selectinload(Course.cohort),
    selectinload(Course.cohort_calendar),
    selectinload(Course.eligible_lecturers).selectinload(CourseEligibleLecturer.lecturer),
    selectinload(Course.eligible_rooms).selectinload(CourseEligibleRoom.room),
)


def _error_response(exc: AcademicCatalogError) -> JSONResponse:
    payload = CatalogErrorEnvelope(errors=[CatalogErrorResponseItem(code=e.code, message=e.message, field=e.field, meta=e.meta) for e in exc.errors])
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


def _not_found(label: str) -> JSONResponse:
    return _error_response(AcademicCatalogError(404, [CatalogErrorItem("NOT_FOUND", f"{label} not found.")]))


def _usage(row, record_type: str) -> UsageSummaryResponse:
    return UsageSummaryResponse.model_validate(usage_for(object_session(row), row))


def _semester(row: Semester) -> SemesterResponse:
    return SemesterResponse(id=row.id, name=row.name, nameRepairRequired=row.name_repair_required, startDate=row.start_date, endDate=row.end_date, isActive=row.is_active, revision=row.revision, usage=_usage(row, "semester"))


def _cohort(row: Cohort) -> CohortResponse:
    return CohortResponse(id=row.id, name=row.name, nameRepairRequired=row.name_repair_required, studentCount=row.student_count, isActive=row.is_active, revision=row.revision, usage=_usage(row, "cohort"))


def _time_window(row: CohortCalendarTimeWindow) -> TimeWindowResponse:
    reasons = [] if row.is_active and row.cohort_calendar.is_active else ["RECORD_INACTIVE" if not row.is_active else "COHORT_CALENDAR_INACTIVE"]
    return TimeWindowResponse(
        id=row.id, cohortCalendarId=row.cohort_calendar_id, weekday=row.weekday,
        kind=row.kind, date=row.date, isIntensive=row.is_intensive,
        overlapNotice=window_overlap_notice(object_session(row), row),
        startTime=format_clock(row.start_time), endTime=format_clock(row.end_time),
        sortOrder=row.sort_order, isActive=row.is_active, revision=row.revision,
        availability=AvailabilityResponse(available=not reasons, reasons=reasons), usage=_usage(row, "time_window"),
    )


def _cohort_calendar(row: CohortCalendar) -> CohortCalendarResponse:
    return CohortCalendarResponse(
        id=row.id, name=row.name, nameRepairRequired=row.name_repair_required, cohortId=row.cohort_id, semesterId=row.semester_id, startDate=row.start_date, endDate=row.end_date,
        timeWindows=[_time_window(window) for window in row.time_windows],
        isActive=row.is_active, revision=row.revision, usage=_usage(row, "cohort_calendar"),
    )


def _course(db: Session, row: Course) -> CourseResponse:
    reasons = availability_for_course(db, row)
    summary = lambda value: EntitySummaryResponse(id=value.id, name=value.name)
    return CourseResponse(
        id=row.id, name=row.name, nameRepairRequired=row.name_repair_required,
        totalUnits=row.total_units, overallUnits=row.overall_units, minSessionUnits=row.min_session_units, maxSessionUnits=row.max_session_units, preferredSessionUnits=row.preferred_session_units,
        semester=summary(row.current_semester) if row.current_semester else None,
        cohort=summary(row.cohort), cohortCalendar=summary(row.cohort_calendar) if row.cohort_calendar else None, lecturer=summary(row.lecturer) if row.lecturer else None, room=summary(row.room) if row.room else None,
        isActive=row.is_active, revision=row.revision,
        availability=AvailabilityResponse(available=not reasons, reasons=reasons), usage=_usage(row, "course"),
    )


def _page(rows, total: int, page: int, page_size: int, converter) -> PageResponse:
    return PageResponse(page=page, pageSize=page_size, total=total, items=[converter(row) for row in rows])


@router.get("/semesters", response_model=PageResponse)
def list_semesters(page: int = Query(1, ge=1), pageSize: int = Query(50, ge=1, le=200), status_filter: str = Query("all", alias="status"), query: str | None = None, db: Session = Depends(get_db)):
    rows, total = list_records(db, Semester, page=page, page_size=pageSize, status=status_filter, query=query)
    return _page(rows, total, page, pageSize, _semester)


@router.post("/semesters", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED)
def post_semester(payload: SemesterInput, db: Session = Depends(get_db)):
    try:
        row = create_semester(db, name=payload.name, start_date=payload.start_date, end_date=payload.end_date)
        db.commit(); db.refresh(row)
        return _semester(row)
    except AcademicCatalogError as exc:
        db.rollback(); return _error_response(exc)


@router.get("/semesters/{record_id}", response_model=SemesterResponse)
def get_semester(record_id: int, db: Session = Depends(get_db)):
    row = db.get(Semester, record_id)
    if row is None: return _not_found("Semester")
    return _semester(row)


@router.get("/cohorts", response_model=PageResponse)
def list_cohorts(page: int = Query(1, ge=1), pageSize: int = Query(50, ge=1, le=200), status_filter: str = Query("all", alias="status"), query: str | None = None, db: Session = Depends(get_db)):
    rows, total = list_records(db, Cohort, page=page, page_size=pageSize, status=status_filter, query=query)
    return _page(rows, total, page, pageSize, _cohort)


@router.post("/cohorts", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
def post_cohort(payload: CohortInput, db: Session = Depends(get_db)):
    try:
        row = create_cohort(db, name=payload.name, student_count=payload.student_count)
        db.commit(); db.refresh(row)
        return _cohort(row)
    except AcademicCatalogError as exc:
        db.rollback(); return _error_response(exc)


@router.get("/cohorts/{record_id}", response_model=CohortResponse)
def get_cohort(record_id: int, db: Session = Depends(get_db)):
    row = db.get(Cohort, record_id)
    if row is None: return _not_found("Cohort")
    return _cohort(row)


@router.get("/cohort-calendars", response_model=PageResponse)
def list_cohort_calendars(page: int = Query(1, ge=1), pageSize: int = Query(50, ge=1, le=200), status_filter: str = Query("all", alias="status"), query: str | None = None, db: Session = Depends(get_db)):
    rows, total = list_records(db, CohortCalendar, page=page, page_size=pageSize, status=status_filter, query=query, options=(selectinload(CohortCalendar.time_windows).selectinload(CohortCalendarTimeWindow.cohort_calendar),))
    return _page(rows, total, page, pageSize, _cohort_calendar)


@router.post("/cohort-calendars", response_model=CohortCalendarResponse, status_code=status.HTTP_201_CREATED)
def post_cohort_calendar(payload: CohortCalendarInput, db: Session = Depends(get_db)):
    try:
        row = create_cohort_calendar(db, **payload.model_dump())
        db.commit()
        row = db.get(CohortCalendar, row.id, options=[selectinload(CohortCalendar.time_windows)])
        return _cohort_calendar(row)
    except AcademicCatalogError as exc:
        db.rollback(); return _error_response(exc)


@router.get("/cohort-calendars/{record_id}", response_model=CohortCalendarResponse)
def get_cohort_calendar(record_id: int, db: Session = Depends(get_db)):
    row = db.get(CohortCalendar, record_id, options=[selectinload(CohortCalendar.time_windows).selectinload(CohortCalendarTimeWindow.cohort_calendar)])
    if row is None: return _not_found("Cohort Calendar")
    return _cohort_calendar(row)


@router.get("/cohort-calendars/{cohort_calendar_id}/time-windows", response_model=list[TimeWindowResponse])
def list_time_windows(cohort_calendar_id: int, db: Session = Depends(get_db)):
    owner = db.get(CohortCalendar, cohort_calendar_id)
    if owner is None: return _not_found("Cohort Calendar")
    rows = db.execute(
        select(CohortCalendarTimeWindow)
        .where(CohortCalendarTimeWindow.cohort_calendar_id == cohort_calendar_id)
        .options(selectinload(CohortCalendarTimeWindow.cohort_calendar))
        .order_by(CohortCalendarTimeWindow.kind == 'dated', CohortCalendarTimeWindow.weekday, CohortCalendarTimeWindow.date, CohortCalendarTimeWindow.start_time, CohortCalendarTimeWindow.end_time, CohortCalendarTimeWindow.sort_order, CohortCalendarTimeWindow.id)
    ).scalars().all()
    return [_time_window(row) for row in rows]


@router.post("/cohort-calendars/{cohort_calendar_id}/time-windows", response_model=TimeWindowResponse, status_code=status.HTTP_201_CREATED)
def post_time_window(cohort_calendar_id: int, payload: TimeWindowInput, db: Session = Depends(get_db)):
    try:
        row = create_time_window(db, cohort_calendar_id, **payload.model_dump())
        db.commit(); row = db.get(CohortCalendarTimeWindow, row.id, options=[selectinload(CohortCalendarTimeWindow.cohort_calendar)])
        return _time_window(row)
    except AcademicCatalogError as exc:
        db.rollback(); return _error_response(exc)


@router.get("/courses", response_model=PageResponse)
def list_courses(page: int = Query(1, ge=1), pageSize: int = Query(50, ge=1, le=200), status_filter: str = Query("all", alias="status"), query: str | None = None, semesterId: int | None = Query(None, ge=1), db: Session = Depends(get_db)):
    options = COURSE_OPTIONS
    filters = (Course.current_semester_id == semesterId,) if semesterId is not None else ()
    rows, total = list_records(db, Course, page=page, page_size=pageSize, status=status_filter, query=query, options=options, extra_filters=filters)
    return _page(rows, total, page, pageSize, lambda row: _course(db, row))


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def post_course(payload: CourseInput, db: Session = Depends(get_db)):
    try:
        row = create_course(db, name=payload.name, total_units=payload.total_units, overall_units=payload.overall_units, min_session_units=payload.min_session_units, max_session_units=payload.max_session_units, preferred_session_units=payload.preferred_session_units, semester_id=payload.semester_id, cohort_id=payload.cohort_id, lecturer_id=payload.lecturer_id, room_id=payload.room_id)
        db.commit()
        row = db.get(Course, row.id, options=COURSE_OPTIONS)
        return _course(db, row)
    except AcademicCatalogError as exc:
        db.rollback(); return _error_response(exc)


@router.get("/courses/{record_id}", response_model=CourseResponse)
def get_course(record_id: int, db: Session = Depends(get_db)):
    row = db.get(Course, record_id, options=COURSE_OPTIONS)
    if row is None: return _not_found("Course")
    return _course(db, row)


def _commit_or_error(db: Session, action, converter):
    try:
        row = action()
        db.commit()
        return converter(row)
    except AcademicCatalogError as exc:
        db.rollback()
        return _error_response(exc)
    except StaleDataError:
        db.rollback()
        return _error_response(AcademicCatalogError(409, [CatalogErrorItem(
            "STALE_REVISION", "This record changed. Refresh and review the current values."
        )]))


@router.patch("/semesters/{record_id}", response_model=SemesterResponse)
def patch_semester(record_id: int, payload: SemesterUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_semester(db, require_record(db, Semester, record_id), name=payload.name, start_date=payload.start_date, end_date=payload.end_date, expected_revision=payload.expected_revision), _semester)


@router.patch("/cohorts/{record_id}", response_model=CohortMutationResult)
def patch_cohort(record_id: int, payload: CohortUpdate, db: Session = Depends(get_db)):
    def action():
        row, impact = update_cohort_with_capacity_impact(db, require_record(db, Cohort, record_id), name=payload.name, student_count=payload.student_count, expected_revision=payload.expected_revision)
        return row, impact
    def convert(result):
        row, impact = result
        cohort = _cohort(row)
        return CohortMutationResult(**cohort.model_dump(), cohort=cohort, capacityImpact=impact)
    return _commit_or_error(db, action, convert)


@router.patch("/cohort-calendars/{record_id}", response_model=CohortCalendarResponse)
def patch_cohort_calendar(record_id: int, payload: CohortCalendarUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_cohort_calendar(db, require_record(db, CohortCalendar, record_id), **payload.model_dump()), _cohort_calendar)


@router.get("/time-windows/{record_id}", response_model=TimeWindowResponse)
def get_time_window(record_id: int, db: Session = Depends(get_db)):
    try:
        return _time_window(require_record(db, CohortCalendarTimeWindow, record_id))
    except AcademicCatalogError as exc:
        return _error_response(exc)


@router.patch("/time-windows/{record_id}", response_model=TimeWindowResponse)
def patch_time_window(record_id: int, payload: TimeWindowUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_time_window(db, require_record(db, CohortCalendarTimeWindow, record_id), **payload.model_dump()), _time_window)


@router.patch("/courses/{record_id}", response_model=CourseResponse)
def patch_course(record_id: int, payload: CourseUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_course(db, require_record(db, Course, record_id), name=payload.name, total_units=payload.total_units, overall_units=payload.overall_units, min_session_units=payload.min_session_units, max_session_units=payload.max_session_units, preferred_session_units=payload.preferred_session_units, semester_id=payload.semester_id, cohort_id=payload.cohort_id, expected_revision=payload.expected_revision), lambda row: _course(db, row))


RESOURCE_MODELS = {
    "semesters": Semester,
    "cohorts": Cohort,
    "courses": Course,
    "cohort-calendars": CohortCalendar,
    "time-windows": CohortCalendarTimeWindow,
}


def _converter(resource: str, db: Session, row):
    if resource == "semesters": return _semester(row)
    if resource == "cohorts": return _cohort(row)
    if resource == "courses": return _course(db, row)
    if resource == "cohort-calendars": return _cohort_calendar(row)
    return _time_window(row)


def make_usage_endpoint(resource: str):
    def endpoint(record_id: int, db: Session = Depends(get_db)):
        try:
            row = require_record(db, RESOURCE_MODELS[resource], record_id)
            return UsageSummaryResponse.model_validate(usage_for(db, row))
        except AcademicCatalogError as exc:
            return _error_response(exc)
    return endpoint


def make_lifecycle_endpoint(resource: str, active: bool):
    def endpoint(record_id: int, payload: LifecycleRequest, db: Session = Depends(get_db)):
        return _commit_or_error(db, lambda: set_lifecycle(db, require_record(db, RESOURCE_MODELS[resource], record_id), active=active, expected_revision=payload.expected_revision), lambda row: _converter(resource, db, row))
    return endpoint


def make_delete_endpoint(resource: str):
    def endpoint(record_id: int, expected_revision: int = Query(..., alias="expectedRevision", ge=1), db: Session = Depends(get_db)):
        try:
            delete_record(db, require_record(db, RESOURCE_MODELS[resource], record_id), expected_revision=expected_revision)
            db.commit()
            return Response(status_code=204)
        except AcademicCatalogError as exc:
            db.rollback()
            return _error_response(exc)
    return endpoint


for resource in RESOURCE_MODELS:
    router.add_api_route(f"/{resource}/{{record_id}}/usage", make_usage_endpoint(resource), methods=["GET"], response_model=UsageSummaryResponse, name=f"get_{resource}_usage")
    router.add_api_route(f"/{resource}/{{record_id}}/archive", make_lifecycle_endpoint(resource, False), methods=["POST"], name=f"archive_{resource}")
    router.add_api_route(f"/{resource}/{{record_id}}/reactivate", make_lifecycle_endpoint(resource, True), methods=["POST"], name=f"reactivate_{resource}")
    router.add_api_route(f"/{resource}/{{record_id}}", make_delete_endpoint(resource), methods=["DELETE"], status_code=204, name=f"delete_{resource}")
