from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.schedule_lifecycle import (
    CreateWorkingRevisionRequest,
    ErrorResponse,
    LifecycleConflictResponse,
    LifecycleErrorItem,
    PreparePublicationRequest,
    PublicationPreparation,
    ScheduleLifecycleOverview,
    ScheduleRevisionContent,
    TransitionRevisionRequest,
)
from app.services.schedule_lifecycle import (
    LifecycleFailure,
    create_working_revision,
    get_lifecycle_overview,
    get_revision_content,
    prepare_publication,
    transition_revision,
)


router = APIRouter(tags=["schedule lifecycle"])


@router.get(
    "/api/semesters/{semester_id}/schedule-lifecycle",
    response_model=ScheduleLifecycleOverview,
    responses={404: {"model": ErrorResponse}},
)
def read_lifecycle(
    semester_id: int, db: Session = Depends(get_db)
) -> ScheduleLifecycleOverview | JSONResponse:
    try:
        return ScheduleLifecycleOverview.model_validate(
            get_lifecycle_overview(db, semester_id)
        )
    except LifecycleFailure as exc:
        return lifecycle_failure_response(exc)


@router.post(
    "/api/semesters/{semester_id}/schedule-revisions",
    response_model=ScheduleLifecycleOverview,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": LifecycleConflictResponse},
        422: {"model": ErrorResponse},
    },
)
def create_revision(
    semester_id: int,
    request: CreateWorkingRevisionRequest,
    db: Session = Depends(get_db),
) -> ScheduleLifecycleOverview | JSONResponse:
    try:
        result = create_working_revision(
            db, semester_id, request.expected_state_token
        )
        db.commit()
        return ScheduleLifecycleOverview.model_validate(result)
    except LifecycleFailure as exc:
        db.rollback()
        return lifecycle_failure_response(exc)
    except Exception:
        db.rollback()
        raise


@router.get(
    "/api/schedule-revisions/{revision_id}",
    response_model=ScheduleRevisionContent,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def read_revision(
    revision_id: int, db: Session = Depends(get_db)
) -> ScheduleRevisionContent | JSONResponse:
    try:
        return ScheduleRevisionContent.model_validate(
            get_revision_content(db, revision_id)
        )
    except LifecycleFailure as exc:
        return lifecycle_failure_response(exc)


@router.post(
    "/api/schedule-revisions/{revision_id}/publication-preparation",
    response_model=PublicationPreparation,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": LifecycleConflictResponse},
        422: {"model": ErrorResponse},
    },
)
def prepare_revision_publication(
    revision_id: int,
    request: PreparePublicationRequest,
    db: Session = Depends(get_db),
) -> PublicationPreparation | JSONResponse:
    try:
        return PublicationPreparation.model_validate(
            prepare_publication(
                db,
                revision_id,
                request.expected_revision_version,
                request.expected_state_token,
            )
        )
    except LifecycleFailure as exc:
        return lifecycle_failure_response(exc)


@router.post(
    "/api/schedule-revisions/{revision_id}/transitions",
    response_model=ScheduleLifecycleOverview,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": LifecycleConflictResponse},
        422: {"model": ErrorResponse},
    },
)
def transition(
    revision_id: int,
    request: TransitionRevisionRequest,
    db: Session = Depends(get_db),
) -> ScheduleLifecycleOverview | JSONResponse:
    try:
        result = transition_revision(
            db,
            revision_id,
            action=str(request.action),
            expected_revision_version=request.expected_revision_version,
            expected_state_token=request.expected_state_token,
            confirmed=request.confirmed,
            publication_token=request.publication_token,
        )
        db.commit()
        return ScheduleLifecycleOverview.model_validate(result)
    except LifecycleFailure as exc:
        db.rollback()
        return lifecycle_failure_response(exc)
    except Exception:
        db.rollback()
        raise


def lifecycle_failure_response(exc: LifecycleFailure) -> JSONResponse:
    error = LifecycleErrorItem(
        code=exc.code,
        message=exc.message,
        field=exc.field,
        meta=exc.meta,
    )
    if exc.status_code == 409:
        content = LifecycleConflictResponse(
            errors=[error], current_overview=exc.current_overview
        ).model_dump(mode="json", by_alias=True)
    else:
        content = ErrorResponse(errors=[error]).model_dump(mode="json", by_alias=True)
    return JSONResponse(status_code=exc.status_code, content=content)
