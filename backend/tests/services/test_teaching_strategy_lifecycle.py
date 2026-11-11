"""Real-search candidates through the operation lifecycle, on disposable SQLite."""
from dataclasses import replace

import pytest

from app.models.planning import Lecturer, Room, Course
from app.services import optimization_operations as operations
from tests.optimization_fixtures import CONTEXT_SECRET
from tests.services.test_optimization_operations import (
    setup_operation, setup_strategy_operation, settled, saved_state,
)


def begin(value):
    factory, auth, request, worker, algorithm = value
    with factory() as db:
        operations.start_operation(db, request, auth)
    return settled(factory, auth, request)


@pytest.mark.parametrize('setup_strategy_operation', ['standard_optimized'], indirect=True)
def test_optimized_conditional_proof_is_scoped_and_survives_atomic_acceptance(setup_strategy_operation):
    factory, auth, request, worker, _ = setup_strategy_operation
    candidate = worker.result_override
    worker.result_override = replace(candidate, optimal=False, objectives=tuple(
        replace(e, proof_status='proven' if index < 4 else 'unfinished' if index == 4 else 'conditional')
        for index,e in enumerate(candidate.objectives)))
    status = begin(setup_strategy_operation)
    proof = status.review.proof
    assert status.phase == 'awaiting_decision' and not status.can_finalize
    assert proof.coverage_proven and not proof.preferences_proven
    assert proof.objectives[5].condition['weekly_spread'] == proof.objectives[4].value
    assert all(o.candidate_fingerprint == status.review.candidate_fingerprint for o in proof.objectives)
    with factory() as db:
        saved = operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint)
    assert saved.saved and saved.result.proof == proof


def test_no_candidate_writes_and_explicit_or_proven_save(setup_strategy_operation):
    factory, auth, request, worker, algorithm = setup_strategy_operation
    before = saved_state(factory)
    status = begin(setup_strategy_operation)
    assert saved_state(factory) == before
    assert status.review.algorithm == algorithm
    assert worker.last_problem.algorithm == algorithm
    assert status.review.proof.preferences_proven is worker.result_override.optimal
    if algorithm == 'standard_optimized':
        assert not status.can_finalize
        assert status.review.proof.objective_profile == 'standard-optimized-v1'
    with factory() as db:
        saved = operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, finalize=status.can_finalize)
    assert saved.saved and saved.result.algorithm == algorithm
    with factory() as db:
        assert operations.apply_operation(db, str(request.operation_id), auth, None, 'wrong').saved


@pytest.mark.parametrize('change', ['code', 'eligibility', 'capacity', 'requirement'])
def test_material_change_before_save_rejects_all_selected_work(setup_strategy_operation, change):
    factory, auth, request, worker, algorithm = setup_strategy_operation
    status = begin(setup_strategy_operation)
    with factory() as db:
        if change == 'code':
            lecturer = db.get(Lecturer, 1)
            lecturer.reference_code = 'Z-NEW'
            lecturer.normalized_reference_code = 'z-new'
        elif change == 'eligibility':
            course = db.get(Course, 1)
            course.eligible_lecturers.clear()
        elif change == 'capacity': db.get(Room, 1).capacity = 1
        else: db.get(Course, 1).total_units += 1
        db.commit()
    before = saved_state(factory)
    with factory() as db, pytest.raises(operations.OperationFailure):
        operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
            status.review.candidate_fingerprint, finalize=status.can_finalize)
    assert saved_state(factory) == before


def test_corrupted_exact_candidate_is_never_reviewed(setup_strategy_operation):
    factory, auth, request, worker, algorithm = setup_strategy_operation
    candidate = worker.result_override
    first = candidate.courses[0]
    broken = replace(first, sessions=tuple(replace(s, room_id=999999) for s in first.sessions))
    worker.result_override = replace(candidate, courses=(broken, *candidate.courses[1:]))
    before = saved_state(factory)
    status = begin(setup_strategy_operation)
    assert status.phase == 'failed' and status.review is None
    assert not status.can_accept and not status.can_finalize
    assert saved_state(factory) == before


@pytest.mark.parametrize('all_empty', [False, True])
def test_partial_and_zero_preserve_whole_selected_scope(setup_strategy_operation, all_empty):
    factory, auth, request, worker, algorithm = setup_strategy_operation
    candidate = worker.result_override
    rows = tuple(replace(c, sessions=(), scheduled_units=0) if all_empty or index else c
                 for index, c in enumerate(candidate.courses))
    total = sum(c.scheduled_units for c in rows)
    worker.result_override = replace(candidate, courses=rows, total_units=total, optimal=False,
        objectives=tuple(replace(o, value=total if index == 0 else o.value, proof_status='unfinished') for index, o in enumerate(candidate.objectives)))
    before = saved_state(factory)
    status = begin(setup_strategy_operation)
    assert saved_state(factory) == before
    if all_empty:
        assert status.phase == 'timeout_no_candidate' and status.review is None
        assert not status.can_accept and not status.can_finalize
    else:
        assert status.phase == 'awaiting_decision' and status.can_accept
        assert len(status.review.comparison.courses) == 2
        assert status.review.comparison.courses[1].generated.scheduled_units == 0
