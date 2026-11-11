"""I-011 real-strategy comparison on disposable, identical snapshots.

Run from the repository root with PYTHONPATH=backend:
  backend/.venv/Scripts/python.exe -m pytest backend/tests/performance/test_teaching_strategy_comparison.py -q

Missing strategies FAIL the acceptance comparison; they are never substituted.
Set TEACHING_COMPARISON_REPORT to an output JSON path to retain measurements.
"""
from copy import deepcopy
from dataclasses import replace
from datetime import time, timedelta
import json
import os
from pathlib import Path
import platform
from time import monotonic
from time import sleep

import pytest

from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan
from app.services.semester_optimization import (
    NoGeneratedAlternative, OptimalResultNotProven, OptimizationSearchControl,
    week_start,
)
from app.services.teaching_strategies import get_strategy
from tests.fixtures.teaching_strategies import (
    completed_facts, selection, snapshot_identity,
)
from tests.optimization_fixtures import SEMESTER_START, optimization_course, fixed_session


ALGORITHMS = ('standard', 'cohort', 'lecturer')
SCENARIOS = ('single', 'cohort_competition', 'shared_lecturer', 'intensive', 'partial_week', 'twenty')


def test_harness_scenarios_are_fixed_isolated_and_complete():
    cases = comparison_scenarios()
    assert tuple(cases) == SCENARIOS
    assert len(cases['single'][0]) == 1
    assert len(cases['twenty'][0]) == 20
    assert any(w.kind == 'dated' and w.is_intensive for c in cases['intensive'][0] for w in c.windows)
    assert all(snapshot_identity(*value) == snapshot_identity(*comparison_scenarios()[name])
               for name, value in cases.items())
    assert {c.cohort_id for c in cases['cohort_competition'][0]} == {1}
    assert len({c.cohort_id for c in cases['shared_lecturer'][0]}) > 1
    assert len({l.id for c in cases['shared_lecturer'][0] for l in c.lecturers}) == 1


def test_harness_reports_real_standard_evidence_without_mutating_input():
    courses, fixed = comparison_scenarios()['single']
    before = deepcopy((courses, fixed))
    row = measure_comparison('single', 'standard', courses, fixed, seconds=2)
    assert (courses, fixed) == before
    assert row['snapshot'] == snapshot_identity(courses, fixed)
    assert row['status'] == 'measured'
    assert row['requiredUnits'] == row['scheduledUnits'] + row['remainingUnits']
    assert row['scheduledUnits'] > 0
    assert row['elapsedSeconds'] >= 0
    assert row['allowanceSeconds'] == 2
    assert row['objectiveProfile'] == 'standard-v1'
    assert row['proofs'][0]['objective_key'] == 'total_units'
    assert row['hardValid'] is True
    assert row['weeklyCohortUnits'] and row['weeklyLecturerUnits']


def test_harness_missing_algorithm_is_explicit_and_never_substituted():
    courses, fixed = comparison_scenarios()['single']
    row = measure_comparison('single', 'not-a-strategy', courses, fixed, seconds=2)
    assert row['status'] == 'unavailable'
    assert row['scheduledUnits'] is None
    assert row['termination'] is None
    assert row['hardValid'] is None


@pytest.fixture(scope='module')
def comparison_report():
    report = {'environment': {'python': platform.python_version(), 'platform': platform.platform()},
              'scope': 'in-process search; excludes worker startup, API and save latency',
              'results': []}
    yield report
    destination = os.environ.get('TEACHING_COMPARISON_REPORT')
    if destination:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


@pytest.mark.parametrize('scenario', SCENARIOS)
@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_real_algorithm_comparison(scenario, algorithm, comparison_report):
    courses, fixed = comparison_scenarios()[scenario]
    row = measure_comparison(scenario, algorithm, courses, fixed, seconds=2)
    comparison_report['results'].append(row)
    assert row['status'] == 'measured', f"{algorithm}/{scenario}: {row['status']}"
    assert row['hardValid'] is True
    assert row['requiredUnits'] == row['scheduledUnits'] + row['remainingUnits']
    assert row['elapsedSeconds'] <= row['allowanceSeconds'] + 1.0, 'Search exceeded its allowance plus 1s finalization tolerance'
    if algorithm != 'standard':
        assert row['optimal'] is False
        assert not any(p['proof_status'] == 'proven' for p in row['proofs'][1:])


def comparison_scenarios():
    """Six small deterministic inputs; protected occupancy is identical per strategy."""
    span = PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=27))
    common = (TimeWindowPlan(1, 0, time(8), time(12)),
              TimeWindowPlan(2, 2, time(8), time(12)))
    def course(identifier, **options):
        return replace(optimization_course(identifier, total_units=6, windows=common, **options),
                       planning_period=span, preferred_session_units=3)
    protected = (replace(fixed_session(course_id=91, cohort_id=1, lecturer_id=1,
        room_id=1, start=time(6), end=time(7)), units=1),
        fixed_session(course_id=92, cohort_id=2, lecturer_id=2, room_id=2,
            start=time(8), end=time(9), source_kind='active_exam', source_id=992))
    intensive = (*common, *tuple(TimeWindowPlan(11+i,None,time(8),time(12),kind='dated',
        date=SEMESTER_START+timedelta(days=7+offset),is_intensive=True) for i,offset in enumerate((0,2))))
    return {
        'single': ((course(1),), protected),
        'cohort_competition': ((course(1, cohort_id=1, lecturer_ids=(1, 2), room_ids=(1, 2)),
                                course(2, cohort_id=1, lecturer_ids=(1, 2), room_ids=(1, 2))), protected),
        'shared_lecturer': ((course(1, lecturer_ids=(1,)), course(2, lecturer_ids=(1,))), protected),
        'intensive': ((replace(course(1), windows=intensive), replace(course(2,cohort_id=1),windows=intensive)), protected),
        'partial_week': ((replace(course(1), planning_period=PlanningPeriodPlan(
            SEMESTER_START + timedelta(days=2), SEMESTER_START + timedelta(days=15))),), protected),
        'twenty': (selection(20), protected),
    }


def measure_comparison(scenario, algorithm, courses, fixed, *, seconds):
    """Time only search; independently validate and derive loads afterwards.

    No policy, database, HTTP endpoint or live application state is accessed.
    A fresh absolute control/deadline and a detached copy are used for every run.
    """
    from app.services.conflict_aware_generation import validate_exact_candidate
    from app.services.semester_optimization import CourseOptimization, SemesterOptimizationResult

    required = sum(c.total_units for c in courses)
    row = dict(scenario=scenario, algorithm=algorithm, snapshot=snapshot_identity(courses, fixed),
        allowanceSeconds=seconds, requiredUnits=required, status='unavailable',
        scheduledUnits=None, remainingUnits=None, elapsedSeconds=None,
        termination=None, hardValid=None, weeklyCohortUnits={}, weeklyLecturerUnits={},
        proofs=[], objectiveProfile='standard-v1' if algorithm == 'standard' else 'heuristic-v1',
        optimal=None, usableCandidate=False)
    try:
        strategy = get_strategy(algorithm)
    except ValueError:
        return row
    detached_courses, detached_fixed = deepcopy((courses, fixed))
    checkpoints = []
    started = monotonic()
    control = OptimizationSearchControl(deadline=started + seconds,
                                       checkpoint=checkpoints.append)
    termination = None
    try:
        result = strategy.optimize(detached_courses, detached_fixed, (), holidays={},
            generated_only=True, deadline_seconds=seconds, allow_unproven=True, control=control)
    except (OptimalResultNotProven, NoGeneratedAlternative):
        termination = 'deadline' if monotonic() >= control.deadline else 'standard_completed' if algorithm == 'standard' else 'heuristic_completed'
        result = checkpoints[-1] if checkpoints else SemesterOptimizationResult(
            courses=tuple(CourseOptimization(c.course_id, (), False, 0, 0, 0, ()) for c in courses),
            total_units=0, conflicts=0, lecturer_changes=0, room_changes=0,
            retained_drafts=0, elapsed_milliseconds=0, optimal=False)
    elapsed = monotonic() - started
    validate_exact_candidate(courses, fixed, (), {}, result.courses, algorithm=algorithm)
    facts = completed_facts(result)
    cohort_by_course = {c.course_id: c.cohort_id for c in courses}
    loads = {'cohort': {}, 'lecturer': {}}
    for candidate in result.courses:
        for session in candidate.sessions:
            week = week_start(session.date).isoformat()
            for owner, identity in (('cohort', cohort_by_course[candidate.course_id]), ('lecturer', session.lecturer_id)):
                series = loads[owner].setdefault(str(identity), {})
                series[week] = series.get(week, 0) + session.units
    for session in fixed:
        if session.source_kind != 'teaching_session':
            continue
        for owner, identity in (('cohort', session.cohort_id), ('lecturer', session.lecturer_id)):
            if str(identity) in loads[owner]:
                series = loads[owner][str(identity)]
                week = week_start(session.date).isoformat()
                series[week] = series.get(week, 0) + session.units
    # The raw weekly measurements are owner-specific; they are not labelled as
    # equivalent objective scores across Standard and heuristic proof profiles.
    row.update(status='measured', scheduledUnits=result.total_units,
        remainingUnits=required-result.total_units, elapsedSeconds=round(elapsed, 6),
        termination=termination or getattr(result, 'termination', None) or (
            'deadline' if result.search_exhausted else 'standard_completed' if algorithm == 'standard' else 'heuristic_completed'),
        hardValid=True, weeklyCohortUnits=loads['cohort'], weeklyLecturerUnits=loads['lecturer'],
        proofs=facts['objectives'], optimal=result.optimal, usableCandidate=result.total_units > 0,
        unitUpperBound=result.unit_upper_bound,
        additionalPossibleUnits=(result.unit_upper_bound-result.total_units if result.unit_upper_bound is not None else None),
        intensiveTeachingTime=result.intensive_teaching_time, dailyVariety=result.daily_variety)
    return row


@pytest.mark.parametrize('algorithm', ALGORITHMS)
@pytest.mark.parametrize('count', [1, 20])
def test_real_spawned_dispatch_and_status_delivery(algorithm, count, comparison_report):
    from app.services.optimization_worker import SolverProcess, DetachedOptimizationInput
    from app.services.conflict_aware_generation import validate_exact_candidate
    courses = selection(count)
    started = monotonic()
    problem = DetachedOptimizationInput(courses, (), (), {}, started + 10,
        algorithm=algorithm, strategy_profile='standard-v1' if algorithm == 'standard' else 'heuristic-v1')
    worker = SolverProcess(problem)
    acknowledged = monotonic() - started
    observations = []
    try:
        while monotonic() < problem.deadline + 1:
            observations.extend((monotonic(), message) for message in worker.receive())
            if any(message['kind'] in ('result', 'timeout', 'failed') for _, message in observations):
                break
            sleep(.01)
        result = next(message['result'] for _, message in observations if message['kind'] == 'result')
        validate_exact_candidate(courses, (), (), {}, result.courses, algorithm=algorithm)
        assert result.total_units == 2 * count
        assert acknowledged < 1
        assert any(message.get('phase') == 'optimizing' for _, message in observations)
        updates = [stamp for stamp, message in observations if message['kind'] in ('phase', 'checkpoint', 'result')]
        assert max((b-a for a, b in zip(updates, updates[1:])), default=0) <= 5
        comparison_report.setdefault('workerRuns', []).append(dict(algorithm=algorithm,
            courseCount=count, snapshot=snapshot_identity(courses, ()), allowanceSeconds=10,
            dispatchAcknowledgementSeconds=round(acknowledged, 6), elapsedSeconds=round(monotonic()-started, 6),
            scheduledUnits=result.total_units, remainingUnits=0, hardValid=True))
    finally:
        worker.close()


@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_real_spawned_expired_deadline_and_cancel_acknowledgement(algorithm, comparison_report):
    from app.services.optimization_worker import SolverProcess, DetachedOptimizationInput
    expired = DetachedOptimizationInput(selection(1), (), (), {}, monotonic() - 1, algorithm=algorithm)
    worker = SolverProcess(expired)
    try:
        messages = []
        end = monotonic() + 10
        while monotonic() < end:
            messages.extend(worker.receive())
            if any(m['kind'] in ('result', 'timeout', 'failed') for m in messages):
                break
            sleep(.01)
        assert any(m['kind'] == 'timeout' and m['budgetExhausted'] for m in messages)
        assert not any(m['kind'] == 'result' for m in messages)
    finally:
        worker.close()
    from tests.optimization_fixtures import reference_performance_courses
    active = SolverProcess(DetachedOptimizationInput(tuple(reference_performance_courses()), (), (), {}, monotonic()+10, algorithm=algorithm))
    try:
        end = monotonic() + 5
        while monotonic() < end:
            if any(m.get('phase') == 'optimizing' for m in active.receive()):
                break
            sleep(.01)
        started = monotonic()
        active.close()
        elapsed = monotonic() - started
        assert elapsed < 1 and not active.is_alive()
        comparison_report.setdefault('workerControls', []).append(dict(algorithm=algorithm,
            expiredDeadlineReturnedNoResult=True, cancellationAcknowledgementSeconds=round(elapsed, 6)))
    finally:
        active.close()


@pytest.mark.parametrize('algorithm', ALGORITHMS)
def test_real_active_search_honors_original_absolute_allowance(algorithm, comparison_report):
    from app.services.optimization_worker import SolverProcess, DetachedOptimizationInput
    courses = tuple(optimization_course(i,total_units=80,lecturer_ids=(1,2),room_ids=(1,2)) for i in range(1,21))
    started = monotonic()
    allowance = 2
    worker = SolverProcess(DetachedOptimizationInput(courses,(),(),{},started+allowance,algorithm=algorithm))
    messages = []
    try:
        while monotonic() < started+allowance+1:
            messages.extend(worker.receive())
            if any(m['kind'] in ('result','timeout','failed') for m in messages):
                break
            sleep(.01)
        elapsed = monotonic()-started
        assert any(m.get('phase') == 'optimizing' for m in messages), 'Must measure an active search, not startup expiry'
        terminal = next(m for m in messages if m['kind'] in ('result','timeout','failed'))
        assert terminal['kind'] != 'failed'
        exhausted = terminal.get('budgetExhausted') if terminal['kind']=='timeout' else terminal['result'].search_exhausted
        # A faster completed search is valid. Requiring every native run to
        # time out makes this a hardware-speed assertion instead of a budget test.
        assert elapsed <= allowance+1
        comparison_report.setdefault('activeDeadlines',[]).append(dict(algorithm=algorithm,
            snapshot=snapshot_identity(courses,()),allowanceSeconds=allowance,
            elapsedSeconds=round(elapsed,6),budgetExhausted=bool(exhausted)))
    finally:
        worker.close()
