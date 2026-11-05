"""Single-process teaching operations; durable receipts, memory-only candidates."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from threading import RLock, Thread
from time import monotonic, sleep

from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.models.planning import OptimizationOperation, PlannerAccount, PlannerSession, Semester
from app.schemas.conflict_aware_generation import OptimizationOperationStatus, OptimizationGenerationResult, OptimizationSummary, CourseOptimizationOutcome
from app.services import conflict_aware_generation as generation
from app.services.optimization_config import load_optimization_policy
from app.services.optimization_worker import DetachedOptimizationInput, SolverProcess
from app.services.schedule_lifecycle import claim_active_working_revision, require_active_working_revision, LifecycleFailure
from app.services.planning_outcomes import retain_planning_outcome

TERMINAL = {'saved', 'cancelled', 'timeout_no_candidate', 'failed', 'stale', 'interrupted'}


class OperationFailure(RuntimeError):
    def __init__(self, code, message, status=409):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


@dataclass
class LiveOperation:
    engine: object
    request: object
    started: float
    deadline: float
    lock: object = field(default_factory=RLock)
    worker: object = None
    solution: object = None
    review: object = None
    objective: str | None = None
    discarded: bool = False
    transient_phase: str | None = None
    errors: list = field(default_factory=list)


_registry = {}
_registry_lock = RLock()


def _key(db, operation_id):
    return (id(db.get_bind()), str(operation_id))


def _digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _aware(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _origin_current(db, row, auth):
    session = db.get(PlannerSession, row.originating_session_id, populate_existing=True)
    account = db.get(PlannerAccount, row.owner_account_id, populate_existing=True)
    now = datetime.now(timezone.utc)
    return bool(
        session and account and account.is_active
        and session.account_id == row.owner_account_id
        and auth.session.id == row.originating_session_id
        and hmac.compare_digest(session.secret_digest, row.originating_session_secret_digest)
        and hmac.compare_digest(auth.secret_digest, row.originating_session_secret_digest)
        and now < _aware(session.absolute_expires_at)
        and now < _aware(session.last_activity_at) + timedelta(minutes=60)
    )


def _owned(db, operation_id, auth):
    row = db.get(OptimizationOperation, str(operation_id), populate_existing=True)
    if row is None or row.owner_account_id != auth.account.id:
        raise OperationFailure('OPERATION_NOT_FOUND', 'Der Optimierungslauf wurde nicht gefunden.', 404)
    return row


def _live_allowed(db, row, live, auth, secret):
    return bool(live and not live.discarded and secret
        and hmac.compare_digest(row.context_secret_digest, _digest(secret))
        and _origin_current(db, row, auth))


def get_status(db, operation_id, auth, secret=None):
    row = _owned(db, operation_id, auth)
    live = _registry.get(_key(db, operation_id))
    elapsed = row.elapsed_milliseconds
    if live and row.phase not in TERMINAL:
        elapsed = max(0, int((monotonic() - live.started) * 1000))
    allowed = _live_allowed(db, row, live, auth, secret) if row.phase not in TERMINAL else False
    phase = live.transient_phase if live and live.transient_phase and row.phase not in TERMINAL else row.phase
    review = live.review if allowed and phase in ('awaiting_decision', 'ready_to_save') else None
    return OptimizationOperationStatus(
        operationId=row.operation_id, semesterId=row.semester_id,
        scheduleRevisionId=row.schedule_revision_id, selectedCourseIds=row.selected_course_ids,
        selectionCount=len(row.selected_course_ids), phase=phase,
        budgetSeconds=row.budget_seconds, elapsedMilliseconds=elapsed,
        budgetExhausted=row.budget_exhausted or bool(live and row.phase in ('preparing','optimizing') and monotonic() >= live.deadline),
        currentObjectiveKey=live.objective if live and row.phase == 'optimizing' else None,
        saved=row.phase == 'saved', canAccept=review is not None and phase == 'awaiting_decision',
        canFinalize=review is not None and phase == 'ready_to_save', review=review,
        result=row.saved_result, terminalCode=row.terminal_code,
        errors=live.errors if live else [],
    )


def _check_prepared(db, request):
    require_active_working_revision(db, request.semester_id, request.schedule_revision_id)
    loaded = generation.load_operation(db, request.semester_id,
        [c.course_id for c in request.courses], request.unavailable_dates, request.schedule_revision_id)
    supplied = {c.course_id: c for c in request.courses}
    if (len(supplied) != len(request.courses) or len(loaded.courses) != len(supplied)
        or loaded.shared_snapshot_token != request.shared_snapshot_token
        or list(loaded.unavailable_dates) != request.unavailable_dates):
        raise OperationFailure('STALE_PLANNING_INPUT', 'Die Planungsdaten haben sich geändert. Bitte neu erzeugen.')
    for item in loaded.courses:
        expected = supplied[item.course.id]
        if (expected.input_snapshot_token != item.input_snapshot_token
            or expected.expected_draft_schedule_id != (item.draft.id if item.draft else None)
            or expected.expected_draft_revision != (item.draft.revision if item.draft else None)):
            raise OperationFailure('STALE_PLANNING_INPUT', 'Die Planungsdaten haben sich geändert. Bitte neu erzeugen.')
        unavailable = generation._unavailable_selection_error(db, item, request.semester_id)
        if unavailable:
            raise OperationFailure(unavailable.code, unavailable.message, 422)
    return loaded


def start_operation(db, request, auth):
    operation_id = str(request.operation_id)
    payload = request.preparation.model_dump(by_alias=True, mode='json')
    payload['courses'].sort(key=lambda course: course['courseId'])
    fingerprint = _digest(json.dumps(payload, sort_keys=True, separators=(',', ':')))
    with _registry_lock:
        existing = db.get(OptimizationOperation, operation_id, populate_existing=True)
        if existing:
            if (existing.owner_account_id != auth.account.id
                or existing.request_fingerprint != fingerprint
                or existing.context_secret_digest != _digest(request.context_secret)
                or not _origin_current(db, existing, auth)):
                raise OperationFailure('OPERATION_ID_CONFLICT', 'Diese Laufkennung kann nicht erneut verwendet werden.')
            return get_status(db, operation_id, auth, request.context_secret)
        policy = load_optimization_policy()
        if policy.policy_fingerprint != request.policy_fingerprint:
            raise OperationFailure('BUDGET_POLICY_CHANGED', 'Das Zeitbudget wurde geändert. Bitte die Auswahl neu vorbereiten.')
        require_active_working_revision(db, request.preparation.semester_id, request.preparation.schedule_revision_id)
        started = monotonic()
        row = OptimizationOperation(
            operation_id=operation_id, owner_account_id=auth.account.id,
            originating_session_id=auth.session.id, originating_session_secret_digest=auth.secret_digest,
            context_secret_digest=_digest(request.context_secret), request_fingerprint=fingerprint,
            semester_id=request.preparation.semester_id, schedule_revision_id=request.preparation.schedule_revision_id,
            selected_course_ids=sorted(c.course_id for c in request.preparation.courses),
            budget_seconds=policy.default_seconds, captured_ceiling_seconds=policy.ceiling_seconds,
            policy_fingerprint=policy.policy_fingerprint, phase='preparing',
            started_at=datetime.now(timezone.utc), elapsed_milliseconds=0,
        )
        db.add(row)
        db.commit()
        live = LiveOperation(db.get_bind(), request.preparation, started, started + policy.default_seconds)
        _registry[_key(db, operation_id)] = live
        try:
            Thread(target=_run, args=(operation_id, live), daemon=True).start()
        except Exception:
            _finish(db, row, live, 'failed', 'OPTIMIZATION_DISPATCH_FAILED')
            db.commit()
    return get_status(db, operation_id, auth, request.context_secret)


def _finish(db, row, live, phase, code=None):
    row.budget_exhausted = row.budget_exhausted or (row.phase in ('preparing','optimizing') and monotonic() >= live.deadline)
    row.phase, row.terminal_code = phase, code
    row.finished_at = datetime.now(timezone.utc)
    row.elapsed_milliseconds = max(0, int((monotonic() - live.started) * 1000))
    live.discarded = True
    live.transient_phase = None
    live.solution = live.review = None
    if live.worker:
        live.worker.close()
        live.worker = None


def _run(operation_id, live):
    factory = sessionmaker(bind=live.engine, expire_on_commit=False)
    try:
        with factory() as db:
            loaded = _check_prepared(db, live.request)
            problem = DetachedOptimizationInput(tuple(c.optimization for c in loaded.courses),
                loaded.fixed_sessions, loaded.unavailable_dates, loaded.holidays, live.deadline)
        with live.lock:
            if live.discarded: return
            try:
                live.worker = SolverProcess(problem)
            except Exception as exc:
                raise OperationFailure('OPTIMIZATION_DISPATCH_FAILED', 'Der Solverprozess konnte nicht gestartet werden.', 500) from exc
            with factory() as db:
                row = db.get(OptimizationOperation, operation_id)
                row.phase = 'optimizing'
                db.commit()
        solution = None
        checkpoint = None
        search_exhausted = False
        while True:
            with live.lock:
                if live.discarded: return
                try:
                    messages = live.worker.receive()
                    alive = live.worker.is_alive()
                    if not alive:
                        messages.extend(live.worker.receive())
                except Exception as exc:
                    raise OperationFailure('OPTIMIZATION_WORKER_FAILED', 'Die Verbindung zum Solverprozess ist abgebrochen.', 500) from exc
                completed = False
                for message in messages:
                    if message['kind'] == 'objective': live.objective = message['objectiveKey']
                    elif message['kind'] == 'checkpoint': checkpoint = message['result']
                    elif message['kind'] == 'result': solution = message['result']; completed = True
                    elif message['kind'] == 'failed': raise OperationFailure(message['code'], 'Die Optimierung ist fehlgeschlagen.', 500)
                    elif message['kind'] == 'timeout':
                        live.errors = message.get('errors', [])
                        search_exhausted = message.get('budgetExhausted', monotonic() >= live.deadline)
                        completed = True
                if completed: break
                if not alive:
                    raise OperationFailure('OPTIMIZATION_WORKER_FAILED', 'Der Solverprozess wurde unerwartet beendet.', 500)
                if monotonic() >= live.deadline:
                    search_exhausted = True
                    break
            sleep(.02)
        with live.lock:
            if live.discarded: return
            solution = solution or checkpoint
            live.worker.close()
            live.worker = None
            with factory() as db:
                row = db.get(OptimizationOperation, operation_id)
                row.budget_exhausted = search_exhausted or bool(solution and solution.search_exhausted)
                if solution is None or (not solution.optimal and solution.total_units <= 0):
                    _finish(db, row, live, 'timeout_no_candidate', 'NO_USABLE_CANDIDATE')
                    db.commit()
                    return
                row.phase = 'checking'
                db.commit()
                loaded = _check_prepared(db, live.request)
                generation.validate_exact_candidate(tuple(c.optimization for c in loaded.courses),
                    loaded.fixed_sessions, loaded.unavailable_dates, loaded.holidays, solution.courses)
                live.solution = solution
                live.review = generation._decision_required_result(db, loaded, solution,
                    live.request.courses, live.request.shared_snapshot_token, live.request.schedule_revision_id)
                row.phase = 'ready_to_save' if live.review.proof.preferences_proven and all(not c.draft or not c.draft.sessions for c in loaded.courses) else 'awaiting_decision'
                db.commit()
    except Exception as exc:
        with live.lock:
            if live.discarded: return
            with factory() as db:
                row = db.get(OptimizationOperation, operation_id)
                if row and row.phase not in TERMINAL:
                    stale = isinstance(exc, LifecycleFailure) or (isinstance(exc, OperationFailure) and exc.code == 'STALE_PLANNING_INPUT')
                    _finish(db, row, live, 'stale' if stale else 'failed',
                        'STALE_PLANNING_INPUT' if stale else exc.code if isinstance(exc, OperationFailure) else 'OPTIMIZATION_OPERATION_FAILED')
                    db.commit()


def apply_operation(db, operation_id, auth, secret, fingerprint, *, finalize=False):
    operation_id = str(operation_id)
    row = _owned(db, operation_id, auth)
    if row.phase == 'saved': return get_status(db, operation_id, auth)
    live = _registry.get(_key(db, operation_id))
    if not _live_allowed(db, row, live, auth, secret):
        raise OperationFailure('REVIEW_CONTEXT_LOST', 'Der Vergleich ist nicht mehr verfügbar. Bitte neu erzeugen.')
    with live.lock:
        try:
            live.transient_phase = 'saving'
            # Physical write claim closes validation/apply and publication races.
            db.execute(update(Semester).where(Semester.id == row.semester_id).values(id=Semester.id))
            row = _owned(db, operation_id, auth)
            if row.phase == 'saved': return get_status(db, operation_id, auth)
            expected_phase = 'ready_to_save' if finalize else 'awaiting_decision'
            if row.phase != expected_phase or not _live_allowed(db, row, live, auth, secret):
                raise OperationFailure('REVIEW_CONTEXT_LOST', 'Dieser Vergleich kann nicht übernommen werden.')
            if not live.review or live.review.candidate_fingerprint != fingerprint:
                raise OperationFailure('CANDIDATE_MISMATCH', 'Der Vergleich stimmt nicht mit dem erzeugten Ergebnis überein.')
            claim_active_working_revision(db, row.semester_id, row.schedule_revision_id)
            loaded = _check_prepared(db, live.request)
            solution = live.solution
            generation.validate_exact_candidate(tuple(c.optimization for c in loaded.courses),
                loaded.fixed_sessions, loaded.unavailable_dates, loaded.holidays, solution.courses)
            if finalize and (not live.review.proof.preferences_proven or any(c.draft and c.draft.sessions for c in loaded.courses)):
                raise OperationFailure('EXPLICIT_ACCEPTANCE_REQUIRED', 'Bitte den erzeugten Stundenplan ausdrücklich prüfen und übernehmen.')
            outcomes = []
            solved = {c.course_id: c for c in solution.courses}
            comparisons = {c.course_id: c for c in live.review.comparison.courses}
            for item in loaded.courses:
                candidate = solved[item.course.id]
                if candidate.sessions:
                    draft = generation.replace_draft_schedule(db, item.plan, row.semester_id,
                        list(candidate.sessions), existing_draft=item.draft, reload=False)
                else:
                    if item.draft: db.delete(item.draft)
                    draft = None
                outcomes.append(CourseOptimizationOutcome(
                    courseId=item.course.id, courseName=item.course.name,
                    status='complete' if candidate.scheduled_units >= item.course.total_units else 'improved_partial',
                    draftScheduleId=draft.id if draft else None, draftRevision=draft.revision if draft else None,
                    scheduledUnits=candidate.scheduled_units, remainingUnits=max(item.course.total_units-candidate.scheduled_units,0),
                    saved=True, improvement=None, reasons=comparisons[item.course.id].remaining_reasons,
                    errors=[],
                ))
            result = OptimizationGenerationResult(semesterId=row.semester_id, outcomes=outcomes, proof=live.review.proof,
                summary=OptimizationSummary(total=len(outcomes), complete=sum(o.status == 'complete' for o in outcomes),
                    improvedPartial=sum(o.status == 'improved_partial' for o in outcomes), unchanged=0, failed=0, stale=0,
                    scheduledUnits=sum(o.scheduled_units for o in outcomes), remainingUnits=sum(o.remaining_units for o in outcomes),
                    elapsedMilliseconds=max(0,int((monotonic()-live.started)*1000)), optimalForPreparedSnapshot=solution.optimal))
            for outcome in outcomes:
                retain_planning_outcome(db, schedule_revision_id=row.schedule_revision_id, course_id=outcome.course_id,
                    operation_kind='semester_optimization', classification='successful', source_status=str(outcome.status),
                    result_payload=outcome.model_dump(by_alias=True,mode='json'), completed_at=datetime.now(timezone.utc))
            row.saved_result = result.model_dump(by_alias=True, mode='json')
            _finish(db, row, live, 'saved')
            db.commit()
        except Exception as exc:
            db.rollback()
            row = _owned(db, operation_id, auth)
            if row.phase == 'saved': return get_status(db, operation_id, auth)
            if isinstance(exc, OperationFailure) and exc.code in ('CANDIDATE_MISMATCH', 'REVIEW_CONTEXT_LOST', 'EXPLICIT_ACCEPTANCE_REQUIRED'):
                raise
            stale = isinstance(exc, LifecycleFailure) or (isinstance(exc, OperationFailure) and exc.code == 'STALE_PLANNING_INPUT')
            _finish(db, row, live, 'stale' if stale else 'failed', 'STALE_PLANNING_INPUT' if stale else 'OPTIMIZATION_APPLICATION_FAILED')
            db.commit()
            raise OperationFailure(row.terminal_code, 'Die Planungsdaten haben sich geändert. Bitte neu erzeugen.' if stale else 'Der Stundenplan konnte nicht gespeichert werden.', 409 if stale else 500) from exc
        finally:
            live.transient_phase = None
    return get_status(db, operation_id, auth)


def cancel_operation(db, operation_id, auth):
    row = _owned(db, str(operation_id), auth)
    live = _registry.get(_key(db, operation_id))
    with live.lock if live else _registry_lock:
        db.execute(update(Semester).where(Semester.id == row.semester_id).values(id=Semester.id))
        row = _owned(db, operation_id, auth)
        if row.phase not in TERMINAL:
            if live: _finish(db, row, live, 'cancelled')
            else:
                row.phase, row.finished_at = 'cancelled', datetime.now(timezone.utc)
            db.commit()
        else: db.rollback()
    return get_status(db, operation_id, auth)


def shutdown_operations(engine):
    factory = sessionmaker(bind=engine)
    for key, live in list(_registry.items()):
        if live.engine is not engine: continue
        with live.lock:
            with factory() as db:
                row = db.get(OptimizationOperation, key[1])
                if row and row.phase not in TERMINAL:
                    _finish(db, row, live, 'interrupted', 'OPERATION_INTERRUPTED')
                    db.commit()
            _registry.pop(key, None)


def recover_operations(db):
    db.execute(update(OptimizationOperation).where(OptimizationOperation.phase.not_in(TERMINAL)).values(
        phase='interrupted', finished_at=datetime.now(timezone.utc), terminal_code='OPERATION_INTERRUPTED'))
    db.commit()
