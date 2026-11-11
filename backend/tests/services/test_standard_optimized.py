from dataclasses import replace
from datetime import time, timedelta
import hashlib
from pathlib import Path

import pytest

from app.services.semester_optimization import OptimizationCancelled, OptimizationSearchControl, week_start
from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan
from app.services.teaching_strategies import get_strategy
from tests.optimization_fixtures import SEMESTER_START, optimization_course, fixed_session


def spread_course():
    return replace(optimization_course(1, total_units=8, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=55)),
        windows=(TimeWindowPlan(1, 0, time(8), time(10)),))


def run(courses, fixed=(), **options):
    return get_strategy('standard_optimized').optimize(courses, fixed, generated_only=True,
        deadline_seconds=5, allow_unproven=True, **options)


def test_separate_strategy_reuses_standard_without_modifying_its_source():
    source = Path(__file__).parents[2] / 'app/services/semester_optimization.py'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    assert type(get_strategy('standard_optimized')) is not type(get_strategy('standard'))
    run((spread_course(),))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_full_coverage_spreads_over_effective_period_instead_of_earliest_weeks():
    course = spread_course()
    standard = get_strategy('standard').optimize((course,), (), generated_only=True, deadline_seconds=5)
    result = run((course,))
    sessions = result.courses[0].sessions
    assert result.total_units == standard.total_units == 8
    assert max(s.date for s in sessions) >= SEMESTER_START + timedelta(days=42)
    assert max(s.date for s in standard.courses[0].sessions) < SEMESTER_START + timedelta(days=28)
    weeks = sorted((week_start(s.date)-SEMESTER_START).days//7 for s in sessions)
    assert weeks == [0, 2, 4, 6] or weeks == [1, 3, 5, 7]
    assert [e.objective_key for e in result.objectives][4] == 'weekly_spread'
    assert result.objectives[0].proof_status == 'proven'


def test_fixed_occupancy_and_unavailable_dates_remain_hard():
    course = spread_course()
    blocked = SEMESTER_START + timedelta(days=49)
    fixed = fixed_session(course_id=99, cohort_id=course.cohort_id, lecturer_id=1, room_id=1,
        session_date=SEMESTER_START + timedelta(days=42), start=time(8), end=time(10))
    result = run((course,), (fixed,), unavailable_dates=(blocked,))
    assert result.total_units == 8
    assert all(s.date not in (fixed.date, blocked) for s in result.courses[0].sessions)


def test_coverage_outranks_spread_when_only_early_capacity_exists():
    course = spread_course()
    result = run((course,), unavailable_dates=tuple(SEMESTER_START+timedelta(days=7*i) for i in range(2,8)))
    assert result.total_units == 4
    assert len(result.courses[0].sessions) == 2


def test_cancellation_is_not_swallowed_by_the_extension():
    with pytest.raises(OptimizationCancelled):
        run((spread_course(),), control=OptimizationSearchControl(deadline=float('inf'), cancelled=lambda: True))


def test_stage_budget_reserves_distribution_time():
    from app.services.standard_optimized import stage_budget_seconds, STAGE_WEIGHTS
    assert sum(STAGE_WEIGHTS) == 100
    assert stage_budget_seconds(100, 0) == 35
    assert stage_budget_seconds(55, 4) == 40
    assert stage_budget_seconds(8, 10) == 8


def test_unproven_spread_keeps_coverage_and_marks_later_proof_conditional(monkeypatch):
    from ortools.sat.python import cp_model
    original = cp_model.CpSolver.solve
    stages = []
    def report_bounded(self, model, callback=None):
        status = original(self, model, callback)
        stages.append(status)
        # Constructive full coverage skips its solve, so the first solve is
        # weekly_spread; force an
        # unproven feasible result to exercise the bounded-stage transition.
        return cp_model.FEASIBLE if len(stages) == 1 else status
    monkeypatch.setattr(cp_model.CpSolver, 'solve', report_bounded)
    result = run((spread_course(),))
    assert result.total_units == 8
    assert not result.optimal
    evidence = {e.objective_key:e for e in result.objectives}
    assert evidence['total_units'].proof_status == 'proven'
    assert evidence['weekly_spread'].proof_status == 'unfinished'
    assert evidence['canonical_resource'].proof_status == 'conditional'


def test_checkpoints_are_shared_immutable_results_with_distribution_evidence():
    from time import monotonic
    checkpoints = []
    result = run((spread_course(),), control=OptimizationSearchControl(deadline=monotonic()+5, checkpoint=checkpoints.append))
    assert checkpoints
    assert all(c.total_units <= result.total_units for c in checkpoints)
    assert all(len(c.objectives) == 11 for c in checkpoints)
    assert result.termination == 'standard_optimized_completed'


def test_deadline_during_distribution_retains_coverage_without_claiming_proof():
    from time import monotonic
    deadline = monotonic() + 5
    expired = False
    def progress(key):
        nonlocal expired
        if key == 'weekly_spread':
            expired = True
    result = run((spread_course(),), control=OptimizationSearchControl(deadline=deadline,
        clock=lambda: deadline+1 if expired else monotonic(), progress=progress))
    assert result.total_units == 8
    assert result.termination == 'deadline' and result.search_exhausted
    assert not result.optimal
    assert result.objectives[4].proof_status == 'unfinished'


def test_cancellation_after_checkpoint_does_not_return_the_candidate():
    from time import monotonic
    cancelled = False
    def checkpoint(_):
        nonlocal cancelled
        cancelled = True
    with pytest.raises(OptimizationCancelled):
        run((spread_course(),), control=OptimizationSearchControl(deadline=monotonic()+5,
            cancelled=lambda: cancelled, checkpoint=checkpoint))


def test_constructive_candidate_precedes_model_build_and_survives_unknown(monkeypatch):
    from time import monotonic
    from ortools.sat.python import cp_model
    from app.services import standard_optimized as strategy
    from app.services.conflict_aware_generation import validate_exact_candidate
    checkpoints, stages = [], []
    original = cp_model.CpModel
    def build(*args, **kwargs):
        assert checkpoints, 'A validated proposal must exist before expensive model construction'
        return original(*args, **kwargs)
    monkeypatch.setattr(cp_model, 'CpModel', build)
    monkeypatch.setattr(cp_model.CpSolver, 'solve', lambda *args: cp_model.UNKNOWN)
    course = spread_course()
    result = run((course,), control=OptimizationSearchControl(monotonic()+5,
        checkpoint=checkpoints.append, progress=stages.append))
    validate_exact_candidate((course,), (), (), {}, result.courses, algorithm='standard_optimized')
    assert result.total_units == checkpoints[0].total_units == course.total_units
    assert result.courses == checkpoints[-1].courses
    assert 'total_units' not in stages
    assert result.objectives[0].proof_status == 'proven'
    assert result.unit_upper_bound == course.total_units
    assert not result.optimal
    assert result.objectives[4].proof_status == 'unfinished'


def test_model_build_deadline_keeps_validated_starting_candidate():
    from time import monotonic
    deadline = monotonic()+5
    checkpoints = []
    def checkpoint(candidate):
        checkpoints.append(candidate)
    result = run((spread_course(),), control=OptimizationSearchControl(deadline,
        clock=lambda: deadline+1 if checkpoints else monotonic(), checkpoint=checkpoint))
    assert result.courses == checkpoints[0].courses
    assert result.total_units == 8
    assert result.termination == 'deadline' and result.search_exhausted
    assert not result.optimal
    assert result.objectives[0].proof_status == 'proven'
    assert all(e.proof_status != 'proven' for e in result.objectives[1:])


def test_partial_starting_candidate_is_retained_without_claiming_full_coverage(monkeypatch):
    from time import monotonic
    from ortools.sat.python import cp_model
    monkeypatch.setattr(cp_model.CpSolver, 'solve', lambda *args: cp_model.UNKNOWN)
    blocked = tuple(SEMESTER_START+timedelta(days=7*i) for i in range(2,8))
    checkpoints = []
    result = run((spread_course(),), unavailable_dates=blocked,
        control=OptimizationSearchControl(monotonic()+5, checkpoint=checkpoints.append))
    assert result.total_units == checkpoints[0].total_units == 4
    assert result.objectives[0].proof_status == 'unfinished'
    assert not result.optimal


def test_no_starting_candidate_uses_remaining_coverage_budget(monkeypatch):
    from time import monotonic
    from ortools.sat.python import cp_model
    from app.services import standard_optimized as strategy
    from app.services.semester_optimization import OptimalResultNotProven
    monkeypatch.setattr(strategy, '_construct_completion', lambda *args, **kwargs: {})
    allowances = []
    def unknown(self, *args):
        allowances.append(self.parameters.max_time_in_seconds)
        return cp_model.UNKNOWN
    monkeypatch.setattr(cp_model.CpSolver, 'solve', unknown)
    with pytest.raises(OptimalResultNotProven):
        run((spread_course(),), control=OptimizationSearchControl(monotonic()+5))
    assert len(allowances) == 1 and 4 < allowances[0] <= 5


def test_starting_objectives_equal_exact_model_for_the_same_assignment(monkeypatch):
    from time import monotonic
    from app.services import optimization_incumbent
    from app.services.schedule_generation import TimeWindowPlan
    from tests.optimization_fixtures import resource
    original = optimization_incumbent.seed_incumbent
    pinned = []
    def pin(model, *args, **kwargs):
        pinned.append(args[2])
        result = original(model, *args, **kwargs)
        hint = model.proto.solution_hint
        for index, value in zip(hint.vars, hint.values):
            model.add(model.get_int_var_from_proto_index(index) == value)
        return result
    monkeypatch.setattr(optimization_incumbent, 'seed_incumbent', pin)
    windows = (TimeWindowPlan(1, 0, time(8), time(12)),
        TimeWindowPlan(2, None, time(8), time(12), kind='dated',
            date=SEMESTER_START+timedelta(days=1), is_intensive=True))
    first = replace(spread_course(), windows=windows, min_session_units=2,
        max_session_units=4, lecturers=(resource(1, 'L1'),resource(2,'L2')),
        rooms=(resource(1,'R1',capacity=100),resource(2,'R2',capacity=100)))
    second = replace(first, course_id=2, total_units=5)
    fixed = fixed_session(course_id=99, cohort_id=first.cohort_id, lecturer_id=9,
        room_id=2, session_date=SEMESTER_START, start=time(8), end=time(9))
    checkpoints = []
    other_fixed = replace(fixed,room_id=1,lecturer_id=8,start_time=time(7),end_time=time(8))
    result = run((first, second), (fixed,other_fixed), control=OptimizationSearchControl(
        monotonic()+5, checkpoint=checkpoints.append))
    assert result.optimal
    starting = {e.objective_key:e.value for e in pinned[0].objectives}
    assert starting['intensive_teaching_time'] > 0
    assert starting['room_changes'] > 0
    assert starting['schedule_shape'] > 0
    assert {e.objective_key:e.value for e in result.objectives} == starting


def test_timeout_starting_plan_already_spreads_over_the_semester(monkeypatch):
    from ortools.sat.python import cp_model
    monkeypatch.setattr(cp_model.CpSolver, 'solve', lambda *args: cp_model.UNKNOWN)
    result = run((spread_course(),))
    sessions = result.courses[0].sessions
    assert result.total_units == 8
    assert max(s.date for s in sessions) >= SEMESTER_START+timedelta(days=42)
    assert next(e.value for e in result.objectives if e.objective_key == 'weekly_spread') <= 32


def test_new_run_reuses_a_better_valid_saved_arrangement(monkeypatch):
    from ortools.sat.python import cp_model
    from app.services.semester_optimization import CurrentSession
    course = spread_course()
    optimal = run((course,))
    saved = replace(course, current_sessions=tuple(CurrentSession(
        course_id=course.course_id, cohort_id=course.cohort_id, date=s.date,
        start_time=s.start_time, end_time=s.end_time, units=s.units,
        time_window_id=s.time_window_id, constraint_window_index=s.constraint_window_index,
        lecturer_id=s.lecturer_id, room_id=s.room_id) for s in optimal.courses[0].sessions))
    monkeypatch.setattr(cp_model.CpSolver, 'solve', lambda *args: cp_model.UNKNOWN)
    from app.services import standard_optimized as strategy
    monkeypatch.setattr(strategy, '_construct_completion', lambda *args, **kwargs: {})
    result = run((saved,))
    assert result.courses[0].sessions == optimal.courses[0].sessions
    assert result.total_units == 8 and result.objectives[0].proof_status == 'proven'


def test_invalid_saved_arrangement_is_not_used_as_a_seed(monkeypatch):
    from ortools.sat.python import cp_model
    from app.services.semester_optimization import CurrentSession
    course = spread_course()
    saved = replace(course, current_sessions=(CurrentSession(course_id=course.course_id,
        cohort_id=course.cohort_id, date=SEMESTER_START, start_time=time(8),
        end_time=time(10), units=2, time_window_id=1, constraint_window_index=0,
        lecturer_id=999, room_id=999),))
    monkeypatch.setattr(cp_model.CpSolver, 'solve', lambda *args: cp_model.UNKNOWN)
    result = run((saved,))
    assert result.total_units == 8
    assert all(s.lecturer_id != 999 and s.room_id != 999 for s in result.courses[0].sessions)


def test_compact_model_has_one_interval_per_course_day_resource(monkeypatch):
    from ortools.sat.python import cp_model
    from tests.optimization_fixtures import optimization_course
    models = []
    def unknown(self, model, *args):
        models.append(model.proto)
        return cp_model.UNKNOWN
    monkeypatch.setattr(cp_model.CpSolver, 'solve', unknown)
    course = optimization_course(1, total_units=8, min_units=2, max_units=4,
        lecturer_ids=(1,2), room_ids=(1,2))
    run((course,))
    intervals = sum(c.has_interval() for c in models[0].constraints)
    # Each Monday has cohort + two lecturer + two room intervals.
    assert intervals == 5*((course.planning_period.end_date-course.planning_period.start_date).days//7+1)


@pytest.mark.parametrize('shared_cohort', [False,True])
@pytest.mark.parametrize('blocked_end', [time(10),time(10,0,0,123)])
def test_compact_and_original_models_have_identical_exact_objectives(shared_cohort,blocked_end):
    from app.services.standard_optimized import optimize_semester
    from app.services.conflict_aware_generation import validate_exact_candidate
    from tests.optimization_fixtures import optimization_course
    course = optimization_course(1, total_units=4, min_units=2, max_units=3,
        lecturer_ids=(1,2), room_ids=(1,2))
    course = replace(course,planning_period=PlanningPeriodPlan(SEMESTER_START,SEMESTER_START+timedelta(days=13)))
    second = replace(course, course_id=2, cohort_id=1 if shared_cohort else 2,total_units=3)
    fixed = fixed_session(course_id=99, cohort_id=99, lecturer_id=1, room_id=1,
        session_date=SEMESTER_START, start=time(8), end=blocked_end)
    compact = optimize_semester((course,second), (fixed,), generated_only=True, deadline_seconds=10)
    original = optimize_semester((course,second), (fixed,), generated_only=False, deadline_seconds=10)
    assert [e.value for e in compact.objectives] == [e.value for e in original.objectives]
    validate_exact_candidate((course,second), (fixed,), (), {}, compact.courses, algorithm='standard_optimized')
