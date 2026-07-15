from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.db.session import get_db
from app.models.planning import Lecturer, Room
from app.schemas.resource_catalog import (
    LecturerCreate,
    LecturerList,
    LecturerReactivationResult,
    LecturerRecord,
    LecturerRemovalResult,
    LecturerUpdate,
    ResourceErrorEnvelope,
    ResourceErrorResponseItem,
    ResourceUsageAssessment,
    RevisionCommand,
    RoomCreate,
    RoomList,
    RoomMutationResult,
    RoomReactivationResult,
    RoomRecord,
    RoomRemovalResult,
    RoomUpdate,
    UnavailabilityCreate,
    UnavailabilityRecord,
    UnavailabilityUpdate,
    CourseResourceConfiguration,
    CourseResourceEligibilityUpdate,
)
from app.services.resource_catalog import (
    ResourceCatalogError,
    ResourceErrorItem,
    assess_resource_usage,
    create_resource,
    list_resources,
    reactivate_resource,
    remove_resource,
    require_resource,
    update_resource,
    create_unavailability,
    delete_unavailability,
    list_unavailability,
    update_unavailability,
    unavailability_record,
    get_course_resource_configuration,
    replace_course_eligibility,
)

router = APIRouter(prefix="/api/resources", tags=["resource catalog"])
academic_router = APIRouter(prefix="/api/academic", tags=["resource eligibility"])


def _error_response(exc: ResourceCatalogError) -> JSONResponse:
    payload = ResourceErrorEnvelope(
        errors=[
            ResourceErrorResponseItem(
                code=item.code,
                message=item.message,
                field=item.field,
                meta=item.meta,
            )
            for item in exc.errors
        ]
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


def _commit(db: Session, action):
    try:
        result = action()
        db.commit()
        return result
    except ResourceCatalogError as exc:
        db.rollback()
        return _error_response(exc)
    except StaleDataError:
        db.rollback()
        return _error_response(ResourceCatalogError(409, [ResourceErrorItem(
            "STALE_REVISION", "This record changed. Refresh and review the current values."
        )]))


@router.get("/lecturers", response_model=LecturerList)
def get_lecturers(
    status_filter: str = Query("active", alias="status"),
    query: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, total = list_resources(db, Lecturer, status=status_filter, query=query, page=page, page_size=pageSize)
    return LecturerList(items=rows, page=page, pageSize=pageSize, total=total)


@router.post("/lecturers", response_model=LecturerRecord, status_code=status.HTTP_201_CREATED)
def post_lecturer(payload: LecturerCreate, db: Session = Depends(get_db)):
    return _commit(db, lambda: create_resource(db, Lecturer, name=payload.name, reference_code=payload.reference_code)[0])


@router.get("/lecturers/{lecturer_id}", response_model=LecturerRecord)
def get_lecturer(lecturer_id: int, db: Session = Depends(get_db)):
    try:
        return require_resource(db, Lecturer, lecturer_id)
    except ResourceCatalogError as exc:
        return _error_response(exc)


@router.patch("/lecturers/{lecturer_id}", response_model=LecturerRecord)
def patch_lecturer(lecturer_id: int, payload: LecturerUpdate, db: Session = Depends(get_db)):
    return _commit(db, lambda: update_resource(db, require_resource(db, Lecturer, lecturer_id), name=payload.name, reference_code=payload.reference_code, expected_revision=payload.expected_revision)[0])


@router.get("/lecturers/{lecturer_id}/usage", response_model=ResourceUsageAssessment)
def get_lecturer_usage(lecturer_id: int, db: Session = Depends(get_db)):
    try:
        return assess_resource_usage(db, require_resource(db, Lecturer, lecturer_id))
    except ResourceCatalogError as exc:
        return _error_response(exc)


@router.delete("/lecturers/{lecturer_id}", response_model=LecturerRemovalResult)
def delete_lecturer(
    lecturer_id: int,
    expected_revision: int = Query(..., alias="expectedRevision", ge=1),
    confirmed: bool = Query(...),
    db: Session = Depends(get_db),
):
    return _commit(db, lambda: remove_resource(db, require_resource(db, Lecturer, lecturer_id), expected_revision=expected_revision, confirmed=confirmed))


@router.post("/lecturers/{lecturer_id}/reactivate", response_model=LecturerReactivationResult)
def reactivate_lecturer(lecturer_id: int, payload: RevisionCommand, db: Session = Depends(get_db)):
    return _commit(db, lambda: reactivate_resource(db, require_resource(db, Lecturer, lecturer_id), expected_revision=payload.expected_revision))


@router.get("/rooms", response_model=RoomList)
def get_rooms(
    status_filter: str = Query("active", alias="status"),
    query: str | None = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows, total = list_resources(db, Room, status=status_filter, query=query, page=page, page_size=pageSize)
    return RoomList(items=rows, page=page, pageSize=pageSize, total=total)


@router.post("/rooms", response_model=RoomRecord, status_code=status.HTTP_201_CREATED)
def post_room(payload: RoomCreate, db: Session = Depends(get_db)):
    return _commit(db, lambda: create_resource(db, Room, name=payload.name, reference_code=payload.reference_code, capacity=payload.capacity)[0])


@router.get("/rooms/{room_id}", response_model=RoomRecord)
def get_room(room_id: int, db: Session = Depends(get_db)):
    try:
        return require_resource(db, Room, room_id)
    except ResourceCatalogError as exc:
        return _error_response(exc)


@router.patch("/rooms/{room_id}", response_model=RoomMutationResult)
def patch_room(room_id: int, payload: RoomUpdate, db: Session = Depends(get_db)):
    def action():
        room, impacts = update_resource(db, require_resource(db, Room, room_id), name=payload.name, reference_code=payload.reference_code, capacity=payload.capacity, expected_revision=payload.expected_revision)
        return {"room": room, "affectedRelationships": impacts}
    return _commit(db, action)


@router.get("/rooms/{room_id}/usage", response_model=ResourceUsageAssessment)
def get_room_usage(room_id: int, db: Session = Depends(get_db)):
    try:
        return assess_resource_usage(db, require_resource(db, Room, room_id))
    except ResourceCatalogError as exc:
        return _error_response(exc)


@router.delete("/rooms/{room_id}", response_model=RoomRemovalResult)
def delete_room(
    room_id: int,
    expected_revision: int = Query(..., alias="expectedRevision", ge=1),
    confirmed: bool = Query(...),
    db: Session = Depends(get_db),
):
    return _commit(db, lambda: remove_resource(db, require_resource(db, Room, room_id), expected_revision=expected_revision, confirmed=confirmed))


@router.post("/rooms/{room_id}/reactivate", response_model=RoomReactivationResult)
def reactivate_room(room_id: int, payload: RevisionCommand, db: Session = Depends(get_db)):
    return _commit(db, lambda: reactivate_resource(db, require_resource(db, Room, room_id), expected_revision=payload.expected_revision))


def _resource_model(resource_type: str):
    if resource_type == "lecturers": return Lecturer
    if resource_type == "rooms": return Room
    raise ResourceCatalogError(404, [ResourceErrorItem("NOT_FOUND", "Resource type not found.")])


def _period_payload(payload) -> dict:
    values = payload.model_dump(by_alias=False)
    return {
        "kind": values["kind"],
        "weekdays": values.get("weekdays"),
        "start_date_value": values.get("start_date"),
        "end_date_value": values.get("end_date"),
        "start_time_value": values.get("start_time"),
        "end_time_value": values.get("end_time"),
    }


@router.get("/{resource_type}/{resource_id}/unavailability", response_model=list[UnavailabilityRecord])
def get_unavailability(resource_type: str, resource_id: int, db: Session = Depends(get_db)):
    try:
        row = require_resource(db, _resource_model(resource_type), resource_id)
        return [unavailability_record(period) for period in list_unavailability(db, row)]
    except ResourceCatalogError as exc:
        return _error_response(exc)


@router.post("/{resource_type}/{resource_id}/unavailability", response_model=UnavailabilityRecord, status_code=status.HTTP_201_CREATED)
def post_unavailability(resource_type: str, resource_id: int, payload: UnavailabilityCreate, db: Session = Depends(get_db)):
    return _commit(db, lambda: unavailability_record(create_unavailability(db, require_resource(db, _resource_model(resource_type), resource_id), **_period_payload(payload))))


@router.patch("/{resource_type}/{resource_id}/unavailability/{period_id}", response_model=UnavailabilityRecord)
def patch_unavailability(resource_type: str, resource_id: int, period_id: int, payload: UnavailabilityUpdate, db: Session = Depends(get_db)):
    return _commit(db, lambda: unavailability_record(update_unavailability(db, require_resource(db, _resource_model(resource_type), resource_id), period_id, expected_revision=payload.expected_revision, **_period_payload(payload))))


@router.delete("/{resource_type}/{resource_id}/unavailability/{period_id}", status_code=204)
def remove_unavailability(resource_type: str, resource_id: int, period_id: int, expected_revision: int = Query(..., alias="expectedRevision", ge=1), db: Session = Depends(get_db)):
    result = _commit(db, lambda: delete_unavailability(db, require_resource(db, _resource_model(resource_type), resource_id), period_id, expected_revision=expected_revision))
    return result if isinstance(result, JSONResponse) else Response(status_code=204)


@academic_router.get("/courses/{course_id}/resource-eligibility", response_model=CourseResourceConfiguration)
def get_course_eligibility(course_id: int, db: Session = Depends(get_db)):
    from app.models.planning import Course
    course = db.get(Course, course_id)
    if course is None:
        return _error_response(ResourceCatalogError(404, [ResourceErrorItem("NOT_FOUND", "Course not found.")]))
    return get_course_resource_configuration(db, course)


@academic_router.put("/courses/{course_id}/resource-eligibility", response_model=CourseResourceConfiguration)
def put_course_eligibility(course_id: int, payload: CourseResourceEligibilityUpdate, db: Session = Depends(get_db)):
    from app.models.planning import Course
    def action():
        course = db.get(Course, course_id)
        if course is None:
            raise ResourceCatalogError(404, [ResourceErrorItem("NOT_FOUND", "Course not found.")])
        return replace_course_eligibility(db, course, expected_revision=payload.expected_revision, lecturer_ids=payload.lecturer_ids, room_ids=payload.room_ids)
    return _commit(db, action)
