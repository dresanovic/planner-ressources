from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.draft_schedule import (
    DraftScheduleResponse,
    DraftSessionResponse,
    GenerateDraftScheduleRequest,
    GenerationFailureResponse,
)
from app.services.draft_schedule_repository import (
    PlanningInputNotFoundError,
    get_draft_schedule,
    load_course_plan,
    load_semester_plan,
    load_time_windows,
    replace_draft_schedule,
)
from app.services.schedule_generation import generate_schedule

router = APIRouter(prefix="/api/courses/{course_id}/draft-schedule", tags=["draft schedule"])


@router.post(
    "/generate",
    response_model=DraftScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": GenerationFailureResponse}},
)
def generate_draft_schedule(
    course_id: int,
    request: GenerateDraftScheduleRequest,
    db: Session = Depends(get_db),
) -> DraftScheduleResponse | JSONResponse:
    try:
        course = load_course_plan(db, course_id)
        semester = load_semester_plan(db, request.semester_id)
        time_windows = load_time_windows(db, course.study_type_id)
    except PlanningInputNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = generate_schedule(
        course=course,
        semester=semester,
        time_windows=time_windows,
        selected_time_window_id=request.selected_time_window_id,
    )
    if not result.ok:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=GenerationFailureResponse(errors=result.errors).model_dump(mode="json"),
        )
    draft = replace_draft_schedule(
        db,
        course_plan=course,
        semester_id=semester.id,
        selected_time_window_id=request.selected_time_window_id,
        generated_sessions=result.sessions,
    )
    return _to_response(draft)


@router.get("", response_model=DraftScheduleResponse)
def read_draft_schedule(course_id: int, db: Session = Depends(get_db)) -> DraftScheduleResponse:
    draft = get_draft_schedule(db, course_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="No generated draft schedule exists.")
    return _to_response(draft)


def _to_response(draft) -> DraftScheduleResponse:
    return DraftScheduleResponse(
        draftScheduleId=draft.id,
        courseId=draft.course_id,
        semesterId=draft.semester_id,
        selectedTimeWindowId=draft.selected_time_window_id,
        sessions=[
            DraftSessionResponse(
                id=session.id,
                date=session.date,
                startTime=session.start_time.strftime("%H:%M"),
                endTime=session.end_time.strftime("%H:%M"),
                units=session.units,
                timeWindowId=session.time_window_id,
            )
            for session in draft.sessions
        ],
    )
