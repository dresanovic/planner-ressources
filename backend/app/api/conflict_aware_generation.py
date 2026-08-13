from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conflict_aware_generation import (
    AcceptRegenerationRequest,
    OperationError,
    OptimizationDecisionRequiredResult,
    OptimizationGenerationRequest,
    OptimizationGenerationResult,
    OptimizationOperationFailure,
    OptimizationPreparationRequest,
    OptimizationPreparationResponse,
    RequestFailureResponse,
)
from app.services.conflict_aware_generation import (
    CandidateNotReproducible,
    InvalidOptimizationSelection,
    SemesterNotFoundError,
    StaleOptimizationCandidate,
    accept_optimization,
    canonical_unavailable_dates,
    generate_optimization,
    prepare_optimization,
)
from app.services.semester_optimization import NoGeneratedAlternative, OptimalResultNotProven, OptimizationModelInvalid
from app.services.schedule_lifecycle import LifecycleFailure, require_active_working_revision
from app.api.schedule_lifecycle import lifecycle_failure_response
from app.services.planning_outcomes import retain_planning_outcome


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
        require_active_working_revision(db, request.semester_id, request.schedule_revision_id)
        return prepare_optimization(
            db,
            request.semester_id,
            request.course_ids,
            request.unavailable_dates,
            request.schedule_revision_id,
        )
    except LifecycleFailure as exc:
        return lifecycle_failure_response(exc)
    except SemesterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidOptimizationSelection as exc:
        return _request_failure(exc.code, exc.message)


@router.post(
    "/generate",
    response_model=OptimizationGenerationResult | OptimizationDecisionRequiredResult,
    response_model_exclude_none=True,
)
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
    try:
        require_active_working_revision(db, request.semester_id, request.schedule_revision_id)
        result = generate_optimization(
            db,
            request.semester_id,
            request.courses,
            request.unavailable_dates,
            request.shared_snapshot_token,
            request.schedule_revision_id,
        )
        if isinstance(result, OptimizationDecisionRequiredResult):
            db.rollback()
            return result
        _retain_saved_outcomes(db, request.schedule_revision_id, result)
        db.commit()
        return result
    except SemesterNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LifecycleFailure as exc:
        db.rollback()
        return lifecycle_failure_response(exc)
    except InvalidOptimizationSelection as exc:
        db.rollback()
        return _request_failure(exc.code, exc.message)
    except StaleOptimizationCandidate as exc:
        db.rollback()
        return _conflict_failure("STALE_PLANNING_INPUT", str(exc))
    except NoGeneratedAlternative as exc:
        db.rollback()
        return _operation_failure("NO_VALID_ALTERNATIVE", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
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


@router.post(
    "/accept",
    response_model=OptimizationGenerationResult,
    response_model_exclude_none=True,
)
def accept_conflict_aware_drafts(
    request: AcceptRegenerationRequest,
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
    try:
        require_active_working_revision(
            db, request.semester_id, request.schedule_revision_id
        )
        result = accept_optimization(
            db,
            request.semester_id,
            request.courses,
            request.unavailable_dates,
            request.shared_snapshot_token,
            request.schedule_revision_id,
            request.candidate_fingerprint,
        )
        _retain_saved_outcomes(db, request.schedule_revision_id, result)
        db.commit()
        return result
    except SemesterNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LifecycleFailure as exc:
        db.rollback()
        return lifecycle_failure_response(exc)
    except InvalidOptimizationSelection as exc:
        db.rollback()
        return _request_failure(exc.code, exc.message)
    except StaleOptimizationCandidate as exc:
        db.rollback()
        return _conflict_failure("STALE_PLANNING_INPUT", str(exc))
    except CandidateNotReproducible as exc:
        db.rollback()
        return _conflict_failure("CANDIDATE_NOT_REPRODUCIBLE", str(exc))
    except NoGeneratedAlternative as exc:
        db.rollback()
        return _operation_failure("NO_VALID_ALTERNATIVE", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
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
            "The accepted optimization operation failed. No result was saved.",
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


def _conflict_failure(code: str, message: str):
    body = RequestFailureResponse(errors=[OperationError(code=code, message=message)])
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=body.model_dump(mode="json", by_alias=True),
    )


def _retain_saved_outcomes(
    db: Session,
    schedule_revision_id: int,
    result: OptimizationGenerationResult,
) -> None:
    completed_at = datetime.now(timezone.utc)
    classifications = {
        "complete": "successful",
        "improved_partial": "successful",
        "unchanged": "unchanged",
        "failed": "failed",
        "stale": "stale",
    }
    for outcome in result.outcomes:
        status_value = (
            outcome.status.value
            if hasattr(outcome.status, "value")
            else str(outcome.status)
        )
        retain_planning_outcome(
            db,
            schedule_revision_id=schedule_revision_id,
            course_id=outcome.course_id,
            operation_kind="semester_optimization",
            classification=classifications[status_value],
            source_status=status_value,
            result_payload=outcome.model_dump(
                mode="json", by_alias=True, exclude_none=True
            ),
            completed_at=completed_at,
        )
