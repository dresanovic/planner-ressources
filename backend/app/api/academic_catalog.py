from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, object_session, selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.db.session import get_db
from app.models.planning import Cohort, Course, CourseEligibleLecturer, CourseEligibleRoom, Semester, StudyType, StudyTypeTimeWindow
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
    StudyTypeInput,
    StudyTypeUpdate,
    StudyTypeResponse,
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
    create_study_type,
    create_time_window,
    delete_record,
    list_records,
    require_record,
    set_lifecycle,
    update_cohort,
    update_cohort_with_capacity_impact,
    update_course,
    update_semester,
    update_study_type,
    update_time_window,
    usage_for,
)

router = APIRouter(prefix="/api/academic", tags=["academic catalog"])

COURSE_OPTIONS = (
    selectinload(Course.current_semester),
    selectinload(Course.cohort),
    selectinload(Course.study_type),
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


def _time_window(row: StudyTypeTimeWindow) -> TimeWindowResponse:
    reasons = [] if row.is_active and row.study_type.is_active else ["RECORD_INACTIVE" if not row.is_active else "STUDY_TYPE_INACTIVE"]
    return TimeWindowResponse(
        id=row.id, studyTypeId=row.study_type_id, weekday=row.weekday,
        startTime=row.start_time.strftime("%H:%M"), endTime=row.end_time.strftime("%H:%M"),
        sortOrder=row.sort_order, isActive=row.is_active, revision=row.revision,
        availability=AvailabilityResponse(available=not reasons, reasons=reasons), usage=_usage(row, "time_window"),
    )


def _study_type(row: StudyType) -> StudyTypeResponse:
    return StudyTypeResponse(
        id=row.id, name=row.name, nameRepairRequired=row.name_repair_required,
        timeWindows=[_time_window(window) for window in row.time_windows],
        isActive=row.is_active, revision=row.revision, usage=_usage(row, "study_type"),
    )


def _course(db: Session, row: Course) -> CourseResponse:
    reasons = availability_for_course(db, row)
    summary = lambda value: EntitySummaryResponse(id=value.id, name=value.name)
    return CourseResponse(
        id=row.id, name=row.name, nameRepairRequired=row.name_repair_required,
        totalUnits=row.total_units, minSessionUnits=row.min_session_units, maxSessionUnits=row.max_session_units,
        semester=summary(row.current_semester) if row.current_semester else None,
        cohort=summary(row.cohort), studyType=summary(row.study_type), lecturer=summary(row.lecturer) if row.lecturer else None, room=summary(row.room) if row.room else None,
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


@router.get("/study-types", response_model=PageResponse)
def list_study_types(page: int = Query(1, ge=1), pageSize: int = Query(50, ge=1, le=200), status_filter: str = Query("all", alias="status"), query: str | None = None, db: Session = Depends(get_db)):
    rows, total = list_records(db, StudyType, page=page, page_size=pageSize, status=status_filter, query=query, options=(selectinload(StudyType.time_windows).selectinload(StudyTypeTimeWindow.study_type),))
    return _page(rows, total, page, pageSize, _study_type)


@router.post("/study-types", response_model=StudyTypeResponse, status_code=status.HTTP_201_CREATED)
def post_study_type(payload: StudyTypeInput, db: Session = Depends(get_db)):
    try:
        row = create_study_type(db, name=payload.name)
        db.commit()
        row = db.get(StudyType, row.id, options=[selectinload(StudyType.time_windows)])
        return _study_type(row)
    except AcademicCatalogError as exc:
        db.rollback(); return _error_response(exc)


@router.get("/study-types/{record_id}", response_model=StudyTypeResponse)
def get_study_type(record_id: int, db: Session = Depends(get_db)):
    row = db.get(StudyType, record_id, options=[selectinload(StudyType.time_windows).selectinload(StudyTypeTimeWindow.study_type)])
    if row is None: return _not_found("Study Type")
    return _study_type(row)


@router.get("/study-types/{study_type_id}/time-windows", response_model=list[TimeWindowResponse])
def list_time_windows(study_type_id: int, db: Session = Depends(get_db)):
    owner = db.get(StudyType, study_type_id)
    if owner is None: return _not_found("Study Type")
    rows = db.execute(
        select(StudyTypeTimeWindow)
        .where(StudyTypeTimeWindow.study_type_id == study_type_id)
        .options(selectinload(StudyTypeTimeWindow.study_type))
        .order_by(StudyTypeTimeWindow.sort_order, StudyTypeTimeWindow.id)
    ).scalars().all()
    return [_time_window(row) for row in rows]


@router.post("/study-types/{study_type_id}/time-windows", response_model=TimeWindowResponse, status_code=status.HTTP_201_CREATED)
def post_time_window(study_type_id: int, payload: TimeWindowInput, db: Session = Depends(get_db)):
    try:
        row = create_time_window(db, study_type_id, weekday=payload.weekday, start_time=payload.start_time, end_time=payload.end_time, sort_order=payload.sort_order)
        db.commit(); row = db.get(StudyTypeTimeWindow, row.id, options=[selectinload(StudyTypeTimeWindow.study_type)])
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
        row = create_course(db, name=payload.name, total_units=payload.total_units, min_session_units=payload.min_session_units, max_session_units=payload.max_session_units, semester_id=payload.semester_id, cohort_id=payload.cohort_id, study_type_id=payload.study_type_id, lecturer_id=payload.lecturer_id, room_id=payload.room_id)
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


@router.patch("/study-types/{record_id}", response_model=StudyTypeResponse)
def patch_study_type(record_id: int, payload: StudyTypeUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_study_type(db, require_record(db, StudyType, record_id), name=payload.name, expected_revision=payload.expected_revision), _study_type)


@router.get("/time-windows/{record_id}", response_model=TimeWindowResponse)
def get_time_window(record_id: int, db: Session = Depends(get_db)):
    try:
        return _time_window(require_record(db, StudyTypeTimeWindow, record_id))
    except AcademicCatalogError as exc:
        return _error_response(exc)


@router.patch("/time-windows/{record_id}", response_model=TimeWindowResponse)
def patch_time_window(record_id: int, payload: TimeWindowUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_time_window(db, require_record(db, StudyTypeTimeWindow, record_id), weekday=payload.weekday, start_time=payload.start_time, end_time=payload.end_time, sort_order=payload.sort_order, expected_revision=payload.expected_revision), _time_window)


@router.patch("/courses/{record_id}", response_model=CourseResponse)
def patch_course(record_id: int, payload: CourseUpdate, db: Session = Depends(get_db)):
    return _commit_or_error(db, lambda: update_course(db, require_record(db, Course, record_id), name=payload.name, total_units=payload.total_units, min_session_units=payload.min_session_units, max_session_units=payload.max_session_units, semester_id=payload.semester_id, cohort_id=payload.cohort_id, study_type_id=payload.study_type_id, expected_revision=payload.expected_revision), lambda row: _course(db, row))


RESOURCE_MODELS = {
    "semesters": Semester,
    "cohorts": Cohort,
    "courses": Course,
    "study-types": StudyType,
    "time-windows": StudyTypeTimeWindow,
}


def _converter(resource: str, db: Session, row):
    if resource == "semesters": return _semester(row)
    if resource == "cohorts": return _cohort(row)
    if resource == "courses": return _course(db, row)
    if resource == "study-types": return _study_type(row)
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
