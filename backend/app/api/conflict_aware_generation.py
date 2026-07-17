from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conflict_aware_generation import (
    OperationError,
    OptimizationGenerationRequest,
    OptimizationGenerationResult,
    OptimizationOperationFailure,
    OptimizationPreparationRequest,
    OptimizationPreparationResponse,
    ReplacementConfirmationRequired,
    RequestFailureResponse,
)
from app.services.conflict_aware_generation import (
    InvalidOptimizationSelection,
    SemesterNotFoundError,
    canonical_unavailable_dates,
    generate_optimization,
    prepare_optimization,
)
from app.services.semester_optimization import OptimalResultNotProven, OptimizationModelInvalid


router = APIRouter(
    prefix="/api/draft-schedules/optimization",
    tags=["conflict-aware semester optimization"],
)


@router.post("/prepare", response_model=OptimizationPreparationResponse)
def prepare_conflict_aware_generation(
    request: OptimizationPreparationRequest,
    db: Session = Depends(get_db),
):
    try:
        return prepare_optimization(
            db,
            request.semester_id,
            request.course_ids,
            request.unavailable_dates,
        )
    except SemesterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidOptimizationSelection as exc:
        return _request_failure(exc.code, exc.message)


@router.post("/generate", response_model=OptimizationGenerationResult)
def generate_conflict_aware_drafts(
    request: OptimizationGenerationRequest,
    db: Session = Depends(get_db),
):
    course_ids = [item.course_id for item in request.courses]
    if len(set(course_ids)) != len(course_ids):
        return _request_failure("DUPLICATE_COURSE_SELECTION", "Select each course only once.")
    if list(canonical_unavailable_dates(request.unavailable_dates)) != request.unavailable_dates:
        return _request_failure(
            "INVALID_PREPARED_SNAPSHOT",
            "Unavailable dates must echo the canonical deduplicated preparation values.",
        )
    replacement_ids = [
        item.course_id for item in request.courses
        if item.expected_draft_schedule_id is not None
    ]
    if replacement_ids and not request.replacement_confirmed:
        body = ReplacementConfirmationRequired(
            message="Confirm replacement of the listed Draft Schedules, including manual edits.",
            replacementCourseIds=sorted(replacement_ids),
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=body.model_dump(mode="json", by_alias=True),
        )
    try:
        result = generate_optimization(
            db,
            request.semester_id,
            request.courses,
            request.unavailable_dates,
            request.shared_snapshot_token,
        )
        db.commit()
        return result
    except SemesterNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidOptimizationSelection as exc:
        db.rollback()
        return _request_failure(exc.code, exc.message)
    except OptimalResultNotProven as exc:
        db.rollback()
        return _operation_failure("OPTIMAL_RESULT_NOT_PROVEN", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
    except OptimizationModelInvalid as exc:
        db.rollback()
        return _operation_failure("OPTIMIZATION_MODEL_INVALID", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        db.rollback()
        return _operation_failure(
            "OPTIMIZATION_OPERATION_FAILED",
            "The optimization operation failed. No uncommitted result was saved.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _request_failure(code: str, message: str):
    body = RequestFailureResponse(errors=[OperationError(code=code, message=message)])
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body.model_dump(mode="json", by_alias=True),
    )


def _operation_failure(code: str, message: str, response_status: int):
    body = OptimizationOperationFailure(code=code, message=message, saved=False)
    return JSONResponse(
        status_code=response_status,
        content=body.model_dump(mode="json", by_alias=True),
    )
