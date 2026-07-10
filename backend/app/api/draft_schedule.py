from datetime import time

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.draft_schedule import (
    DraftScheduleContextResponse,
    DraftScheduleResponse,
    DraftSessionResponse,
    GenerateDraftScheduleRequest,
    GenerationConstraintsResponse,
    GenerationFailureResponse,
    PlanningEntityResponse,
    PlanningPeriodResponse,
    AllowedTeachingWindowResponse,
)
from app.services.draft_schedule_repository import (
    GenerationConstraints,
    PlanningInputNotFoundError,
    clear_generation_constraints,
    get_draft_schedule,
    list_draft_schedules_by_semester,
    load_generation_constraints,
    load_course_plan,
    load_semester_plan,
    replace_draft_schedule,
    save_generation_constraints,
)
from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan, generate_schedule

router = APIRouter(prefix="/api/courses/{course_id}/draft-schedule", tags=["draft schedule"])
constraints_router = APIRouter(
    prefix="/api/courses/{course_id}/generation-constraints",
    tags=["draft schedule"],
)
overview_router = APIRouter(prefix="/api/draft-schedules", tags=["draft schedule"])


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
    except PlanningInputNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    planning_period = PlanningPeriodPlan(
        start_date=request.planning_period.start_date,
        end_date=request.planning_period.end_date,
    )
    time_windows = [_request_window_to_plan(index, window) for index, window in enumerate(request.allowed_teaching_windows)]

    result = generate_schedule(
        course=course,
        semester=semester,
        planning_period=planning_period,
        time_windows=time_windows,
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
        generated_sessions=result.sessions,
    )
    save_generation_constraints(
        db,
        course_plan=course,
        semester_plan=semester,
        planning_period=planning_period,
        allowed_windows=time_windows,
    )
    return _to_response(draft)


@router.get("", response_model=DraftScheduleResponse)
def read_draft_schedule(course_id: int, db: Session = Depends(get_db)) -> DraftScheduleResponse:
    draft = get_draft_schedule(db, course_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="No generated draft schedule exists.")
    return _to_response(draft)


@overview_router.get("", response_model=list[DraftScheduleResponse])
def read_draft_schedules(semesterId: int, db: Session = Depends(get_db)) -> list[DraftScheduleResponse]:
    try:
        load_semester_plan(db, semesterId)
    except PlanningInputNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [_to_response(draft) for draft in list_draft_schedules_by_semester(db, semesterId)]


@constraints_router.get("", response_model=GenerationConstraintsResponse)
def read_generation_constraints(
    course_id: int,
    semesterId: int,
    db: Session = Depends(get_db),
) -> GenerationConstraintsResponse:
    try:
        course = load_course_plan(db, course_id)
        semester = load_semester_plan(db, semesterId)
    except PlanningInputNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _constraints_to_response(load_generation_constraints(db, course, semester))


@constraints_router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_generation_constraints(
    course_id: int,
    semesterId: int,
    db: Session = Depends(get_db),
) -> Response:
    try:
        load_course_plan(db, course_id)
        load_semester_plan(db, semesterId)
    except PlanningInputNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    clear_generation_constraints(db, course_id=course_id, semester_id=semesterId)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _to_response(draft) -> DraftScheduleResponse:
    course = draft.course
    return DraftScheduleResponse(
        draftScheduleId=draft.id,
        courseId=draft.course_id,
        semesterId=draft.semester_id,
        context=DraftScheduleContextResponse(
            course=PlanningEntityResponse(id=course.id, name=course.name),
            cohort=PlanningEntityResponse(id=course.cohort.id, name=course.cohort.name),
            lecturer=PlanningEntityResponse(id=course.lecturer.id, name=course.lecturer.name),
            room=PlanningEntityResponse(id=course.room.id, name=course.room.name),
            studyType=PlanningEntityResponse(id=course.study_type.id, name=course.study_type.name),
        ),
        sessions=[
            DraftSessionResponse(
                id=session.id,
                date=session.date,
                startTime=session.start_time.strftime("%H:%M"),
                endTime=session.end_time.strftime("%H:%M"),
                units=session.units,
                courseId=session.course_id,
                lecturerId=session.lecturer_id,
                cohortId=session.cohort_id,
                roomId=session.room_id,
                studyTypeId=course.study_type_id,
                timeWindowId=session.time_window_id,
                constraintWindowIndex=session.constraint_window_index,
            )
            for session in draft.sessions
        ],
    )


def _request_window_to_plan(index: int, window) -> TimeWindowPlan:
    return TimeWindowPlan(
        id=window.source_time_window_id,
        weekday=window.weekday,
        start_time=_parse_time(window.start_time),
        end_time=_parse_time(window.end_time),
        sort_order=index,
        constraint_window_index=index,
    )


def _parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid time value: {value}") from exc


def _constraints_to_response(constraints: GenerationConstraints) -> GenerationConstraintsResponse:
    return GenerationConstraintsResponse(
        courseId=constraints.course_id,
        semesterId=constraints.semester_id,
        isCustom=constraints.is_custom,
        planningPeriod=PlanningPeriodResponse(
            startDate=constraints.planning_period.start_date,
            endDate=constraints.planning_period.end_date,
        ),
        allowedTeachingWindows=[
            AllowedTeachingWindowResponse(
                weekday=window.weekday,
                startTime=window.start_time.strftime("%H:%M"),
                endTime=window.end_time.strftime("%H:%M"),
                sourceTimeWindowId=window.id,
            )
            for window in constraints.allowed_windows
        ],
    )
