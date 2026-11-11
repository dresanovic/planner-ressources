"""Operation-based concurrent accept tests replacing retired synchronous calls."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from app.models.planning import DraftSchedule
from app.services import optimization_operations as operations
from app.services import conflict_aware_generation as generation
from tests.optimization_fixtures import CONTEXT_SECRET
from tests.services.test_optimization_operations import (
    setup_operation, setup_strategy_operation,
    dated_acceptance_operation, settled, saved_state,
)


def test_preference_only_marker_change_rejects_both_concurrent_accepts_without_business_writes(dated_acceptance_operation):
    from tests.fixtures.dated_intensive_windows import mutate_acceptance_window
    factory, auth, request, _ = dated_acceptance_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    with factory() as db:
        mutate_acceptance_window(db, 'fixed_marker')
    before = saved_state(factory)
    barrier = Barrier(2)
    def accept():
        with factory() as db:
            barrier.wait(timeout=5)
            try:
                operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
                    status.review.candidate_fingerprint, finalize=status.can_finalize)
            except operations.OperationFailure:
                return 'rejected'
            return 'unexpected-save'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: accept(), range(2))) == ['rejected', 'rejected']
    assert saved_state(factory) == before


def test_simultaneous_acceptance_commits_the_joint_candidate_at_most_once(setup_strategy_operation, monkeypatch):
    factory, auth, request, worker, algorithm = setup_strategy_operation
    with factory() as db:
        operations.start_operation(db, request, auth)
    status = settled(factory, auth, request)
    calls = []
    original = generation.replace_draft_schedule
    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(generation, 'replace_draft_schedule', counted)
    barrier = Barrier(2)
    def accept():
        with factory() as db:
            barrier.wait(timeout=5)
            return operations.apply_operation(db, str(request.operation_id), auth, CONTEXT_SECRET,
                status.review.candidate_fingerprint, finalize=status.can_finalize)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: accept(), range(2)))
    assert all(result.saved for result in results)
    assert len(calls) == 2  # Exactly one replacement for each selected course.
    assert results[0].result == results[1].result
    with factory() as db:
        drafts = db.query(DraftSchedule).all()
        assert len(drafts) == 2 and all(draft.revision == 1 for draft in drafts)
