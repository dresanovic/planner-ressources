from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.multi_course_generation import (
    BatchGenerationRequest,
    BatchGenerationResult,
    BatchOperationFailureResponse,
    BatchPreparationRequest,
    BatchPreparationResponse,
    BatchRequestFailure,
    BatchRequestFailureResponse,
    ReplacementConfirmationRequiredResponse,
)
from app.services.multi_course_generation import (
    SemesterNotFoundError,
    generate_batch,
    prepare_batch,
)

router = APIRouter(prefix="/api/draft-schedules/batch", tags=["multi-course generation"])


@router.post("/prepare", response_model=BatchPreparationResponse)
def prepare_multi_course_generation(request: BatchPreparationRequest, db: Session = Depends(get_db)):
    validation = _validate_selection(request.operation_kind.value, request.course_ids)
    if validation:
        return _request_failure(validation)
    try:
        return prepare_batch(db, request.semester_id, request.operation_kind, request.course_ids)
    except SemesterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/generate", response_model=BatchGenerationResult, response_model_exclude_none=True)
def generate_multi_course_drafts(request: BatchGenerationRequest, db: Session = Depends(get_db)):
    course_ids = [course.course_id for course in request.courses]
    validation = _validate_selection(request.operation_kind.value, course_ids)
    if validation:
        return _request_failure(validation)
    malformed = any(
        (course.expected_draft_schedule_id is None) != (course.expected_draft_revision is None)
        for course in request.courses
    )
    if malformed:
        return _request_failure(BatchRequestFailure(
            code="INVALID_PREPARED_SNAPSHOT",
            message="Draft Schedule ID and revision must either both be present or both be null.",
        ))
    replacement_ids = [
        course.course_id for course in request.courses
        if course.expected_draft_schedule_id is not None
    ]
    if replacement_ids and not request.replacement_confirmed:
        body = ReplacementConfirmationRequiredResponse(
            message="Confirm replacement of existing Draft Schedules and manual edits.",
            replacementCourseIds=replacement_ids,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=body.model_dump(mode="json", by_alias=True),
        )
    try:
        result = generate_batch(db, request.semester_id, request.operation_kind, request.courses)
        db.commit()
        return result
    except SemesterNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        body = BatchOperationFailureResponse(
            message="The multi-course generation operation failed. No changes from this attempt were saved."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body.model_dump(mode="json"),
        )


def _validate_selection(operation_kind: str, course_ids: list[int]):
    minimum = 2 if operation_kind == "initial" else 1
    if len(course_ids) < minimum or len(course_ids) > 50:
        return BatchRequestFailure(
            code="INVALID_BATCH_SIZE",
            message=f"{operation_kind.capitalize()} generation requires {minimum}-50 courses.",
        )
    if len(set(course_ids)) != len(course_ids):
        return BatchRequestFailure(
            code="DUPLICATE_COURSE_SELECTION",
            message="Select each course only once.",
        )
    return None


def _request_failure(failure: BatchRequestFailure):
    body = BatchRequestFailureResponse(errors=[failure])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body.model_dump(mode="json"),
    )
