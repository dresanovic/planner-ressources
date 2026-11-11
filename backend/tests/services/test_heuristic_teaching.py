from dataclasses import replace
from datetime import timedelta
from time import monotonic

import pytest

from app.services.teaching_strategies import get_strategy
from app.services.conflict_aware_generation import validate_exact_candidate
from app.services.semester_optimization import OptimizationSearchControl, OptimizationCancelled
from tests.fixtures.teaching_strategies import exact22, preference_inputs, selection


def test_lecturer_construction_visits_other_owner_before_successor(monkeypatch):
    from app.services import heuristic_teaching as engine
    from app.services.schedule_generation import PlanningPeriodPlan
    from tests.optimization_fixtures import optimization_course, SEMESTER_START
    period = PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=13))
    courses = (
        replace(optimization_course(1, total_units=4, min_units=2, max_units=2,
            lecturer_ids=(1, 3)), planning_period=period),
        replace(optimization_course(2, total_units=2, min_units=2, max_units=2,
            lecturer_ids=(2,)), planning_period=period),
    )
    monkeypatch.setattr(engine, 'REPAIR_LIMIT', 0)
    trace = []
    control = OptimizationSearchControl(monotonic() + 10,
        checkpoint=lambda result: trace.append(tuple(
            (c.course_id, s.lecturer_id) for c in result.courses for s in c.sessions)))
    result = get_strategy('lecturer').optimize(courses, (), control=control)
    first_seen = {pair: next(i for i, values in enumerate(trace) if pair in values)
                  for pair in ((1, 1), (2, 2), (1, 3))}
    assert first_seen[(1, 1)] < first_seen[(2, 2)] < first_seen[(1, 3)]
    validate_exact_candidate(courses, (), (), {}, result.courses, algorithm='lecturer')


@pytest.mark.parametrize('zero_first', [False, True])
def test_construction_reranks_groups_using_only_outstanding_demand(monkeypatch, zero_first):
    from app.services import heuristic_teaching as engine
    from app.services.schedule_generation import PlanningPeriodPlan
    from tests.optimization_fixtures import optimization_course, SEMESTER_START
    courses = tuple(replace(optimization_course(i, total_units=0 if zero_first and i == 1 else 2,
        min_units=2, max_units=2, cohort_id=1 if i != 2 else 2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(weeks=weeks)))
        for i, weeks in ((1, 0), (2, 1), (3, 2)))
    monkeypatch.setattr(engine, 'REPAIR_LIMIT', 0)
    trace = []
    control = OptimizationSearchControl(monotonic() + 10,
        checkpoint=lambda result: trace.append(tuple(c.course_id for c in result.courses if c.sessions)))
    result = get_strategy('cohort').optimize(courses, (), control=control)
    expected = (2, 3) if zero_first else (1, 2, 3)
    observed = sorted(expected, key=lambda course_id: next(i for i, values in enumerate(trace) if course_id in values))
    assert tuple(observed) == expected
    assert result.total_units == 2 * len(expected)


def test_deadline_during_packet_construction_retains_previous_complete_checkpoint(monkeypatch):
    from app.services import heuristic_teaching as engine
    from tests.optimization_fixtures import OptimizationClock
    clock = OptimizationClock()
    original = engine.SemesterOptimizationResult
    built = []
    def expire_in_packet(*args, **kwargs):
        packet = original(*args, **kwargs)
        built.append(packet.total_units)
        if packet.total_units > 2:
            clock.advance(2)
        return packet
    monkeypatch.setattr(engine, 'SemesterOptimizationResult', expire_in_packet)
    emitted = []
    control = OptimizationSearchControl(1, clock=clock, checkpoint=emitted.append)
    course = replace(exact22(), total_units=4, min_session_units=2, max_session_units=2, preferred_session_units=2)
    result = get_strategy('cohort').optimize((course,), (), control=control)
    assert result.termination == 'deadline'
    assert result.total_units == emitted[-1].total_units == 2
    assert built[-1] > result.total_units
    validate_exact_candidate((course,), (), (), {}, result.courses, algorithm='cohort')


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_real_search_exact22_and_honest_proofs(algorithm):
    course = exact22()
    result = get_strategy(algorithm).optimize((course,), (), generated_only=True, deadline_seconds=5)
    assert result.total_units == 22
    assert sorted(s.units for s in result.courses[0].sessions) == [3, 3, 3, 3, 3, 3, 4]
    assert len({s.date for s in result.courses[0].sessions}) == 7
    assert result.optimal is False
    assert all(o.proof_status != 'proven' for o in result.objectives[1:])
    validate_exact_candidate((course,), (), (), {}, result.courses)


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
@pytest.mark.parametrize('count', [1, 20])
def test_one_and_twenty_courses_share_demand_and_occupancy(algorithm, count):
    courses = selection(count)
    result = get_strategy(algorithm).optimize(courses, (), deadline_seconds=5)
    assert result.total_units == 2 * count
    assert len(result.courses) == count
    validate_exact_candidate(courses, (), (), {}, result.courses)


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
@pytest.mark.parametrize('name', ['ordinary_extra_days', 'intensive_extra_days', 'staggered_cohort', 'shared_lecturer_competition'])
def test_named_coverage_and_shared_hard_rule_cases(algorithm, name):
    courses, fixed = preference_inputs()[name]
    result = get_strategy(algorithm).optimize(courses, fixed, deadline_seconds=5)
    assert result.total_units == sum(c.total_units for c in courses)
    validate_exact_candidate(courses, fixed, (), {}, result.courses)


def test_distinct_owner_fixture_chooses_different_weeks():
    courses, fixed = preference_inputs()['distinct_owner']
    cohort = get_strategy('cohort').optimize(courses, fixed, deadline_seconds=5)
    lecturer = get_strategy('lecturer').optimize(courses, fixed, deadline_seconds=5)
    assert cohort.courses[0].sessions[0].date == courses[0].planning_period.start_date + timedelta(days=7)
    assert lecturer.courses[0].sessions[0].date == courses[0].planning_period.start_date


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_cancel_is_checked_before_candidate_enumeration(algorithm):
    control = OptimizationSearchControl(monotonic() + 5, cancelled=lambda: True)
    with pytest.raises(OptimizationCancelled):
        get_strategy(algorithm).optimize((exact22(),), (), control=control)


@pytest.mark.parametrize('total,targets', [(23,(12,11)),(24,(8,8,8)),(22,(8,7,7))])
def test_lecturer_split_is_sequential_and_nontransferable(total, targets):
    from tests.optimization_fixtures import optimization_course
    course = optimization_course(1, total_units=total, lecturer_ids=tuple(reversed(range(1,len(targets)+1))))
    result = get_strategy('lecturer').optimize((course,), (), deadline_seconds=5)
    sessions = sorted(result.courses[0].sessions, key=lambda s: (s.date, s.start_time))
    assert result.total_units == total
    assert tuple(sum(s.units for s in sessions if s.lecturer_id == i) for i in range(1,len(targets)+1)) == targets
    assert [s.lecturer_id for s in sessions] == sorted(s.lecturer_id for s in sessions)


def test_zero_explicit_portion_does_not_block_a_later_lecturer():
    from tests.optimization_fixtures import optimization_course
    course = replace(optimization_course(1,total_units=2,min_units=1,max_units=1,lecturer_ids=(3,2,1)),
        explicit_lecturer_portions=((3,1),(2,0),(1,1)))
    result = get_strategy('lecturer').optimize((course,),(),deadline_seconds=5)
    assert result.total_units == 2
    assert [s.lecturer_id for s in result.courses[0].sessions] == [1,3]
    validate_exact_candidate((course,),(),(),{},result.courses,algorithm='lecturer')


def test_independent_validator_rejects_reversed_blocks_with_equal_totals():
    from tests.optimization_fixtures import optimization_course
    from app.services.conflict_aware_generation import InvalidExactCandidate
    course = optimization_course(1,total_units=24,lecturer_ids=(1,2,3))
    result = get_strategy('lecturer').optimize((course,),(),deadline_seconds=5)
    first = result.courses[0]
    reversed_blocks = replace(first,sessions=tuple(replace(s,lecturer_id={1:3,2:2,3:1}[s.lecturer_id]) for s in first.sessions))
    with pytest.raises(InvalidExactCandidate):
        validate_exact_candidate((course,),(),(),{},(reversed_blocks,),algorithm='lecturer')


def test_independent_validator_rejects_transferred_lecturer_share():
    from tests.optimization_fixtures import optimization_course
    from app.services.conflict_aware_generation import InvalidExactCandidate
    course = optimization_course(1, total_units=23, lecturer_ids=(1, 2))
    result = get_strategy('lecturer').optimize((course,), (), deadline_seconds=5)
    first = result.courses[0]
    corrupted = replace(first, sessions=tuple(replace(s, lecturer_id=2) for s in first.sessions))
    with pytest.raises(InvalidExactCandidate):
        validate_exact_candidate((course,), (), (), {}, (corrupted,), algorithm='lecturer')


def test_unrepresentable_predecessor_blocks_successor_without_losing_other_courses():
    from tests.optimization_fixtures import optimization_course
    courses = (optimization_course(1, total_units=2, lecturer_ids=(1, 2)), selection(20)[2])
    result = get_strategy('lecturer').optimize(courses, (), deadline_seconds=5)
    assert result.total_units == 2
    assert result.courses[0].scheduled_units == 0
    assert result.courses[1].scheduled_units == 2


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_repair_cap_counts_failures_and_checkpoints_are_immutable(monkeypatch, algorithm):
    from app.services import heuristic_teaching as engine
    from tests.fixtures.teaching_strategies import completed_facts
    monkeypatch.setattr(engine, 'REPAIR_LIMIT', 1)
    captured = []
    control = OptimizationSearchControl(monotonic() + 5, checkpoint=lambda result: captured.append((result, completed_facts(result))))
    course = exact22()
    result = get_strategy(algorithm).optimize((course,), (), control=control)
    assert result.repair_attempts == 1
    assert result.termination == 'repair_limit'
    assert captured
    for previous, facts in captured:
        assert completed_facts(previous) == facts
        validate_exact_candidate((course,), (), (), {}, previous.courses)


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_deadline_retains_checkpoint_without_optimality_or_infeasibility_claim(algorithm):
    from tests.optimization_fixtures import OptimizationClock
    clock = OptimizationClock()
    captured = []
    def stop_after_first(result):
        captured.append(result)
        clock.advance(2)
    control = OptimizationSearchControl(1, clock=clock, checkpoint=stop_after_first)
    result = get_strategy(algorithm).optimize((exact22(),), (), control=control)
    assert result.termination == 'deadline' and result.search_exhausted
    assert result.total_units == captured[0].total_units > 0
    assert result.optimal is False
    validate_exact_candidate((exact22(),), (), (), {}, result.courses, algorithm=algorithm)


def test_checkpoint_refresh_is_bounded_even_during_scoring(monkeypatch):
    from app.services import heuristic_teaching as engine
    from tests.optimization_fixtures import OptimizationClock
    clock = OptimizationClock()
    times = []
    original = engine.score_arrangement
    def slow_score(*args, **kwargs):
        clock.advance(.1)
        return original(*args, **kwargs)
    monkeypatch.setattr(engine, 'score_arrangement', slow_score)
    control = OptimizationSearchControl(40, clock=clock, checkpoint=lambda result: times.append(clock()))
    get_strategy('cohort').optimize((exact22(),), (), control=control)
    assert len(times) >= 2
    assert max(b-a for a,b in zip(times,times[1:])) <= 5.2


@pytest.mark.parametrize('algorithm', ['cohort', 'lecturer'])
def test_large_demand_does_not_spend_budget_on_unplaceable_remainder(algorithm):
    course = replace(selection(1)[0], total_units=1_000_000)
    result = get_strategy(algorithm).optimize((course,), (), deadline_seconds=1)
    assert result.total_units == 2
    assert result.optimal is False


def test_thousandth_repair_attempt_stops_before_1001():
    from tests.optimization_fixtures import resource
    from app.services.schedule_generation import TimeWindowPlan
    from datetime import time
    course = replace(selection(1)[0],total_units=1,min_session_units=1,max_session_units=1,
        windows=(TimeWindowPlan(1,0,time(8),time(9)),),
        rooms=tuple(resource(i,f'R-{i:04}',capacity=40) for i in range(1,1003)))
    result = get_strategy('cohort').optimize((course,),(),deadline_seconds=10)
    assert result.repair_attempts == 1000
    assert result.termination == 'repair_limit'
    assert result.total_units == 1


@pytest.mark.parametrize('count,accepted', [(8,True),(9,False)])
def test_eight_displacement_boundary_rolls_back_without_mutation(count, accepted):
    from app.services.heuristic_teaching import repair_base
    from tests.optimization_fixtures import optimization_course
    from app.services.schedule_generation import GeneratedSession
    from datetime import time
    courses = {i:optimization_course(i,total_units=1,min_units=1,max_units=1,cohort_id=1) for i in range(1,count+1)}
    courses[99] = optimization_course(99,total_units=12,min_units=1,max_units=12,cohort_id=1)
    state = {i:(GeneratedSession(exact22().planning_period.start_date,time(7+i),time(7+i,45),1,1,0,i,i),) for i in range(1,count+1)}
    state[99] = ()
    before = dict(state)
    proposed = GeneratedSession(exact22().planning_period.start_date,time(8),time(18,50),12,1,0,99,99)
    trial = repair_base(courses,state,courses[99],proposed)
    assert (trial is not None) is accepted
    if accepted:
        assert sum(len(v) for v in trial[0].values()) == 0
    assert state == before


def test_reopening_predecessor_counts_successor_removal_and_restores_failed_repair():
    from app.services.heuristic_teaching import repair_base
    from app.services.teaching_preferences import derive_portions
    from tests.optimization_fixtures import optimization_course
    from app.services.schedule_generation import GeneratedSession
    from datetime import time
    course = optimization_course(1,total_units=4,min_units=2,max_units=2,cohort_id=1,lecturer_ids=(1,2))
    other = optimization_course(99,total_units=2,cohort_id=1)
    day = course.planning_period.start_date
    state = {1:(GeneratedSession(day,time(8),time(9,40),2,1,0,1,1),
                GeneratedSession(day+timedelta(days=7),time(8),time(9,40),2,1,0,2,1)),99:()}
    proposed = GeneratedSession(day,time(8),time(9,40),2,1,0,99,99)
    before = dict(state)
    assert repair_base({1:course,99:other},state,other,proposed,portions={1:derive_portions(course),99:derive_portions(other)},max_displaced=1) is None
    assert state == before


@pytest.mark.parametrize('algorithm', ['cohort','lecturer'])
def test_size_redistribution_uses_larger_sessions_when_dates_are_scarce(algorithm):
    course = replace(exact22(),total_units=25)
    result = get_strategy(algorithm).optimize((course,),(),deadline_seconds=5)
    assert result.total_units == 25
    assert len(result.courses[0].sessions) == 7
    validate_exact_candidate((course,),(),(),{},result.courses,algorithm=algorithm)


@pytest.mark.parametrize('phase', ['enumeration','capacity','scoring','repair','rollback','finalization'])
def test_cancellation_in_each_search_phase_never_publishes_a_late_checkpoint(monkeypatch,phase):
    from app.services import heuristic_teaching as engine
    names={'enumeration':'generate_candidates','capacity':'_size_costs','scoring':'score_arrangement',
           'repair':'repair_base','rollback':'repair_base','finalization':'SemesterOptimizationResult'}
    name=names[phase]
    original=getattr(engine,name)
    cancelled=[False]
    emitted=[]
    def interrupt(*args,**kwargs):
        if phase in ('rollback','finalization'):
            value=original(*args,**kwargs)
            cancelled[0]=True
            return value
        cancelled[0]=True
        return original(*args,**kwargs)
    monkeypatch.setattr(engine,name,interrupt)
    def capture(result):
        assert not cancelled[0], 'No checkpoint may be published after registered cancellation'
        emitted.append(result)
    control=OptimizationSearchControl(monotonic()+30,cancelled=lambda:cancelled[0],checkpoint=capture)
    with pytest.raises(OptimizationCancelled):
        get_strategy('cohort').optimize((exact22(),),(),control=control)


@pytest.mark.parametrize('algorithm',['cohort','lecturer'])
def test_cross_course_repair_can_move_full_demand_to_improve_intensive_variety(algorithm):
    from tests.performance.test_teaching_strategy_comparison import comparison_scenarios
    courses,fixed=comparison_scenarios()['intensive']
    result=get_strategy(algorithm).optimize(courses,fixed,deadline_seconds=10)
    assert result.total_units == 12
    assert result.intensive_teaching_time == 8*2_700_000_000
    assert result.daily_variety == 2
    validate_exact_candidate(courses,fixed,(),{},result.courses,algorithm=algorithm)


def test_repair_can_release_an_old_date_for_a_new_date_without_mutating_best():
    from app.services.heuristic_teaching import repair_base
    from app.services.schedule_generation import GeneratedSession
    from tests.optimization_fixtures import optimization_course
    from datetime import time
    course=optimization_course(1,total_units=2)
    session=GeneratedSession(course.planning_period.start_date,time(8),time(9,40),2,1,0,1,1)
    state={1:(session,)}
    result=repair_base({1:course},state,course,replace(session,date=session.date+timedelta(days=7)))
    assert result[0][1] == ()
    assert state == {1:(session,)}
