from dataclasses import replace
from datetime import timedelta
from datetime import datetime, time
from fractions import Fraction

import pytest

from app.services.teaching_preferences import derive_portions, balance_cost, rhythm_penalty, opportunity_calendar
from app.services.teaching_preferences import score_arrangement
from app.services.schedule_generation import GeneratedSession, TimeWindowPlan, session_duration_minutes, PlanningPeriodPlan
from app.services.semester_optimization import generate_candidates, week_start
from tests.fixtures.teaching_strategies import BALANCE_CASES, PORTION_CASES, exact22
from tests.optimization_fixtures import SEMESTER_START, optimization_course, resource


@pytest.mark.parametrize('interruption', ['cancel', 'deadline'])
def test_scarcity_scan_observes_control_inside_candidate_iteration(interruption):
    from app.services.teaching_preferences import scarcity_key
    from app.services.semester_optimization import OptimizationSearchControl, OptimizationCancelled, OptimalResultNotProven
    course = exact22()
    candidate = generate_candidates(course, (), frozenset()).candidates[0]
    visited = []
    def candidates():
        for index in range(100):
            visited.append(index)
            yield candidate
    control = OptimizationSearchControl(1,
        cancelled=lambda: interruption == 'cancel' and len(visited) >= 5,
        clock=lambda: 1 if interruption == 'deadline' and len(visited) >= 5 else 0)
    with pytest.raises(OptimizationCancelled if interruption == 'cancel' else OptimalResultNotProven):
        scarcity_key(course, candidates(), control=control)
    assert len(visited) == 5


@pytest.mark.parametrize('interruption', ['cancel', 'deadline'])
def test_intensive_scoring_observes_control_inside_fixed_occupancy(interruption):
    from app.services.semester_optimization import intensive_arrangement, OptimizationSearchControl, OptimizationCancelled, OptimalResultNotProven
    from tests.fixtures.teaching_strategies import intensive22
    from tests.optimization_fixtures import fixed_session
    visited = []
    def fixed():
        for index in range(100):
            visited.append(index)
            yield fixed_session(source_id=index)
    control = OptimizationSearchControl(1,
        cancelled=lambda: interruption == 'cancel' and len(visited) >= 5,
        clock=lambda: 1 if interruption == 'deadline' and len(visited) >= 5 else 0)
    with pytest.raises(OptimizationCancelled if interruption == 'cancel' else OptimalResultNotProven):
        intensive_arrangement((intensive22(),), fixed(), {}, control=control)
    assert len(visited) == 5


@pytest.mark.parametrize('loads,weights,expected', BALANCE_CASES)
def test_approved_numeric_balance(loads, weights, expected):
    assert balance_cost(loads, weights) == Fraction(str(expected))


@pytest.mark.parametrize('total,count,expected', PORTION_CASES)
def test_equal_whole_portions_in_fixed_code_order(total, count, expected):
    course = optimization_course(1, total_units=total, lecturer_ids=tuple(range(1, count + 1)))
    portions = derive_portions(replace(course, lecturers=tuple(reversed(course.lecturers))))
    assert tuple(p.required_units for p in portions) == expected
    assert tuple(p.lecturer_id for p in portions) == tuple(range(1, count + 1))


def test_explicit_sizes_do_not_change_code_order_or_transfer():
    course = optimization_course(1, total_units=23, lecturer_ids=(1, 2))
    course = replace(course, lecturers=(resource(1, 'b'), resource(2, 'a')))
    portions = derive_portions(course, {1: 15, 2: 8})
    assert [(p.lecturer_id, p.required_units, p.source) for p in portions] == [(2, 8, 'explicit'), (1, 15, 'explicit')]
    for invalid in ({1: -1, 2: 24}, {1: True, 2: 22}, {1: 11}, {1: 12, 2: 12}):
        with pytest.raises(ValueError):
            derive_portions(course, invalid)


def test_opportunity_dates_deduplicate_windows_and_week_rhythm_excludes_boundaries():
    course = exact22()
    candidates = generate_candidates(course, (), frozenset()).candidates
    calendar = opportunity_calendar(course, candidates)
    repeated = opportunity_calendar(course, candidates + candidates)
    assert calendar == repeated
    assert len(calendar) == 7
    first = week_start(SEMESTER_START)
    assert rhythm_penalty({first: 1, first + timedelta(weeks=6): 1}, calendar) == 5
    assert rhythm_penalty({first: 1}, calendar) == 0
    assert rhythm_penalty({first: 2}, calendar) == 1


def test_staggered_cohort_has_exact_36_vs_72_cost_with_equal_higher_priorities():
    from tests.fixtures.teaching_strategies import preference_inputs
    courses, fixed = preference_inputs()['staggered_cohort']
    candidates = {c.course_id: generate_candidates(c, fixed, frozenset()).candidates for c in courses}
    def sessions(course, weeks):
        values = []
        for week in weeks:
            day = SEMESTER_START + timedelta(weeks=week, days=course.windows[0].weekday)
            start = time(8)
            end = (datetime.combine(day, start)+timedelta(minutes=session_duration_minutes(3))).time()
            values.append(GeneratedSession(day,start,end,3,course.windows[0].id,0,1,1))
        return tuple(values)
    sequential = {courses[0].course_id:sessions(courses[0], (0,1)),courses[1].course_id:sessions(courses[1], (2,3))}
    overlapping = {courses[0].course_id:sessions(courses[0], (0,1)),courses[1].course_id:sessions(courses[1], (0,1))}
    a = score_arrangement(courses,fixed,sequential,candidates,'cohort')
    b = score_arrangement(courses,fixed,overlapping,candidates,'cohort')
    assert a[:5] == b[:5]
    assert (a[5],b[5]) == (36,72)
    assert a < b


def test_actual_intensive_overlap_merges_markers_and_excludes_breaks():
    course = replace(optimization_course(1,total_units=2,min_units=2,max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START,SEMESTER_START),
        windows=(TimeWindowPlan(1,0,time(9),time(12)),
                 TimeWindowPlan(2,None,time(9,40),time(10),kind='dated',date=SEMESTER_START,is_intensive=True)))
    sessions = {1:(GeneratedSession(SEMESTER_START,time(9),time(10,40),2,1,0,1,1),)}
    candidates = {1:generate_candidates(course,(),frozenset()).candidates}
    score = score_arrangement((course,),(),sessions,candidates,'cohort')
    assert -score[1] == 10 * 60_000_000
    duplicate = replace(course,windows=(*course.windows,course.windows[1]))
    repeated = score_arrangement((duplicate,),(),sessions,candidates,'cohort')
    assert repeated == score


def test_partial_and_zero_opportunity_weeks_do_not_use_raw_minutes():
    from tests.fixtures.teaching_strategies import preference_inputs
    course = preference_inputs()['partial_boundary'][0][0]
    candidates = generate_candidates(course,(),frozenset()).candidates
    calendar = opportunity_calendar(course,candidates)
    assert len(calendar) == 1
    assert all(cadence == 1 for _,cadence in calendar.values())


def test_scarcity_is_deduplicated_and_specific_to_lecturer_group():
    from app.services.teaching_preferences import scarcity_key
    course = optimization_course(1,total_units=4,lecturer_ids=(1,2))
    values = generate_candidates(course,(),frozenset()).candidates
    first = replace(values[0],lecturer_ids=(1,))
    second = replace(values[-1],lecturer_ids=(2,))
    assert scarcity_key(course,(first,first,second)) == (2,2,1)
    assert scarcity_key(course,(first,first,second),lecturer_id=1) == (1,1,1)
    assert scarcity_key(course,(first,second),lecturer_id=99) == (0,0,1)


def test_lecturer_course_rhythm_precedes_flattening_aggregate_load():
    from tests.fixtures.teaching_strategies import preference_inputs
    first = preference_inputs()['staggered_cohort'][0][0]
    second = replace(first,course_id=2,cohort_id=2,windows=(TimeWindowPlan(2,2,time(8),time(12)),))
    courses = (first,second)
    candidates = {c.course_id:generate_candidates(c,(),frozenset()).candidates for c in courses}
    def values(course,weeks):
        return tuple(GeneratedSession(SEMESTER_START+timedelta(weeks=w,days=course.windows[0].weekday),
            time(8),time(10,35),3,course.windows[0].id,0,1,1) for w in weeks)
    steady = {1:values(first,(0,1)),2:values(second,(0,1))}
    smooth = {1:values(first,(0,2)),2:values(second,(1,3))}
    a = score_arrangement(courses,(),steady,candidates,'lecturer')
    b = score_arrangement(courses,(),smooth,candidates,'lecturer')
    assert a[:4] == b[:4]
    assert (a[4:6],b[4:6]) == ((0,72),(2,36))
    assert a < b


def test_room_metrics_and_protected_instruction_are_counted_once():
    from tests.optimization_fixtures import fixed_session
    course = replace(optimization_course(1,total_units=2,min_units=1,max_units=1,room_ids=(1,2)),
        planning_period=PlanningPeriodPlan(SEMESTER_START,SEMESTER_START+timedelta(days=7)))
    fixed = replace(fixed_session(cohort_id=1,lecturer_id=99,room_id=2,start=time(6),end=time(6,45),source_id=99),units=1)
    candidates = {1:generate_candidates(course,(fixed,),frozenset()).candidates}
    left = GeneratedSession(SEMESTER_START,time(8),time(8,45),1,1,0,1,1)
    right = replace(left,date=SEMESTER_START+timedelta(days=7),room_id=2)
    a = score_arrangement((course,),(fixed,fixed),{1:(left,right)},candidates,'cohort')
    b = score_arrangement((course,),(fixed,),{1:(replace(left,room_id=2),right)},candidates,'cohort')
    assert a[:6] == b[:6]
    assert a[5] == 5  # [2,1] weekly instructional LE, excluding duplicate source.
    assert (a[6:8],b[6:8]) == ((1,1),(0,0))
    assert b < a
