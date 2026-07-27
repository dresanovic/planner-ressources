from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.calendar_workspace import (
    CalendarWorkspaceResponse,
    WorkspaceProblem,
)
from app.services.calendar_workspace import (
    CalendarWorkspaceError,
    get_calendar_workspace,
)


router = APIRouter(tags=["calendar workspace"])


@router.get(
    "/api/semesters/{semester_id}/calendar-workspace",
    response_model=CalendarWorkspaceResponse,
    responses={
        404: {"model": WorkspaceProblem},
        409: {"model": WorkspaceProblem},
        422: {"model": WorkspaceProblem},
    },
)
def read_calendar_workspace(
    semester_id: int,
    revision_id: int | None = Query(default=None, alias="revisionId", ge=1),
    db: Session = Depends(get_db),
):
    try:
        return get_calendar_workspace(db, semester_id, revision_id)
    except CalendarWorkspaceError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
