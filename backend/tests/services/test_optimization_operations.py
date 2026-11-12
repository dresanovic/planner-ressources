"""File-backed operation tests exercise real transactions and exact candidate apply."""
from types import SimpleNamespace
from time import monotonic, sleep

import pytest
from sqlalchemy.orm import sessionmaker

from app.schemas.conflict_aware_generation import OptimizationOperationStart
from app.services import optimization_operations as operations
from app.services.conflict_aware_generation import prepare_optimization, load_operation
from app.services.semester_optimization import optimize_semester
from app.models.planning import DraftSchedule, OptimizationOperation
from tests.optimization_fixtures import seed_optimization_planner, operation_start_payload, CONTEXT_SECRET
from tests.planner_auth_fixtures import file_backed_engine, add_planner_account, add_current_session
from tests.fixtures.dated_intensive_windows import ACCEPTANCE_WINDOW_CHANGES


pytestmark = pytest.mark.usefixtures("isolated_standard_policy")


@pytest.fixture(params=[False,True],ids=['first-plan-finalize','existing-plan-accept'])
def dated_acceptance_operation(tmp_path,monkeypatch,request,isolated_standard_policy):
    from tests.fixtures.dated_intensive_windows import seed_acceptance_context
    engine=file_backed_engine(tmp_path/'dated-acceptance.db')
    factory=sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as db:
        seed_acceptance_context(db,with_selected=request.param)
        account=add_planner_account(db)
        session,_=add_current_session(db,account_id=account.id)
        db.commit()
        auth=SimpleNamespace(account=account,session=session,secret_digest=session.secret_digest)
        prepared=prepare_optimization(db,1,[1],[],1)
        loaded=load_operation(db,1,[1],[],1)
        solution=optimize_semester([c.optimization for c in loaded.courses],loaded.fixed_sessions,generated_only=True)
    class Worker:
        def __init__(self,problem):self.sent=False
        def receive(self):
            if self.sent:return []
            self.sent=True;return [{'kind':'result','result':solution}]
        def is_alive(self):return not self.sent
        def close(self):pass
    monkeypatch.setattr(operations,'SolverProcess',Worker)
    operation_request=OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True,mode='json')))
    yield factory,auth,operation_request,request.param
    operations.shutdown_operations(engine);engine.dispose()


@pytest.mark.parametrize('change',ACCEPTANCE_WINDOW_CHANGES)
def test_dated_and_fixed_context_changes_after_candidate_reject_final_apply(dated_acceptance_operation,change):
    from tests.fixtures.dated_intensive_windows import mutate_acceptance_window
    factory,auth,request,with_selected=dated_acceptance_operation
    with factory() as db:operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    assert status.phase==('awaiting_decision' if with_selected else 'ready_to_save')
    with factory() as db:mutate_acceptance_window(db,change)
    before=saved_state(factory)
    with factory() as db:
        with pytest.raises(operations.OperationFailure):
            operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint,finalize=not with_selected)
        receipt=db.get(OptimizationOperation,str(request.operation_id))
        assert receipt.phase=='stale' and receipt.saved_result is None
    assert saved_state(factory)==before


@pytest.fixture
def setup_operation(tmp_path, monkeypatch, isolated_standard_policy):
    engine = file_backed_engine(tmp_path / 'operations.db')
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        seed_optimization_planner(db, course_count=2)
        account = add_planner_account(db)
        session, raw_secret = add_current_session(db, account_id=account.id)
        db.commit()
        auth = SimpleNamespace(account=account, session=session, secret_digest=session.secret_digest)
        prepared = prepare_optimization(db, 1, [1, 2], [], 1)
        loaded = load_operation(db, 1, [1, 2], [], 1)
        result = optimize_semester([c.optimization for c in loaded.courses], loaded.fixed_sessions, generated_only=True)
    class Worker:
        calls = 0
        result_override = None
        base_result = result
        def __init__(self, problem):
            Worker.calls += 1
            Worker.last_problem = problem
            self.sent = False
        def receive(self):
            if self.sent: return []
            self.sent = True
            return [{'kind': 'result', 'result': self.result_override or result}]
        def is_alive(self): return not self.sent
        def close(self): pass
    monkeypatch.setattr(operations, 'SolverProcess', Worker)
    request = OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True, mode='json')))
    yield factory, auth, request, Worker
    operations.shutdown_operations(engine)
    engine.dispose()


def settled(factory, auth, request, secret=CONTEXT_SECRET):
    end = monotonic() + 10
    while monotonic() < end:
        with factory() as db:
            status = operations.get_status(db, str(request.operation_id), auth, secret)
        if status.phase not in ('preparing', 'optimizing', 'checking'): return status
        sleep(.01)
    pytest.fail('Operation did not settle')


@pytest.fixture(params=['standard', 'cohort', 'lecturer', 'standard_optimized'])
def setup_strategy_operation(setup_operation, isolated_standard_policy, request):
    from app.services.teaching_strategies import get_strategy
    factory, auth, _, worker = setup_operation
    algorithm = request.param
    isolated_standard_policy.write_text('{"activeAlgorithm":"' + algorithm + '","defaultSeconds":300,"ceilingSeconds":1800}')
    with factory() as db:
        prepared = prepare_optimization(db, 1, [1, 2], [], 1)
        loaded = load_operation(db, 1, [1, 2], [], 1)
        worker.result_override = get_strategy(algorithm).optimize(tuple(c.optimization for c in loaded.courses), loaded.fixed_sessions, generated_only=True, deadline_seconds=5, allow_unproven=True)
    value = OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True, mode='json')))
    return factory, auth, value, worker, algorithm


def saved_state(factory):
    """All business tables, including manual/protected work, excluding only receipts."""
    connection = factory.kw['bind'].raw_connection()
    try:
        db = connection.driver_connection
        tables = [row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'optimization_operations' ORDER BY name")]
        return tuple((table, tuple(db.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall())) for table in tables)
    finally:
        connection.close()


def close_working_revision(db, state):
    from app.services.schedule_lifecycle import (
        WORKING_STATES, get_lifecycle_overview, prepare_publication, transition_revision)
    from app.models.planning import ScheduleRevision
    overview=get_lifecycle_overview(db,1)
    revision=overview['activeWorkingRevision']
    token=None
    if state=='published':
        token=prepare_publication(db,1,revision['revisionVersion'],overview['stateToken'])['preparationToken']
    transition_revision(db,1,action='publish' if state=='published' else 'abandon',
        expected_revision_version=revision['revisionVersion'],expected_state_token=overview['stateToken'],
        confirmed=True,publication_token=token)
    db.commit()
    assert db.get(ScheduleRevision,1).state==state
    assert state not in WORKING_STATES


def test_fully_proven_new_selection_has_no_worker_writes_and_finalizes_once(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    assert status.phase == 'ready_to_save'
    assert status.can_finalize and not status.can_accept
    with factory() as db:
        assert db.query(DraftSchedule).count() == 0
        saved = operations.apply_operation(db, status.operation_id, auth, CONTEXT_SECRET, status.review.candidate_fingerprint, finalize=True)
        assert saved.saved
    with factory() as db:
        repeated = operations.apply_operation(db, status.operation_id, auth, CONTEXT_SECRET, status.review.candidate_fingerprint, finalize=True)
        assert repeated.result == saved.result
        late_cancel=operations.cancel_operation(db,status.operation_id,auth,reason='navigation')
        assert late_cancel.saved and late_cancel.terminal_code is None
        assert late_cancel.result==saved.result
        assert db.query(DraftSchedule).count() == 2
    assert worker.calls == 1


def test_start_replay_never_dispatches_twice_even_after_policy_change(setup_operation, monkeypatch):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    settled(factory, auth, request)
    monkeypatch.setenv('TEACHING_OPTIMIZATION_POLICY_FILE', 'missing.json')
    with factory() as db: operations.start_operation(db, request, auth)
    assert worker.calls == 1


def test_cancel_discards_candidate_and_prevents_apply(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        cancelled = operations.cancel_operation(db, str(request.operation_id), auth)
        assert cancelled.phase == 'cancelled'
        with pytest.raises(operations.OperationFailure):
            operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET, status.review.candidate_fingerprint)
        assert db.query(DraftSchedule).count() == 0


@pytest.mark.parametrize('reason,code', [
    ('cancel','CANCELLED_BY_USER'), ('navigation','CANCELLED_BY_NAVIGATION'),
    ('dismiss','CANCELLED_BY_DISMISSAL'), ('retry','CANCELLED_FOR_RETRY'),
    ('context_lost','CANCELLED_CONTEXT_LOST'),
])
def test_cancel_preserves_the_first_recorded_reason(setup_operation,reason,code):
    factory,auth,request,worker=setup_operation
    with factory() as db:operations.start_operation(db,request,auth)
    settled(factory,auth,request)
    with factory() as db:
        cancelled=operations.cancel_operation(db,str(request.operation_id),auth,reason=reason)
        assert cancelled.phase=='cancelled' and cancelled.terminal_code==code
    with factory() as db:
        repeated=operations.cancel_operation(db,str(request.operation_id),auth,reason='context_lost')
        assert repeated.terminal_code==code
        assert db.get(OptimizationOperation,str(request.operation_id)).terminal_code==code
        assert db.query(DraftSchedule).count()==0


def test_missing_live_secret_is_outcome_only_and_other_owner_is_not_found(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    settled(factory, auth, request)
    with factory() as db:
        status = operations.get_status(db, str(request.operation_id), auth, None)
        assert status.review is None and not status.can_finalize
        other = SimpleNamespace(account=SimpleNamespace(id=999), session=auth.session, secret_digest=auth.secret_digest)
        with pytest.raises(operations.OperationFailure) as failure:
            operations.get_status(db, str(request.operation_id), other, CONTEXT_SECRET)
        assert failure.value.status == 404


def test_relevant_input_change_rejects_whole_candidate(setup_operation):
    from app.models.planning import Course
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        db.get(Course, 1).total_units += 1
        db.commit()
    with factory() as db:
        with pytest.raises(operations.OperationFailure) as failure:
            operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET, status.review.candidate_fingerprint, finalize=True)
        assert failure.value.code == 'STALE_PLANNING_INPUT'
        assert db.query(DraftSchedule).count() == 0


def test_reused_session_id_cannot_restore_live_authority_but_owner_can_cancel(setup_operation):
    from app.models.planning import PlannerSession
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        session = db.get(PlannerSession, auth.session.id)
        session.secret_digest = 'f' * 64
        db.commit()
    replacement = SimpleNamespace(account=auth.account, session=auth.session, secret_digest='f' * 64)
    with factory() as db:
        assert not operations.get_status(db, str(request.operation_id), replacement, CONTEXT_SECRET).can_finalize
        with pytest.raises(operations.OperationFailure): operations.start_operation(db, request, replacement)
        with pytest.raises(operations.OperationFailure):
            operations.apply_operation(db, str(request.operation_id), replacement, CONTEXT_SECRET, status.review.candidate_fingerprint, finalize=True)
        assert operations.cancel_operation(db, str(request.operation_id), replacement).phase == 'cancelled'


def test_shutdown_invalidates_review_without_saving_and_recovery_preserves_saved_receipts(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    settled(factory, auth, request)
    operations.shutdown_operations(factory.kw['bind'])
    with factory() as db:
        operations.recover_operations(db)
        status = operations.get_status(db, str(request.operation_id), auth, CONTEXT_SECRET)
        assert status.phase == 'interrupted'
        assert status.review is None
        assert db.query(DraftSchedule).count() == 0


def test_unproven_full_coverage_requires_acceptance_and_keeps_saved_scoped_proof(setup_operation):
    from dataclasses import replace
    factory, auth, request, worker = setup_operation
    with factory() as db:
        loaded=load_operation(db,1,[1,2],[],1)
        result=optimize_semester([c.optimization for c in loaded.courses],[],generated_only=True)
    evidence=tuple(replace(o,proof_status='unfinished' if i==1 else 'not_attempted' if i>1 else 'proven') for i,o in enumerate(result.objectives))
    worker.result_override=replace(result,optimal=False,objectives=evidence)
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    assert status.phase=='awaiting_decision' and not status.can_finalize
    assert status.review.proof.coverage_proven
    assert not status.review.proof.preferences_proven
    assert status.review.proof.additional_possible_units == 0
    with factory() as db:
        assert db.query(DraftSchedule).count()==0
        saved=operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint)
        assert saved.result.proof == status.review.proof
        assert not saved.result.summary.optimal_for_prepared_snapshot


def test_application_failure_rolls_back_every_course_and_receipt(setup_operation, monkeypatch):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    original=operations.generation.replace_draft_schedule
    calls=[]
    def fail_second(*args,**kwargs):
        calls.append(1)
        if len(calls)==2: raise RuntimeError('test persistence failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(operations.generation,'replace_draft_schedule',fail_second)
    with factory() as db:
        with pytest.raises(operations.OperationFailure):
            operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint,finalize=True)
    with factory() as db:
        assert db.query(DraftSchedule).count()==0
        receipt=db.get(OptimizationOperation,str(request.operation_id))
        assert receipt.phase=='failed' and receipt.saved_result is None


def test_postcommit_transport_failure_reports_actual_saved_receipt(setup_operation, monkeypatch):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    with factory() as db:
        commit=db.commit
        def lost_response():
            commit()
            raise OSError('response lost after durable commit')
        monkeypatch.setattr(db,'commit',lost_response)
        saved=operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint,finalize=True)
        assert saved.saved
    with factory() as db:
        assert db.query(DraftSchedule).count()==2
        assert operations.cancel_operation(db,str(request.operation_id),auth).saved


@pytest.mark.parametrize('cancel_second',[False,True])
@pytest.mark.parametrize('explicit_accept',[False,True])
def test_two_sessions_racing_apply_or_cancel_have_one_complete_outcome(setup_operation,cancel_second,explicit_accept):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    factory, auth, request, worker = setup_operation
    before = saved_state(factory)
    if explicit_accept:
        from dataclasses import replace
        worker.result_override = replace(worker.base_result, optimal=False, objectives=tuple(
            replace(o, proof_status='unfinished' if i==0 else 'not_attempted')
            for i,o in enumerate(worker.base_result.objectives)))
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    barrier=Barrier(2)
    def run(cancel):
        with factory() as db:
            barrier.wait(timeout=5)
            if cancel: return operations.cancel_operation(db,str(request.operation_id),auth)
            try: return operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint,finalize=not explicit_accept)
            except operations.OperationFailure: return operations.get_status(db,str(request.operation_id),auth)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(run,False);second=pool.submit(run,cancel_second)
        values=[first.result(timeout=10),second.result(timeout=10)]
    with factory() as db:
        receipt=db.get(OptimizationOperation,str(request.operation_id))
        count=db.query(DraftSchedule).count()
        assert (receipt.phase,count) in [('saved',2),('cancelled',0)]
        if not cancel_second: assert receipt.phase=='saved'
        assert all(value.phase in ('saved','cancelled') for value in values)
        if receipt.phase=='cancelled': assert saved_state(factory)==before


@pytest.mark.parametrize('all_empty',[False,True])
def test_empty_course_is_in_whole_decision_but_empty_timeout_has_no_acceptance(setup_operation,all_empty):
    from dataclasses import replace
    factory, auth, request, worker=setup_operation
    original=worker.base_result
    courses=tuple(replace(c,sessions=(),scheduled_units=0) if i==0 or all_empty else c for i,c in enumerate(original.courses))
    total=sum(c.scheduled_units for c in courses)
    worker.result_override=replace(original,courses=courses,total_units=total,optimal=False,unit_upper_bound=None,
        objectives=tuple(replace(o,proof_status='unfinished' if i==0 else 'not_attempted',value=total if i==0 else None) for i,o in enumerate(original.objectives)))
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    if all_empty:
        assert status.phase=='timeout_no_candidate' and not status.can_accept
    else:
        assert status.review.comparison.courses[0].generated.scheduled_units==0
        assert status.phase=='awaiting_decision'
        with factory() as db:
            saved=operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint)
            assert saved.saved
            assert db.query(DraftSchedule).count()==1


def test_review_elapsed_does_not_consume_the_search_allowance(setup_operation):
    factory,auth,request,worker=setup_operation
    with factory() as db: operations.start_operation(db,request,auth)
    settled(factory,auth,request)
    with factory() as db:
        live=operations._registry[operations._key(db,str(request.operation_id))]
        live.started-=400;live.deadline-=400
        status=operations.get_status(db,str(request.operation_id),auth,CONTEXT_SECRET)
        assert status.elapsed_milliseconds>=400000
        assert not status.budget_exhausted


def test_optimized_checkpoint_survives_worker_deadline_and_requires_acceptance(setup_operation,
        isolated_standard_policy, monkeypatch):
    from app.services.teaching_strategies import get_strategy
    factory, auth, _, worker = setup_operation
    isolated_standard_policy.write_text('{"activeAlgorithm":"standard_optimized","defaultSeconds":300,"ceilingSeconds":1800}')
    with factory() as db:
        prepared = prepare_optimization(db, 1, [1,2], [], 1)
        loaded = load_operation(db, 1, [1,2], [], 1)
    checkpoints = []
    from app.services.semester_optimization import OptimizationSearchControl
    deadline = monotonic()+5
    candidate = get_strategy('standard_optimized').optimize(
        tuple(c.optimization for c in loaded.courses), loaded.fixed_sessions,
        generated_only=True, allow_unproven=True, control=OptimizationSearchControl(deadline,
            clock=lambda: deadline+1 if checkpoints else monotonic(), checkpoint=checkpoints.append))
    assert candidate.total_units > 0 and not candidate.optimal
    request = OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True, mode='json')))
    monkeypatch.setattr(worker, 'receive', lambda self: [
        {'kind':'checkpoint','result':candidate}, {'kind':'timeout','budgetExhausted':True}])
    before = saved_state(factory)
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    assert status.phase == 'awaiting_decision' and status.can_accept
    assert status.termination == 'deadline' and status.budget_exhausted
    assert status.review.comparison.generated.scheduled_units == candidate.total_units
    assert saved_state(factory) == before


@pytest.mark.parametrize('exhausted', [False, True])
def test_optimized_no_candidate_uses_truthful_termination(setup_operation,
        isolated_standard_policy, monkeypatch, exhausted):
    factory, auth, _, worker = setup_operation
    isolated_standard_policy.write_text('{"activeAlgorithm":"standard_optimized","defaultSeconds":300,"ceilingSeconds":1800}')
    with factory() as db: prepared = prepare_optimization(db, 1, [1,2], [], 1)
    request = OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True, mode='json')))
    monkeypatch.setattr(worker, 'receive', lambda self: [{'kind':'timeout','budgetExhausted':exhausted}])
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    assert status.phase == 'timeout_no_candidate' and not status.can_accept
    assert status.termination == ('deadline' if exhausted else 'standard_optimized_completed')


@pytest.mark.parametrize('with_checkpoint',[False,True])
def test_unexpected_child_exit_is_failure_even_with_an_earlier_checkpoint(setup_operation,monkeypatch,with_checkpoint):
    factory,auth,request,worker=setup_operation
    class CrashedWorker:
        def __init__(self,problem): self.sent=False
        def receive(self):
            if not self.sent and with_checkpoint:
                self.sent=True
                return [{'kind':'checkpoint','result':worker.base_result}]
            return []
        def is_alive(self): return False
        def close(self): pass
    monkeypatch.setattr(operations,'SolverProcess',CrashedWorker)
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    assert status.phase=='failed' and status.review is None
    assert status.terminal_code=='OPTIMIZATION_WORKER_FAILED'
    with factory() as db: assert db.query(DraftSchedule).count()==0


@pytest.mark.parametrize('fault', ['dispatch', 'pipe'])
def test_worker_faults_never_offer_or_save_a_checkpoint(setup_operation, monkeypatch, fault):
    factory, auth, request, worker = setup_operation
    class FaultyWorker:
        def __init__(self, problem):
            if fault == 'dispatch': raise OSError('spawn unavailable')
        def receive(self): raise EOFError('pipe lost')
        def is_alive(self): return True
        def close(self): pass
    monkeypatch.setattr(operations, 'SolverProcess', FaultyWorker)
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    assert status.phase == 'failed' and status.review is None
    assert status.terminal_code == ('OPTIMIZATION_DISPATCH_FAILED' if fault == 'dispatch' else 'OPTIMIZATION_WORKER_FAILED')
    with factory() as db: assert db.query(DraftSchedule).count() == 0


def test_real_deleted_session_and_relogin_with_reused_id_is_outcome_only(setup_operation):
    from app.models.planning import PlannerSession
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        old = db.get(PlannerSession, auth.session.id)
        db.delete(old); db.commit()
        replacement, _ = add_current_session(db, account_id=auth.account.id, raw_secret='n' * 43)
        assert replacement.id == auth.session.id
        db.commit()
        relogged = SimpleNamespace(account=auth.account, session=replacement, secret_digest=replacement.secret_digest)
    with factory() as db:
        outcome = operations.get_status(db, str(request.operation_id), relogged, CONTEXT_SECRET)
        assert outcome.review is None and not outcome.can_finalize and not outcome.can_accept
        with pytest.raises(operations.OperationFailure): operations.start_operation(db, request, relogged)
        for finalize in (False, True):
            with pytest.raises(operations.OperationFailure):
                operations.apply_operation(db, str(request.operation_id), relogged, CONTEXT_SECRET,
                    status.review.candidate_fingerprint, finalize=finalize)
        assert operations.cancel_operation(db, str(request.operation_id), relogged).phase == 'cancelled'
        assert db.query(DraftSchedule).count() == 0


@pytest.mark.parametrize('changed', ['lecturer_eligibility','room_eligibility','room_capacity','room_active',
    'lecturer_active','lecturer_availability','room_availability','window','cohort_size','semester_dates',
    'constraints','holiday','active_exam','revision'])
def test_exact_apply_rechecks_each_material_freshness_category(setup_operation, changed):
    from datetime import date, time
    from app.models.planning import (CourseEligibleLecturer, CourseEligibleRoom, Lecturer, Room, Cohort,
        Semester, CohortCalendarTimeWindow, ResourceUnavailabilityPeriod, ResourceUnavailabilityWeekday,
        ScheduleRevision, InstitutionHoliday)
    from tests.optimization_fixtures import active_exam
    from tests.services.test_conflict_aware_generation import save_custom_constraints
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        if changed == 'lecturer_eligibility': db.query(CourseEligibleLecturer).filter_by(course_id=1).delete()
        elif changed == 'room_eligibility': db.query(CourseEligibleRoom).filter_by(course_id=1).delete()
        elif changed == 'room_capacity': db.get(Room, 1).capacity = 20
        elif changed == 'room_active': db.get(Room, 1).is_active = False
        elif changed == 'lecturer_active': db.get(Lecturer, 1).is_active = False
        elif changed in ('lecturer_availability', 'room_availability'):
            db.add(ResourceUnavailabilityPeriod(**{('lecturer_id' if changed.startswith('lecturer') else 'room_id'):1},
                kind='recurring', start_time=time(8), end_time=time(12),
                weekdays=[ResourceUnavailabilityWeekday(weekday=0)]))
        elif changed == 'window': db.get(CohortCalendarTimeWindow, 1).is_active = False
        elif changed == 'cohort_size': db.get(Cohort, 1).student_count += 1
        elif changed == 'semester_dates': db.get(Semester, 1).end_date = date(2026, 12, 1)
        elif changed == 'constraints': save_custom_constraints(db, 1, 0, 1)
        elif changed == 'holiday': db.add(InstitutionHoliday(date=date(2026, 9, 7), name='Test'))
        elif changed == 'active_exam': db.add(active_exam(exam_id=90, course_id=1, exam_date=date(2026, 12, 1)))
        elif changed == 'revision': db.get(ScheduleRevision, 1).state = 'ready_for_review'
        db.commit()
    before = saved_state(factory)
    with factory() as db:
        with pytest.raises(operations.OperationFailure):
            operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
                status.review.candidate_fingerprint, finalize=True)
        assert db.query(DraftSchedule).count() == 0
        assert db.get(OptimizationOperation, str(request.operation_id)).phase == 'stale'
    assert saved_state(factory) == before


@pytest.mark.parametrize('state',['published','abandoned'])
def test_saved_receipt_survives_recovery_and_cancel_after_revision_is_closed(setup_operation,state):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        saved = operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, finalize=True)
        close_working_revision(db,state)
    before=saved_state(factory)
    operations.shutdown_operations(factory.kw['bind'])
    with factory() as db:
        operations.recover_operations(db)
        outcome = operations.cancel_operation(db, str(request.operation_id), auth)
        assert outcome.saved and outcome.result == saved.result
        assert db.query(DraftSchedule).count() == 2
    assert saved_state(factory)==before


def test_confirmed_discard_precedes_fresh_attempt_with_current_policy(setup_operation, monkeypatch, tmp_path):
    from uuid import uuid4
    from tests.optimization_fixtures import operation_start_payload
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    old = settled(factory, auth, request)
    with factory() as db:
        assert operations.cancel_operation(db, str(request.operation_id), auth).phase == 'cancelled'
    policy = tmp_path / 'policy.json'
    policy.write_text('{"defaultSeconds":600,"ceilingSeconds":1200}')
    monkeypatch.setenv('TEACHING_OPTIMIZATION_POLICY_FILE', str(policy))
    with factory() as db:
        prepared = prepare_optimization(db, 1, [1,2], [], 1)
        body = operation_start_payload(prepared.model_dump(by_alias=True, mode='json'))
        body['operationId'] = str(uuid4())
        fresh = OptimizationOperationStart.model_validate(body)
        assert operations.start_operation(db, fresh, auth).budget_seconds == 600
        with pytest.raises(operations.OperationFailure):
            operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
                old.review.candidate_fingerprint, finalize=True)
        assert db.query(DraftSchedule).count() == 0
    settled(factory, auth, fresh)


def test_operation_waiting_for_publication_claim_revalidates_before_save(setup_operation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from app.services.schedule_lifecycle import get_lifecycle_overview, prepare_publication, transition_revision
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    claimed, attempting = Event(), Event()
    def publish():
        with factory() as db:
            overview = get_lifecycle_overview(db, 1)
            revision = overview['activeWorkingRevision']
            prepared = prepare_publication(db, 1, revision['revisionVersion'], overview['stateToken'])
            transition_revision(db, 1, action='publish', expected_revision_version=revision['revisionVersion'],
                expected_state_token=overview['stateToken'], confirmed=True, publication_token=prepared['preparationToken'])
            claimed.set()
            assert attempting.wait(5)
            db.commit()
    def apply():
        assert claimed.wait(5)
        with factory() as db:
            attempting.set()
            with pytest.raises(operations.OperationFailure):
                operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
                    status.review.candidate_fingerprint, finalize=True)
            assert db.query(DraftSchedule).count() == 0
    with ThreadPoolExecutor(max_workers=2) as pool:
        publication=pool.submit(publish);application=pool.submit(apply)
        publication.result(10);application.result(10)
    with factory() as db:
        assert db.get(OptimizationOperation, str(request.operation_id)).phase == 'stale'


def test_irrelevant_past_exam_and_unrelated_resource_do_not_invalidate_candidate(setup_operation):
    from tests.optimization_fixtures import past_exam
    from app.models.planning import Lecturer
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        db.add(past_exam(exam_id=91, course_id=1))
        db.add(Lecturer(name='Unrelated', reference_code='UNRELATED', normalized_reference_code='unrelated'))
        db.commit()
    with factory() as db:
        assert operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, finalize=True).saved


def test_operation_comparison_uses_aggregate_subtraction_with_overscheduled_current_course(setup_operation):
    from dataclasses import replace
    from datetime import date, time, timedelta
    from app.models.planning import Course
    from app.services.draft_schedule_repository import load_course_plan, replace_draft_schedule
    from app.services.schedule_generation import GeneratedSession
    factory, auth, request, worker = setup_operation
    with factory() as db:
        for course_id, required, sessions in ((1,40,10),(2,60,8)):
            db.get(Course, course_id).total_units=required
            replace_draft_schedule(db, load_course_plan(db,course_id),1,[
                GeneratedSession(date(2026,9,7)+timedelta(weeks=i),time(8),time(12,25),5,1,0,course_id,course_id)
                for i in range(sessions)])
        db.commit()
        prepared=prepare_optimization(db,1,[1,2],[],1)
        request=OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True,mode='json')))
    worker.result_override=replace(worker.base_result,optimal=False,objectives=tuple(
        replace(o,proof_status='unfinished' if i==0 else 'not_attempted') for i,o in enumerate(worker.base_result.objectives)))
    before=saved_state(factory)
    with factory() as db: operations.start_operation(db,request,auth)
    status=settled(factory,auth,request)
    current=status.review.comparison.current
    assert (current.required_units,current.scheduled_units,current.remaining_units)==(100,90,10)
    assert [(c.current.required_units,c.current.scheduled_units,c.current.remaining_units)
        for c in status.review.comparison.courses]==[(40,50,0),(60,40,20)]
    assert saved_state(factory)==before


def test_operation_uses_one_original_deadline_without_a_save_reserve(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db: operations.start_operation(db, request, auth)
    settled(factory, auth, request)
    with factory() as db:
        live=operations._registry[operations._key(db,str(request.operation_id))]
        receipt=db.get(OptimizationOperation,str(request.operation_id))
        assert worker.last_problem.deadline==live.deadline
        assert receipt.budget_seconds == 300
        assert live.deadline == live.started + receipt.budget_seconds


@pytest.mark.parametrize('state',['published','abandoned'])
def test_owner_can_discard_unsaved_review_after_revision_becomes_noneditable(setup_operation,state):
    factory,auth,request,worker=setup_operation
    with factory() as db:operations.start_operation(db,request,auth)
    review=settled(factory,auth,request)
    with factory() as db:
        live=operations._registry[operations._key(db,str(request.operation_id))]
        close_working_revision(db,state)
    before=saved_state(factory)
    with factory() as db:
        outcome=operations.cancel_operation(db,str(request.operation_id),auth)
        assert outcome.phase=='cancelled' and not outcome.saved and outcome.review is None
        for finalize in (False,True):
            with pytest.raises(operations.OperationFailure):
                operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,
                    review.review.candidate_fingerprint,finalize=finalize)
    operations._run(str(request.operation_id),live)  # Late work cannot reopen a discarded receipt.
    with factory() as db:
        status=operations.get_status(db,str(request.operation_id),auth,CONTEXT_SECRET)
        assert status.phase=='cancelled' and not status.can_accept and not status.can_finalize
    assert saved_state(factory)==before


def test_captured_standard_identity_survives_policy_deletion_and_reload(setup_operation, isolated_standard_policy):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        first = operations.start_operation(db, request, auth)
    assert first.algorithm == 'standard'
    assert first.strategy_profile == 'standard-v1'
    assert worker.calls <= 1
    isolated_standard_policy.unlink()
    status = settled(factory, auth, request)
    with factory() as db:
        replay = operations.start_operation(db, request, auth)
        assert replay.algorithm == 'standard'
        assert replay.strategy_settings == first.strategy_settings
        row = db.get(OptimizationOperation, str(request.operation_id))
        assert row.algorithm == 'standard'
        assert row.strategy_profile == 'standard-v1'
        assert isinstance(row.strategy_settings, dict)
    assert status.phase in ('ready_to_save', 'awaiting_decision')


def test_algorithm_only_change_requires_new_preparation(setup_operation, isolated_standard_policy):
    factory, auth, request, worker = setup_operation
    isolated_standard_policy.write_text('{"activeAlgorithm":"cohort","defaultSeconds":300,"ceilingSeconds":1800}')
    with factory() as db:
        with pytest.raises(operations.OperationFailure) as failure:
            operations.start_operation(db, request, auth)
        assert failure.value.code == 'BUDGET_POLICY_CHANGED'
        assert db.get(OptimizationOperation, str(request.operation_id)) is None
    assert worker.calls == 0


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_real_heuristic_result_requires_explicit_review_and_keeps_captured_policy(setup_operation, isolated_standard_policy, algorithm):
    from app.services.teaching_strategies import get_strategy
    factory, auth, request, worker = setup_operation
    isolated_standard_policy.write_text('{"activeAlgorithm":"' + algorithm + '","defaultSeconds":300,"ceilingSeconds":1800}')
    with factory() as db:
        prepared = prepare_optimization(db, 1, [1, 2], [], 1)
        loaded = load_operation(db, 1, [1, 2], [], 1)
        worker.result_override = get_strategy(algorithm).optimize(tuple(c.optimization for c in loaded.courses), loaded.fixed_sessions, deadline_seconds=5)
    request = OptimizationOperationStart.model_validate(operation_start_payload(prepared.model_dump(by_alias=True, mode='json')))
    before = saved_state(factory)
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    assert status.phase == 'awaiting_decision'
    assert status.algorithm == algorithm
    assert status.termination in ('heuristic_completed', 'repair_limit')
    assert status.can_accept and not status.can_finalize
    assert status.review.proof.objective_profile == 'heuristic-v1'
    assert status.review.proof.preferences_proven is False
    assert saved_state(factory) == before
    isolated_standard_policy.unlink()
    with factory() as db:
        saved = operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET, status.review.candidate_fingerprint)
    assert saved.saved and saved.result.algorithm == algorithm
    assert saved.termination == status.termination


def test_legacy_saved_receipt_normalizes_standard_identity_without_rewriting_payload(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db,request,auth)
    status = settled(factory,auth,request)
    with factory() as db:
        operations.apply_operation(db,str(request.operation_id),auth,CONTEXT_SECRET,status.review.candidate_fingerprint,finalize=True)
        row = db.get(OptimizationOperation,str(request.operation_id))
        legacy = dict(row.saved_result)
        for key in ('algorithm','strategyProfile','strategySettings'):
            legacy.pop(key,None)
        row.saved_result = legacy
        row.strategy_settings = {'version':'legacy-standard-v1'}
        db.commit()
    operations.shutdown_operations(factory.kw['bind'])
    with factory() as db:
        restored = operations.get_status(db,str(request.operation_id),auth)
        assert restored.result.algorithm == restored.algorithm == 'standard'
        assert restored.result.strategy_settings == restored.strategy_settings
        assert 'algorithm' not in db.get(OptimizationOperation,str(request.operation_id)).saved_result
