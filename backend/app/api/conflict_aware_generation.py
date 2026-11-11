from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
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
from app.services.optimization_config import OptimizationConfigurationError
from app.services import optimization_operations as operations
from app.schemas.conflict_aware_generation import (
    OptimizationOperationStart, OptimizationOperationDecision, OptimizationOperationCancel,
    OptimizationOperationStatus, OptimizationOperationContinue,
)


router = APIRouter(
    prefix="/api/draft-schedules/optimization",
    tags=["conflict-aware semester optimization"],
)


def _operation_call(callback):
    try:
        return callback()
    except operations.OperationFailure as exc:
        return JSONResponse(status_code=exc.status, content={'errors': [{'code': exc.code, 'message': exc.message}]})
    except OptimizationConfigurationError as exc:
        return JSONResponse(status_code=503, content={'errors':[{'code':'OPTIMIZATION_CONFIGURATION_INVALID','message':str(exc)}]})
    except LifecycleFailure as exc:
        return lifecycle_failure_response(exc)


@router.post('/operations', response_model=OptimizationOperationStatus, status_code=202)
def start_optimization_operation(body: OptimizationOperationStart, request: Request, db: Session = Depends(get_db)):
    return _operation_call(lambda: operations.start_operation(db, body, request.state.planner_auth))


@router.get('/operations/{operation_id}', response_model=OptimizationOperationStatus)
def read_optimization_operation(operation_id: str, request: Request, db: Session = Depends(get_db)):
    return _operation_call(lambda: operations.get_status(db, operation_id, request.state.planner_auth,
        request.headers.get('X-Optimization-Context')))


@router.post('/operations/{operation_id}/accept', response_model=OptimizationOperationStatus)
def accept_optimization_operation(operation_id: str, body: OptimizationOperationDecision, request: Request, db: Session = Depends(get_db)):
    return _operation_call(lambda: operations.apply_operation(db, operation_id, request.state.planner_auth,
        body.context_secret, body.candidate_fingerprint))


@router.post('/operations/{operation_id}/continue', response_model=OptimizationOperationStatus, status_code=202)
def continue_optimization_operation(operation_id: str, body: OptimizationOperationContinue, request: Request, db: Session = Depends(get_db)):
    return _operation_call(lambda: operations.continue_operation(db, operation_id, request.state.planner_auth,
        body.context_secret, body.candidate_fingerprint, body.continuation_id))


@router.post('/operations/{operation_id}/finalize', response_model=OptimizationOperationStatus)
def finalize_optimization_operation(operation_id: str, body: OptimizationOperationDecision, request: Request, db: Session = Depends(get_db)):
    return _operation_call(lambda: operations.apply_operation(db, operation_id, request.state.planner_auth,
        body.context_secret, body.candidate_fingerprint, finalize=True))


@router.post('/operations/{operation_id}/cancel', response_model=OptimizationOperationStatus)
def cancel_optimization_operation(operation_id: str, body: OptimizationOperationCancel, request: Request, db: Session = Depends(get_db)):
    return _operation_call(lambda: operations.cancel_operation(db, operation_id, request.state.planner_auth, reason=body.reason))


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
    except OptimizationConfigurationError as exc:
        return JSONResponse(status_code=503, content={"errors": [{
            "code": "OPTIMIZATION_CONFIGURATION_INVALID", "message": str(exc),
        }]})
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
    return _conflict_failure('OPERATION_API_REQUIRED', 'Bitte den Optimierungslauf über die aktuelle Oberfläche starten.')


@router.post(
    "/accept",
    response_model=OptimizationGenerationResult,
    response_model_exclude_none=True,
)
def accept_conflict_aware_drafts(
    request: AcceptRegenerationRequest,
    db: Session = Depends(get_db),
):
    return _conflict_failure('OPERATION_API_REQUIRED', 'Bitte den Optimierungslauf über die aktuelle Oberfläche starten.')


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
