import re
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.planning import CourseEligibleLecturer, CourseEligibleRoom, Lecturer, ResourceUnavailabilityPeriod, Room, Semester
from app.schemas.draft_schedule import (
    AllowedTeachingWindowResponse,
    DraftScheduleContextResponse,
    DraftScheduleMutationResponse,
    DraftScheduleResponse,
    DraftSessionResponse,
    GenerateDraftScheduleRequest,
    GenerationConstraintsResponse,
    GenerationFailure,
    FailureCode,
    GenerationFailureResponse,
    PlanningEntityResponse,
    PlanningResourceResponse,
    PlanningPeriodResponse,
    RelatedSessionResponse,
    SessionEditFailure,
    SessionEditFailureCode,
    SessionEditFailureResponse,
    StaleDraftFailure,
    StaleDraftResponse,
    CreateManualDraftSessionRequest,
    ManualSessionFailure,
    ManualSessionFailureCode,
    ManualSessionFailureResponse,
    UpdateDraftSessionRequest,
    ValidationAlertResponse,
)
from app.services.draft_schedule_repository import (
    DraftSessionEditValidationError,
    ManualSessionValidationError,
    StaleDraftError,
    GenerationConstraints,
    PlanningInputNotFoundError,
    clear_generation_constraints,
    clear_course_draft,
    course_semester_progress,
    create_manual_draft_session,
    delete_draft_session,
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
from app.services.holiday_calendar import holiday_snapshot

router = APIRouter(prefix="/api/courses/{course_id}/draft-schedule", tags=["draft schedule"])
constraints_router = APIRouter(
    prefix="/api/courses/{course_id}/generation-constraints",
    tags=["draft schedule"],
)
overview_router = APIRouter(prefix="/api/draft-schedules", tags=["draft schedule"])
session_router = APIRouter(prefix="/api/draft-sessions", tags=["draft schedule"])
_MANUAL_SESSION_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_MANUAL_SESSION_TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


@router.post(
    "/sessions",
    response_model=DraftScheduleMutationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ManualSessionFailureResponse}},
)
def create_manual_session(
    course_id: int,
    request: CreateManualDraftSessionRequest,
    db: Session = Depends(get_db),
) -> DraftScheduleMutationResponse | JSONResponse:
    try:
        session_date = _parse_manual_session_date(request.date)
    except ValueError:
        return _manual_failure("INVALID_SESSION_DATE", "Session date must use a valid YYYY-MM-DD value.")
    try:
        start_time = _parse_manual_session_time(request.start_time)
        end_time = _parse_manual_session_time(request.end_time)
    except ValueError:
        return _manual_failure("INVALID_SESSION_TIME_RANGE", "Session start and end times must use HH:MM values.")
    try:
        draft = create_manual_draft_session(
            db,
            course_id,
            request.semester_id,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            units=request.units,
            room_id=request.room_id,
        )
        db.commit()
    except ManualSessionValidationError as exc:
        db.rollback()
        return _manual_failure(exc.code, exc.message)
    except PlanningInputNotFoundError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise
    return _to_mutation_response(db, course_id, request.semester_id, draft)


@session_router.delete(
    "/{session_id}",
    response_model=DraftScheduleMutationResponse,
    responses={409: {"model": StaleDraftResponse}},
)
def remove_draft_session(
    session_id: int,
    expectedDraftScheduleId: int,
    expectedDraftRevision: int,
    db: Session = Depends(get_db),
) -> DraftScheduleMutationResponse | JSONResponse:
    try:
        draft, course_id, semester_id = delete_draft_session(
            db,
            session_id,
            expected_draft_schedule_id=expectedDraftScheduleId,
            expected_revision=expectedDraftRevision,
        )
        db.commit()
    except StaleDraftError as exc:
        db.rollback()
        return _stale_response(exc.current_revision)
    except Exception:
        db.rollback()
        raise
    return _to_mutation_response(db, course_id, semester_id, draft)


@router.delete(
    "",
    response_model=DraftScheduleMutationResponse,
    responses={409: {"model": StaleDraftResponse}},
)
def remove_course_draft(
    course_id: int,
    semesterId: int,
    expectedDraftScheduleId: int,
    expectedDraftRevision: int,
    db: Session = Depends(get_db),
) -> DraftScheduleMutationResponse | JSONResponse:
    try:
        course_id, semester_id = clear_course_draft(
            db,
            course_id,
            semesterId,
            expected_draft_schedule_id=expectedDraftScheduleId,
            expected_revision=expectedDraftRevision,
        )
        db.commit()
    except StaleDraftError as exc:
        db.rollback()
        return _stale_response(exc.current_revision)
    except Exception:
        db.rollback()
        raise
    return _to_mutation_response(db, course_id, semester_id, None)


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
    if any(link.room.is_active for link in source_course.eligible_rooms):
        eligibility = [reason for reason in eligibility if reason != "NO_USABLE_ELIGIBLE_ROOM"]
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
    holidays = holiday_snapshot(db, planning_period.start_date, planning_period.end_date)

    result = generate_schedule(
        course=course,
        semester=semester,
        planning_period=planning_period,
        time_windows=time_windows,
        holidays=holidays.by_date,
    )
    if not result.ok:
        current_holidays = holiday_snapshot(db, planning_period.start_date, planning_period.end_date)
        if current_holidays.token != holidays.token:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=GenerationFailureResponse(errors=[GenerationFailure(
                    code=FailureCode.STALE_HOLIDAY_CALENDAR,
                    message="The holiday calendar changed during generation. Review the current calendar and retry.",
                )]).model_dump(mode="json", by_alias=True, exclude_none=True),
            )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=GenerationFailureResponse(errors=result.errors).model_dump(mode="json", by_alias=True, exclude_none=True),
        )
    try:
        # SQLite defers its physical transaction until the first write. Establish
        # the write boundary before the final holiday reload and hold it through
        # persistence so a holiday change cannot commit in between them.
        db.execute(update(Semester).where(Semester.id == semester.id).values(id=Semester.id))
        current_holidays = holiday_snapshot(db, planning_period.start_date, planning_period.end_date)
        conflicting = next((session.date for session in result.sessions if session.date in current_holidays.by_date), None)
        if conflicting is not None:
            holiday = current_holidays.by_date[conflicting]
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=GenerationFailureResponse(errors=[GenerationFailure(
                    code=FailureCode.STALE_HOLIDAY_CALENDAR,
                    message=f"The holiday calendar changed. {holiday.name} on {holiday.date.isoformat()} now conflicts with this result; retry generation.",
                )]).model_dump(mode="json", by_alias=True, exclude_none=True),
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
            lecturer_id=request.lecturer_id,
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


def _to_mutation_response(db: Session, course_id: int, semester_id: int, draft) -> DraftScheduleMutationResponse:
    _total, scheduled, remaining = course_semester_progress(db, course_id, semester_id)
    return DraftScheduleMutationResponse(
        courseId=course_id,
        semesterId=semester_id,
        scheduledUnits=scheduled,
        remainingUnits=remaining,
        draftSchedule=_to_response_with_validation(db, draft) if draft is not None else None,
    )


def _manual_failure(code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ManualSessionFailureResponse(
            errors=[ManualSessionFailure(code=ManualSessionFailureCode(code), message=message)]
        ).model_dump(mode="json"),
    )


def _parse_manual_session_date(value: str) -> date:
    if _MANUAL_SESSION_DATE_PATTERN.fullmatch(value) is None:
        raise ValueError("Manual Draft Session dates must use YYYY-MM-DD.")
    return date.fromisoformat(value)


def _parse_manual_session_time(value: str) -> time:
    if _MANUAL_SESSION_TIME_PATTERN.fullmatch(value) is None:
        raise ValueError("Manual Draft Session times must use HH:MM.")
    return time.fromisoformat(value)


def _stale_response(current_revision: int | None) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=StaleDraftResponse(
            errors=[
                StaleDraftFailure(
                    message="The confirmed Draft Schedule changed. Refresh and confirm again.",
                    currentRevision=current_revision,
                )
            ]
        ).model_dump(by_alias=True, mode="json"),
    )


def _to_responses_with_validation(db: Session, drafts) -> list[DraftScheduleResponse]:
    rooms_by_id = {room.id: room for room in db.execute(select(Room)).scalars().all()}
    lecturers_by_id = {lecturer.id: lecturer for lecturer in db.execute(select(Lecturer)).scalars().all()}
    constraints_by_course_id = {}
    study_windows_by_study_type_id = {}
    unavailability_by_resource = {}
    for period in db.execute(select(ResourceUnavailabilityPeriod).options(selectinload(ResourceUnavailabilityPeriod.weekdays))).scalars().all():
        key = ("lecturer", period.lecturer_id) if period.lecturer_id is not None else ("room", period.room_id)
        unavailability_by_resource.setdefault(key, []).append(period)
    if drafts:
        semester_plan = load_semester_plan(db, drafts[0].semester_id)
        for draft in drafts:
            course_plan = load_course_plan(db, draft.course_id)
            constraints_by_course_id[draft.course_id] = load_generation_constraints(db, course_plan, semester_plan)
            study_type_id = draft.study_type_id_snapshot
            if study_type_id not in study_windows_by_study_type_id:
                study_windows_by_study_type_id[study_type_id] = load_time_windows(db, study_type_id)
        holidays_by_date = holiday_snapshot(
            db,
            semester_plan.start_date,
            semester_plan.end_date,
        ).by_date
    else:
        holidays_by_date = {}
    alerts_by_session = collect_validation_alerts(
        list(drafts),
        rooms_by_id=rooms_by_id,
        lecturers_by_id=lecturers_by_id,
        constraints_by_course_id=constraints_by_course_id,
        study_windows_by_study_type_id=study_windows_by_study_type_id,
        unavailability_by_resource=unavailability_by_resource,
        eligible_lecturer_ids_by_course={draft.course_id: {link.lecturer_id for link in draft.course.eligible_lecturers} for draft in drafts},
        eligible_room_ids_by_course={draft.course_id: {link.room_id for link in draft.course.eligible_rooms} for draft in drafts},
        active_lecturer_ids=set(db.execute(select(Lecturer.id).where(Lecturer.is_active.is_(True))).scalars()),
        active_room_ids={room.id for room in rooms_by_id.values() if room.is_active},
        current_cohort_sizes_by_course={
            draft.course_id: draft.course.cohort.student_count for draft in drafts
        },
        holidays_by_date=holidays_by_date,
    )
    return [_to_response(draft, alerts_by_session=alerts_by_session, rooms_by_id=rooms_by_id, lecturers_by_id=lecturers_by_id) for draft in drafts]


def _to_response(draft, alerts_by_session=None, rooms_by_id=None, lecturers_by_id=None) -> DraftScheduleResponse:
    course = draft.course
    alerts_by_session = alerts_by_session or {}
    rooms_by_id = rooms_by_id or {}
    lecturers_by_id = lecturers_by_id or {}
    first_session = draft.sessions[0] if draft.sessions else None
    context_lecturer = lecturers_by_id.get(first_session.lecturer_id) if first_session else course.lecturer
    context_room = rooms_by_id.get(first_session.room_id) if first_session else course.room
    return DraftScheduleResponse(
        draftScheduleId=draft.id,
        revision=draft.revision,
        courseId=draft.course_id,
        semesterId=draft.semester_id,
        context=DraftScheduleContextResponse(
            course=PlanningEntityResponse(id=course.id, name=draft.course_name_snapshot),
            cohort=PlanningEntityResponse(id=draft.cohort_id_snapshot, name=draft.cohort_name_snapshot),
            cohortSize=draft.cohort_size_snapshot,
            lecturer=PlanningEntityResponse(id=context_lecturer.id, name=context_lecturer.name),
            room=PlanningEntityResponse(id=context_room.id, name=context_room.name),
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
                lecturerName=lecturers_by_id.get(session.lecturer_id).name if lecturers_by_id.get(session.lecturer_id) is not None else f"Lecturer {session.lecturer_id}",
                lecturerReferenceCode=lecturers_by_id.get(session.lecturer_id).reference_code if lecturers_by_id.get(session.lecturer_id) is not None else "UNKNOWN",
                cohortId=session.cohort_id,
                roomId=session.room_id,
                roomName=rooms_by_id.get(session.room_id).name if rooms_by_id.get(session.room_id) is not None else f"Room {session.room_id}",
                roomReferenceCode=rooms_by_id.get(session.room_id).reference_code if rooms_by_id.get(session.room_id) is not None else "UNKNOWN",
                studyTypeId=draft.study_type_id_snapshot,
                timeWindowId=session.time_window_id,
                constraintWindowIndex=session.constraint_window_index,
                lecturer=_planning_resource(lecturers_by_id.get(session.lecturer_id), "Lecturer", session.lecturer_id),
                room=_planning_resource(rooms_by_id.get(session.room_id), "Room", session.room_id),
                validationAlerts=[
                    _validation_alert_to_response(alert)
                    for alert in alerts_by_session.get(session.id, [])
                ],
            )
            for session in draft.sessions
        ],
    )


def _planning_resource(resource, label: str, resource_id: int) -> PlanningResourceResponse:
    return PlanningResourceResponse(
        id=resource_id,
        name=resource.name if resource is not None else f"{label} {resource_id}",
        referenceCode=resource.reference_code if resource is not None else "UNKNOWN",
    )


def _validation_alert_to_response(alert: ValidationAlert) -> ValidationAlertResponse:
    return ValidationAlertResponse(
        code=alert.code.value,
        message=alert.message,
        holidayDate=alert.holiday_date,
        holidayName=alert.holiday_name,
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
