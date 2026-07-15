from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.planning import Room
from app.schemas.draft_schedule import (
    AllowedTeachingWindowResponse,
    DraftScheduleContextResponse,
    DraftScheduleResponse,
    DraftSessionResponse,
    GenerateDraftScheduleRequest,
    GenerationConstraintsResponse,
    GenerationFailureResponse,
    PlanningEntityResponse,
    PlanningPeriodResponse,
    RelatedSessionResponse,
    SessionEditFailure,
    SessionEditFailureCode,
    SessionEditFailureResponse,
    UpdateDraftSessionRequest,
    ValidationAlertResponse,
)
from app.services.draft_schedule_repository import (
    DraftSessionEditValidationError,
    GenerationConstraints,
    PlanningInputNotFoundError,
    clear_generation_constraints,
    get_draft_schedule,
    list_draft_schedules_by_semester,
    load_generation_constraints,
    load_course_plan,
    load_semester_plan,
    load_time_windows,
    replace_draft_schedule,
    save_generation_constraints,
    update_draft_session,
)
from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan, generate_schedule
from app.models.planning import Course
from app.services.academic_catalog import planning_eligibility_reasons
from app.services.draft_schedule_validation import (
    ValidationAlert,
    collect_validation_alerts,
)

router = APIRouter(prefix="/api/courses/{course_id}/draft-schedule", tags=["draft schedule"])
constraints_router = APIRouter(
    prefix="/api/courses/{course_id}/generation-constraints",
    tags=["draft schedule"],
)
overview_router = APIRouter(prefix="/api/draft-schedules", tags=["draft schedule"])
session_router = APIRouter(prefix="/api/draft-sessions", tags=["draft schedule"])


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
    source_course = db.get(Course, course_id)
    eligibility = planning_eligibility_reasons(db, source_course, request.semester_id)
    if eligibility:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": [{"code": code, "message": "Course academic data is not eligible for this Semester."} for code in eligibility]},
        )
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
    try:
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
        db.commit()
    except Exception:
        db.rollback()
        raise
    return _to_response_with_validation(db, draft)


@router.get("", response_model=DraftScheduleResponse)
def read_draft_schedule(
    course_id: int,
    semesterId: int,
    db: Session = Depends(get_db),
) -> DraftScheduleResponse:
    draft = get_draft_schedule(db, course_id, semesterId)
    if draft is None:
        raise HTTPException(status_code=404, detail="No generated draft schedule exists.")
    return _to_response_with_validation(db, draft)


@overview_router.get("", response_model=list[DraftScheduleResponse])
def read_draft_schedules(semesterId: int, db: Session = Depends(get_db)) -> list[DraftScheduleResponse]:
    try:
        load_semester_plan(db, semesterId)
    except PlanningInputNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_responses_with_validation(db, list_draft_schedules_by_semester(db, semesterId))


@session_router.patch(
    "/{session_id}",
    response_model=DraftScheduleResponse,
    responses={422: {"model": SessionEditFailureResponse}},
)
def edit_draft_session(
    session_id: int,
    request: UpdateDraftSessionRequest,
    db: Session = Depends(get_db),
) -> DraftScheduleResponse | JSONResponse:
    try:
        draft = update_draft_session(
            db,
            session_id,
            date=_parse_date(request.date),
            start_time=_parse_edit_time(request.start_time),
            end_time=_parse_edit_time(request.end_time),
            room_id=request.room_id,
        )
        db.commit()
    except DraftSessionEditValidationError as exc:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=SessionEditFailureResponse(
                errors=[
                    SessionEditFailure(
                        code=SessionEditFailureCode(exc.code),
                        message=exc.message,
                    )
                ]
            ).model_dump(mode="json"),
        )
    except PlanningInputNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response_with_validation(db, draft)


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
    eligibility = planning_eligibility_reasons(db, db.get(Course, course_id), semesterId)
    if eligibility:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": [{"code": code, "message": "Course academic data is not eligible for this Semester."} for code in eligibility]},
        )
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
    eligibility = planning_eligibility_reasons(db, db.get(Course, course_id), semesterId)
    if eligibility:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": [{"code": code, "message": "Course academic data is not eligible for this Semester."} for code in eligibility]},
        )
    try:
        clear_generation_constraints(db, course_id=course_id, semester_id=semesterId)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _to_response_with_validation(db: Session, draft) -> DraftScheduleResponse:
    semester_drafts = list_draft_schedules_by_semester(db, draft.semester_id)
    responses = _to_responses_with_validation(db, semester_drafts)
    for response in responses:
        if response.draft_schedule_id == draft.id:
            return response
    return _to_response(draft)


def _to_responses_with_validation(db: Session, drafts) -> list[DraftScheduleResponse]:
    rooms_by_id = {room.id: room for room in db.execute(select(Room)).scalars().all()}
    constraints_by_course_id = {}
    study_windows_by_study_type_id = {}
    if drafts:
        semester_plan = load_semester_plan(db, drafts[0].semester_id)
        for draft in drafts:
            course_plan = load_course_plan(db, draft.course_id)
            constraints_by_course_id[draft.course_id] = load_generation_constraints(db, course_plan, semester_plan)
            study_type_id = draft.study_type_id_snapshot
            if study_type_id not in study_windows_by_study_type_id:
                study_windows_by_study_type_id[study_type_id] = load_time_windows(db, study_type_id)
    alerts_by_session = collect_validation_alerts(
        list(drafts),
        rooms_by_id=rooms_by_id,
        constraints_by_course_id=constraints_by_course_id,
        study_windows_by_study_type_id=study_windows_by_study_type_id,
    )
    return [_to_response(draft, alerts_by_session=alerts_by_session, rooms_by_id=rooms_by_id) for draft in drafts]


def _to_response(draft, alerts_by_session=None, rooms_by_id=None) -> DraftScheduleResponse:
    course = draft.course
    alerts_by_session = alerts_by_session or {}
    rooms_by_id = rooms_by_id or {}
    return DraftScheduleResponse(
        draftScheduleId=draft.id,
        revision=draft.revision,
        courseId=draft.course_id,
        semesterId=draft.semester_id,
        context=DraftScheduleContextResponse(
            course=PlanningEntityResponse(id=course.id, name=draft.course_name_snapshot),
            cohort=PlanningEntityResponse(id=draft.cohort_id_snapshot, name=draft.cohort_name_snapshot),
            cohortSize=draft.cohort_size_snapshot,
            lecturer=PlanningEntityResponse(id=course.lecturer.id, name=course.lecturer.name),
            room=PlanningEntityResponse(id=course.room.id, name=course.room.name),
            studyType=PlanningEntityResponse(id=draft.study_type_id_snapshot, name=draft.study_type_name_snapshot),
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
                studyTypeId=draft.study_type_id_snapshot,
                timeWindowId=session.time_window_id,
                constraintWindowIndex=session.constraint_window_index,
                validationAlerts=[
                    _validation_alert_to_response(alert)
                    for alert in alerts_by_session.get(session.id, [])
                ],
            )
            for session in draft.sessions
        ],
    )


def _validation_alert_to_response(alert: ValidationAlert) -> ValidationAlertResponse:
    return ValidationAlertResponse(
        code=alert.code.value,
        message=alert.message,
        relatedSessions=[
            RelatedSessionResponse(
                sessionId=related.session_id,
                draftScheduleId=related.draft_schedule_id,
                courseId=related.course_id,
                courseName=related.course_name,
                date=related.date,
                startTime=related.start_time,
                endTime=related.end_time,
                cohortName=related.cohort_name,
                lecturerName=related.lecturer_name,
                roomName=related.room_name,
            )
            for related in alert.related_sessions
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


def _parse_edit_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise DraftSessionEditValidationError(
            "INVALID_SESSION_TIME_RANGE",
            "Session start and end times must use HH:MM values.",
        ) from exc


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DraftSessionEditValidationError(
            "INVALID_SESSION_DATE",
            "Session date must use a valid YYYY-MM-DD value.",
        ) from exc


def _constraints_to_response(constraints: GenerationConstraints) -> GenerationConstraintsResponse:
    return GenerationConstraintsResponse(
        courseId=constraints.course_id,
        semesterId=constraints.semester_id,
        isCustom=constraints.is_custom,
        revision=constraints.revision,
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
