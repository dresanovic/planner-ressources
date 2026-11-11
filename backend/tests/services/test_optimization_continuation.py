from dataclasses import replace
from time import monotonic
from uuid import uuid4

import pytest

from app.services import optimization_operations as operations
from app.services.teaching_strategies import get_strategy
from app.services.semester_optimization import OptimizationSearchControl
from tests.optimization_fixtures import CONTEXT_SECRET, optimization_course
from tests.services.test_optimization_operations import (
    setup_operation, settled, saved_state,
)


def test_continue_same_operation_retains_candidate_and_replay_is_idempotent(setup_operation):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    before = saved_state(factory)
    continuation_id = str(uuid4())
    fingerprint = status.review.candidate_fingerprint
    with factory() as db:
        operations.continue_operation(db, status.operation_id, auth, CONTEXT_SECRET,
            fingerprint, continuation_id)
    continued = settled(factory, auth, request)
    assert continued.operation_id == status.operation_id
    assert worker.last_problem.incumbent == worker.base_result
    assert continued.review.comparison.generated.scheduled_units == status.review.comparison.generated.scheduled_units
    with factory() as db:
        operations.continue_operation(db, status.operation_id, auth, CONTEXT_SECRET,
            fingerprint, continuation_id)
    assert worker.calls == 2
    assert saved_state(factory) == before


@pytest.mark.parametrize('bad_secret,bad_fingerprint', [(True, False), (False, True)])
def test_continue_rejects_wrong_context_or_candidate(setup_operation, bad_secret, bad_fingerprint):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db, pytest.raises(operations.OperationFailure):
        operations.continue_operation(db, status.operation_id, auth,
            'f' * 64 if bad_secret else CONTEXT_SECRET,
            '0' * 64 if bad_fingerprint else status.review.candidate_fingerprint, str(uuid4()))
    assert worker.calls == 1


def test_continue_timeout_retains_reviewable_incumbent(setup_operation, monkeypatch):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    monkeypatch.setattr(worker, 'receive', lambda self: [{'kind': 'timeout', 'budgetExhausted': True}])
    with factory() as db:
        operations.continue_operation(db, status.operation_id, auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, str(uuid4()))
    continued = settled(factory, auth, request)
    assert continued.phase == 'awaiting_decision'
    assert continued.can_accept
    assert continued.review.candidate_fingerprint == status.review.candidate_fingerprint


@pytest.mark.parametrize('outcome', ['failed', 'worse'])
def test_continuation_failure_or_worse_result_keeps_previous_proposal(setup_operation, monkeypatch, outcome):
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    if outcome == 'failed':
        monkeypatch.setattr(worker, 'receive', lambda self: [{'kind': 'failed', 'code': 'OPTIMIZATION_WORKER_FAILED'}])
    else:
        worker.result_override = replace(worker.base_result, total_units=0, objectives=tuple(
            replace(e, value=0) if e.objective_key == 'total_units' else e for e in worker.base_result.objectives))
    with factory() as db:
        operations.continue_operation(db, status.operation_id, auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, str(uuid4()))
    continued = settled(factory, auth, request)
    assert continued.phase == 'awaiting_decision'
    assert continued.review.candidate_fingerprint == status.review.candidate_fingerprint


def test_changed_inputs_reject_continuation_without_discarding_saved_work(setup_operation):
    from app.models.planning import Course
    factory, auth, request, worker = setup_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        db.get(Course, 1).total_units += 2
        db.commit()
    before = saved_state(factory)
    with factory() as db, pytest.raises(operations.OperationFailure) as error:
        operations.continue_operation(db, status.operation_id, auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, str(uuid4()))
    assert error.value.code == 'STALE_PLANNING_INPUT'
    assert worker.calls == 1
    assert saved_state(factory) == before


@pytest.mark.parametrize('algorithm', ['standard', 'standard_optimized'])
def test_exact_continuation_skips_proven_coverage_and_preserves_quality(algorithm):
    strategy = get_strategy(algorithm)
    course = optimization_course(1, total_units=4, min_units=2, max_units=2)
    original = strategy.optimize((course,), (), generated_only=True, deadline_seconds=5)
    incumbent = replace(original, optimal=False, objectives=tuple(
        replace(e, proof_status='unfinished' if i == 0 else 'not_attempted')
        for i, e in enumerate(original.objectives)))
    stages = []
    result = strategy.optimize((course,), (), generated_only=True, allow_unproven=True,
        incumbent=incumbent, control=OptimizationSearchControl(monotonic()+5, progress=stages.append))
    assert 'total_units' not in stages
    assert result.total_units == 4
    assert result.objectives[0].proof_status == 'proven'
    score = lambda value: tuple(-e.value if e.direction == 'max' else e.value for e in value.objectives)
    assert score(result) <= score(incumbent)


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_heuristic_continuation_starts_from_incumbent(algorithm):
    strategy = get_strategy(algorithm)
    course = optimization_course(1, total_units=4, min_units=2, max_units=2)
    original = strategy.optimize((course,), (), generated_only=True, deadline_seconds=5)
    result = strategy.optimize((course,), (), generated_only=True, deadline_seconds=5, incumbent=original)
    assert result.total_units >= original.total_units


@pytest.mark.parametrize('coverage,penalty,allowed', [(3, 0, False), (4, 11, False), (4, 9, True), (5, 20, True)])
def test_incumbent_lexicographic_guard_allows_only_ordered_improvements(coverage, penalty, allowed):
    from ortools.sat.python import cp_model
    from time import monotonic
    from app.services.optimization_incumbent import seed_incumbent
    from app.services.semester_optimization import SemesterOptimizationResult, ObjectiveEvidence, OptimizationSearchControl
    incumbent = SemesterOptimizationResult((), 4, 0, 0, 0, 0, 0, optimal=False, objectives=(
        ObjectiveEvidence('total_units', 'max', 'unfinished', 4),
        ObjectiveEvidence('penalty', 'min', 'not_attempted', 10)))
    model = cp_model.CpModel()
    units = model.new_int_var(0, 5, 'units')
    cost = model.new_int_var(0, 20, 'penalty')
    seed_incumbent(model, {}, [('total_units', 'max', units), ('penalty', 'min', cost)],
        incumbent, OptimizationSearchControl(monotonic()+5), 5)
    model.add(units == coverage)
    model.add(cost == penalty)
    assert (cp_model.CpSolver().solve(model) == cp_model.OPTIMAL) == allowed


@pytest.mark.parametrize('algorithm', ['standard', 'standard_optimized'])
def test_continuation_improves_intensive_placement_without_losing_units(algorithm):
    from datetime import time, timedelta
    from time import monotonic
    from app.services.schedule_generation import TimeWindowPlan
    from app.services.semester_optimization import OptimizationSearchControl
    from tests.optimization_fixtures import SEMESTER_START
    windows = (
        TimeWindowPlan(1, None, time(8), time(10), kind='dated', date=SEMESTER_START),
        TimeWindowPlan(2, None, time(8), time(10), kind='dated', date=SEMESTER_START+timedelta(days=7), is_intensive=True),
    )
    course = optimization_course(1, total_units=2, min_units=2, max_units=2, windows=windows)
    strategy = get_strategy(algorithm)
    # The same temporal candidates without intensive preferences choose the early
    # date. Its measured values also describe this legal but improvable proposal.
    unmarked = replace(course, windows=tuple(replace(w, is_intensive=False) for w in windows))
    incumbent = strategy.optimize((unmarked,), (), generated_only=True, deadline_seconds=5)
    incumbent = replace(incumbent, optimal=False, objectives=tuple(
        e if i == 0 else replace(e, proof_status='not_attempted')
        for i, e in enumerate(incumbent.objectives)))
    assert incumbent.total_units == 2 and incumbent.intensive_teaching_time == 0
    result = strategy.optimize((course,), (), generated_only=True, allow_unproven=True,
        deadline_seconds=5, incumbent=incumbent)
    assert result.total_units == incumbent.total_units
    assert result.intensive_teaching_time > incumbent.intensive_teaching_time
    assert result.courses[0].sessions[0].date == SEMESTER_START+timedelta(days=7)
