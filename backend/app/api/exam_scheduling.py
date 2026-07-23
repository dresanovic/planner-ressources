from datetime import time

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.db.session import get_db
from app.schemas.exam_scheduling import (
    CreateManualExamRequest,
    DeleteExamRequest,
    DeleteExamResponse,
    ExamCoursePlanningState,
    ExamGenerationPreparation,
    ExamGenerationPreparationRequest,
    ExamGenerationResult,
    ExamPlanningOverview,
    GenerateExamsRequest,
    SaveExamConfigurationRequest,
    UpdateExamRequest,
)
from app.services.exam_scheduling import (
    ExamErrorItem,
    ExamSchedulingError,
    create_manual_exam,
    delete_exam,
    generate_exams,
    get_exam_planning_overview,
    prepare_exam_generation,
    save_exam_configuration,
    update_exam,
)
from app.models.planning import ExamSession
from app.services.schedule_lifecycle import LifecycleFailure, claim_active_working_revision, require_active_working_revision
from app.api.schedule_lifecycle import lifecycle_failure_response

router = APIRouter(tags=["exam scheduling"])


def _error(exc: ExamSchedulingError):
    body = {"errors": [{"code": item.code, "message": item.message, "field": item.field} for item in exc.errors]}
    if exc.status_code == 409:
        body["currentState"] = _transport(exc.current_state)
    return JSONResponse(status_code=exc.status_code, content=_transport(body))


def _concurrent_error():
    return ExamSchedulingError(409, [ExamErrorItem("STALE_REVISION", "Exam planning state changed. Refresh and try again.")])


@router.get("/api/exam-planning", response_model=ExamPlanningOverview)
def overview(semester_id: int = Query(alias="semesterId", ge=1), db: Session = Depends(get_db)):
    try:
        return _transport(get_exam_planning_overview(db, semester_id))
    except ExamSchedulingError as exc:
        return _error(exc)


@router.put("/api/courses/{course_id}/exam-configuration", response_model=ExamCoursePlanningState)
def put_configuration(course_id: int, payload: SaveExamConfigurationRequest, db: Session = Depends(get_db)):
    try:
        state, created = save_exam_configuration(db, course_id=course_id, semester_id=payload.semester_id, enabled=payload.enabled, expected_revision=payload.expected_revision, configuration=payload.configuration.model_dump() if payload.configuration else None)
        db.commit()
        return JSONResponse(status_code=status.HTTP_201_CREATED if created else 200, content=_transport(state))
    except ExamSchedulingError as exc:
        db.rollback(); return _error(exc)
    except (IntegrityError, StaleDataError):
        db.rollback(); return _error(_concurrent_error())


@router.post("/api/exams/generation/prepare", response_model=ExamGenerationPreparation)
def prepare(payload: ExamGenerationPreparationRequest, db: Session = Depends(get_db)):
    try:
        require_active_working_revision(db, payload.semester_id, payload.schedule_revision_id)
        return _transport(prepare_exam_generation(db, payload.semester_id, payload.course_ids, schedule_revision_id=payload.schedule_revision_id))
    except LifecycleFailure as exc:
        return lifecycle_failure_response(exc)
    except ExamSchedulingError as exc:
        return _error(exc)


@router.post("/api/exams/generation", response_model=ExamGenerationResult)
def generate(payload: GenerateExamsRequest, db: Session = Depends(get_db)):
    try:
        require_active_working_revision(db, payload.semester_id, payload.schedule_revision_id)
        result = generate_exams(db, payload.model_dump(by_alias=True))
        db.commit()
        return _transport(result)
    except ExamSchedulingError as exc:
        db.rollback(); return _error(exc)
    except LifecycleFailure as exc:
        db.rollback(); return lifecycle_failure_response(exc)
    except (IntegrityError, StaleDataError):
        db.rollback(); return _error(_concurrent_error())


@router.post("/api/courses/{course_id}/exam-sessions", response_model=ExamCoursePlanningState, status_code=status.HTTP_201_CREATED)
def create_session(course_id: int, payload: CreateManualExamRequest, db: Session = Depends(get_db)):
    try:
        claim_active_working_revision(db, payload.semester_id, payload.schedule_revision_id)
        state = create_manual_exam(db, course_id=course_id, semester_id=payload.semester_id, exam_date=payload.date, start_time=time.fromisoformat(payload.start_time), lecturer_id=payload.lecturer_id, room_id=payload.room_id, expected_configuration_revision=payload.expected_configuration_revision, input_snapshot_token=payload.input_snapshot_token)
        db.commit(); return _transport(state)
    except ExamSchedulingError as exc:
        db.rollback(); return _error(exc)
    except LifecycleFailure as exc:
        db.rollback(); return lifecycle_failure_response(exc)
    except (IntegrityError, StaleDataError):
        db.rollback(); return _error(_concurrent_error())


@router.patch("/api/exam-sessions/{exam_id}", response_model=ExamCoursePlanningState)
def patch_session(exam_id: int, payload: UpdateExamRequest, db: Session = Depends(get_db)):
    try:
        source_exam = db.get(ExamSession, exam_id)
        if source_exam is None:
            raise ExamSchedulingError(404, [ExamErrorItem("EXAM_NOT_FOUND", "Exam Session not found.")])
        claim_active_working_revision(db, source_exam.semester_id, payload.schedule_revision_id)
        state = update_exam(db, exam_id, exam_date=payload.date, start_time=time.fromisoformat(payload.start_time), lecturer_id=payload.lecturer_id, room_id=payload.room_id, expected_exam_revision=payload.expected_exam_revision, input_snapshot_token=payload.input_snapshot_token)
        db.commit(); return _transport(state)
    except ExamSchedulingError as exc:
        db.rollback(); return _error(exc)
    except LifecycleFailure as exc:
        db.rollback(); return lifecycle_failure_response(exc)
    except (IntegrityError, StaleDataError):
        db.rollback(); return _error(_concurrent_error())


@router.delete("/api/exam-sessions/{exam_id}", response_model=DeleteExamResponse)
def remove_session(exam_id: int, payload: DeleteExamRequest, db: Session = Depends(get_db)):
    try:
        source_exam = db.get(ExamSession, exam_id)
        if source_exam is None:
            raise ExamSchedulingError(404, [ExamErrorItem("EXAM_NOT_FOUND", "Exam Session not found.")])
        claim_active_working_revision(db, source_exam.semester_id, payload.schedule_revision_id)
        result = delete_exam(db, exam_id, confirmed=payload.confirmed, expected_exam_revision=payload.expected_exam_revision, input_snapshot_token=payload.input_snapshot_token)
        db.commit(); return _transport(result)
    except ExamSchedulingError as exc:
        db.rollback(); return _error(exc)
    except LifecycleFailure as exc:
        db.rollback(); return lifecycle_failure_response(exc)
    except (IntegrityError, StaleDataError):
        db.rollback(); return _error(_concurrent_error())


def _transport(value):
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, dict):
        return {key: _transport(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_transport(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
