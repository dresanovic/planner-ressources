from collections import Counter
from dataclasses import replace
from datetime import date, datetime, time, timedelta

from app.services.schedule_generation import PlanningPeriodPlan, ResourceCandidatePlan, TimeWindowPlan
from app.services.holiday_calendar import HolidayReference
import pytest

from app.services.semester_optimization import CurrentSession, FixedSession, NoGeneratedAlternative, generate_candidates, optimize_semester
from tests.optimization_fixtures import SEMESTER_START, optimization_course


def test_equal_intensive_scores_across_dates_preserve_lower_shape_and_stable_ties():
    windows=tuple(TimeWindowPlan(i,None,time(9),time(12,20),kind='dated',date=SEMESTER_START+timedelta(days=offset),is_intensive=True)
                  for i,offset in ((1,0),(2,7)))
    value=replace(optimization_course(1,total_units=2,min_units=1,max_units=2),windows=windows)
    marked=optimize_semester([value],[],generated_only=True,deadline_seconds=10)
    unmarked=optimize_semester([replace(value,windows=tuple(replace(w,is_intensive=False) for w in windows))],[],generated_only=True,deadline_seconds=10)
    # All2LE are intensive and all single-LV contributions are0, whether spread
    # or concentrated. Existing size preference favors one2LE session, then the
    # existing canonical tie chooses the earlier date; no distribution objective.
    assert [c.sessions for c in marked.courses] == [c.sessions for c in unmarked.courses]
    assert [(e.objective_key,e.value) for e in marked.objectives if e.objective_key not in ('intensive_teaching_time','daily_variety')] == [(e.objective_key,e.value) for e in unmarked.objectives if e.objective_key not in ('intensive_teaching_time','daily_variety')]
    assert [(s.date,s.units) for s in marked.courses[0].sessions] == [(SEMESTER_START,2)]
    repeated=optimize_semester([value],[],generated_only=True,deadline_seconds=10)
    assert repeated.courses == marked.courses


def test_same_cohort_same_day_prefers_shared_room_across_courses():
    courses = [replace(optimization_course(i, total_units=2, min_units=2, max_units=2,
        cohort_id=1, room_ids=rooms), planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START))
        for i, rooms in [(1, (1, 2)), (2, (2,))]]
    result = optimize_semester(courses, [], generated_only=True, deadline_seconds=10)
    assert result.total_units == 4 and result.optimal
    assert {s.room_id for c in result.courses for s in c.sessions} == {2}


def test_same_day_room_preference_includes_fixed_occupancy_but_allows_fallback():
    course = replace(optimization_course(1, total_units=2, min_units=2, max_units=2,
        cohort_id=1, room_ids=(1, 2)), planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START))
    fixed = [FixedSession(99, 1, 99, 2, SEMESTER_START, time(8), time(8, 45))]
    preferred = optimize_semester([course], fixed, generated_only=True, deadline_seconds=10)
    assert preferred.courses[0].sessions[0].room_id == 2
    fallback = optimize_semester([replace(course, rooms=(course.rooms[0],))], fixed,
                                generated_only=True, deadline_seconds=10)
    assert fallback.total_units == 2 and fallback.courses[0].sessions[0].room_id == 1


def test_first_search_candidate_tries_preferred_three_units_before_fallback_sizes():
    from app.services.semester_optimization import OptimizationSearchControl, OptimizationCancelled, monotonic
    checkpoints = []
    course = replace(optimization_course(1, total_units=8),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=14)))
    control = OptimizationSearchControl(deadline=monotonic() + 10,
        checkpoint=checkpoints.append, cancelled=lambda: bool(checkpoints))
    with pytest.raises(OptimizationCancelled):
        optimize_semester([course], [], generated_only=True, control=control, allow_unproven=True)
    sessions = sorted(checkpoints[0].courses[0].sessions, key=lambda item: (item.date, item.start_time))
    assert [item.units for item in sessions] == [3, 3, 2]


def test_explicit_preferred_size_overrides_midpoint_in_first_candidate():
    from app.services.semester_optimization import OptimizationSearchControl, OptimizationCancelled, monotonic
    checkpoints = []
    course = replace(optimization_course(1, total_units=6, min_units=2, max_units=6),
        preferred_session_units=3,
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=7)))
    control = OptimizationSearchControl(deadline=monotonic() + 10,
        checkpoint=checkpoints.append, cancelled=lambda: bool(checkpoints))
    with pytest.raises(OptimizationCancelled):
        optimize_semester([course], [], generated_only=True, control=control, allow_unproven=True)
    assert [item.units for item in checkpoints[0].courses[0].sessions] == [3, 3]


@pytest.mark.parametrize('total', [25, 34])
def test_first_candidate_completes_preferred_size_remainder_without_one_unit_session(total):
    from app.services.semester_optimization import OptimizationSearchControl, OptimizationCancelled, monotonic
    checkpoints = []
    course = replace(optimization_course(1, total_units=total),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=70)))
    control = OptimizationSearchControl(deadline=monotonic() + 10,
        checkpoint=checkpoints.append, cancelled=lambda: bool(checkpoints))
    with pytest.raises(OptimizationCancelled):
        optimize_semester([course], [], generated_only=True, control=control, allow_unproven=True)
    first = checkpoints[0]
    assert first.total_units == total
    assert all(2 <= session.units <= 4 for session in first.courses[0].sessions)
    assert first.optimal is False
    assert first.objectives[0].proof_status == 'proven'
    assert first.unit_upper_bound == total


@pytest.mark.parametrize('total', [25, 34])
def test_completion_hint_preserves_proven_priorities_and_repeatability_with_native_fallback(monkeypatch, total):
    from app.services import semester_optimization as service
    course = replace(optimization_course(1, total_units=total),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=70)))
    first = optimize_semester([course], [], generated_only=True, allow_unproven=True, deadline_seconds=10)
    repeated = optimize_semester([course], [], generated_only=True, allow_unproven=True, deadline_seconds=10)
    assert first.optimal and first.total_units == total
    assert first.courses == repeated.courses
    monkeypatch.setattr(service, '_add_completion_hint', lambda *_args: None)
    native = optimize_semester([course], [], generated_only=True, allow_unproven=True, deadline_seconds=10)
    assert native.optimal
    assert [(e.objective_key, e.value) for e in first.objectives] == [(e.objective_key, e.value) for e in native.objectives]


def test_incomplete_completion_hint_never_excludes_better_native_assignment(monkeypatch):
    from app.services import semester_optimization as service
    courses = [replace(optimization_course(i, total_units=2, min_units=2, max_units=2,
        cohort_id=i, room_ids=rooms), planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
        windows=(TimeWindowPlan(i, 0, time(8), time(9, 40)),)) for i, rooms in ((1, (1, 2)), (2, (1,)))]
    courses.append(replace(optimization_course(3, total_units=7),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=7))))
    original = service._add_completion_hint
    seed_totals = []
    def capture(model, variables, control):
        original(model, variables, control)
        hints = dict(zip(model.proto.solution_hint.vars, model.proto.solution_hint.values))
        seed_totals.append(sum(c.units for v in variables.values() for c in v.candidate_set.candidates
                               if hints.get(v.temporal[c.candidate_id].index) == 1))
    monkeypatch.setattr(service, '_add_completion_hint', capture)
    result = optimize_semester(courses, [], generated_only=True, deadline_seconds=10)
    assert seed_totals == [9]  # Earliest room choice blocks the other course.
    assert result.optimal and result.total_units == 11
    assert result.courses[0].sessions[0].room_id == 2


@pytest.mark.parametrize('stop', ['deadline', 'cancel'])
def test_completion_hint_obeys_the_existing_control_before_native_solve(monkeypatch, stop):
    from app.services import semester_optimization as service
    from tests.optimization_fixtures import OptimizationClock
    clock = OptimizationClock()
    cancelled = False
    control = service.OptimizationSearchControl(deadline=1, clock=clock, cancelled=lambda: cancelled)
    original = service._add_completion_hint
    def stop_before_hint(model, variables, active_control):
        nonlocal cancelled
        if stop == 'deadline': clock.advance(1)
        else: cancelled = True
        original(model, variables, active_control)
    monkeypatch.setattr(service, '_add_completion_hint', stop_before_hint)
    def forbidden_solver(): pytest.fail('Expired or cancelled construction must not start native solve')
    monkeypatch.setattr(service.cp_model, 'CpSolver', forbidden_solver)
    expected = service.OptimalResultNotProven if stop == 'deadline' else service.OptimizationCancelled
    with pytest.raises(expected):
        optimize_semester([optimization_course(1, total_units=7)], [], generated_only=True, control=control)


def test_completion_first_candidate_handles_scarce_dates_and_joint_hard_constraints():
    from app.services.semester_optimization import OptimizationSearchControl, OptimizationCancelled, monotonic
    from app.services.conflict_aware_generation import validate_exact_candidate
    common = dict(cohort_id=1, lecturer_ids=(1,), room_ids=(1,))
    flexible = replace(optimization_course(1, total_units=7, **common),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=14)))
    scarce = replace(optimization_course(2, total_units=4, min_units=4, max_units=4, **common),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START))
    checkpoints = []
    control = OptimizationSearchControl(deadline=monotonic() + 10,
        checkpoint=checkpoints.append, cancelled=lambda: bool(checkpoints))
    with pytest.raises(OptimizationCancelled):
        optimize_semester([flexible, scarce], [], generated_only=True, allow_unproven=True, control=control)
    first = checkpoints[0]
    assert first.total_units == 11
    validate_exact_candidate((flexible, scarce), (), (), {}, first.courses)


def test_empty_completion_hint_uses_native_no_candidate_result(monkeypatch):
    from app.services import semester_optimization as service
    course = replace(optimization_course(1, total_units=7),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START))
    fixed = [FixedSession(99, 1, 1, 1, SEMESTER_START, time(8), time(12))]
    original = service._add_completion_hint
    hint_counts = []
    def capture(model, variables, control):
        original(model, variables, control)
        hint_counts.append(len(model.proto.solution_hint.vars))
    monkeypatch.setattr(service, '_add_completion_hint', capture)
    with pytest.raises(NoGeneratedAlternative):
        optimize_semester([course], fixed, generated_only=True, allow_unproven=True, deadline_seconds=10)
    assert hint_counts == [0]


@pytest.mark.parametrize('preferred,total,expected', [(2, 8, [2, 2, 2, 2]), (4, 8, [4, 4]), (3.5, 7, [3, 4])])
def test_shape_objective_uses_explicit_preference_and_half_unit_ties(preferred, total, expected):
    course = replace(optimization_course(1, total_units=total, min_units=2, max_units=5),
        preferred_session_units=preferred,
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=21)),
        windows=(TimeWindowPlan(1, 0, time(8), time(14)),))
    result = optimize_semester([course], [], generated_only=True, deadline_seconds=10)
    assert result.optimal and result.total_units == total
    assert sorted(item.units for item in result.courses[0].sessions) == expected


@pytest.mark.parametrize('minutes,required',[(360,(2,2,3)),(405,(2,2,2,2))])
def test_later_starts_fill_shared_cohort_window_with_sequential_courses(minutes,required):
    end=(datetime.combine(SEMESTER_START,time(8))+timedelta(minutes=minutes)).time()
    courses=[replace(optimization_course(i,total_units=units,min_units=units,max_units=units,
        cohort_id=1,lecturer_ids=(1,),room_ids=(1,)),
        planning_period=PlanningPeriodPlan(SEMESTER_START,SEMESTER_START),
        windows=(TimeWindowPlan(1,0,time(8),end),)) for i,units in enumerate(required,1)]
    result=optimize_semester(courses,[],generated_only=True,deadline_seconds=10)
    assert result.optimal and result.total_units==sum(required)
    sessions=sorted((s for c in result.courses for s in c.sessions),key=lambda s:s.start_time)
    assert all(left.end_time<=right.start_time for left,right in zip(sessions,sessions[1:]))


@pytest.mark.parametrize('blocked_by',['cohort','lecturer','room','recurring','dated'])
def test_later_start_respects_exact_fixed_and_availability_end_boundary(blocked_by):
    from app.models.planning import ResourceUnavailabilityPeriod,ResourceUnavailabilityWeekday
    course=replace(optimization_course(1,total_units=2,min_units=2,max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START,SEMESTER_START))
    boundary=time(9,7,30)
    fixed=[]
    if blocked_by in ('cohort','lecturer','room'):
        fixed=[FixedSession(99,1 if blocked_by=='cohort' else 99,
            1 if blocked_by=='lecturer' else 99,1 if blocked_by=='room' else 99,
            SEMESTER_START,time(8),boundary)]
    else:
        period=ResourceUnavailabilityPeriod(kind=blocked_by,start_time=time(8),end_time=boundary,
            start_date=SEMESTER_START,end_date=SEMESTER_START,
            weekdays=[ResourceUnavailabilityWeekday(weekday=0)] if blocked_by=='recurring' else [])
        course=replace(course,lecturers=(replace(course.lecturers[0],unavailable_periods=(period,)),))
    result=optimize_semester([course],fixed,generated_only=True,deadline_seconds=10)
    assert result.total_units==2
    assert result.courses[0].sessions[0].start_time==boundary


@pytest.mark.parametrize('ranges,blocked',[
    (((0,120),(15,150),(5,180)),(50,65)),
    (((7,110),(20,130),(0,90)),(45,70)),
    (((0,60),(10,75),(20,100)),(30,50)),
    (((0,180),(0,180),(0,180)),(45,60)),
])
def test_temporal_event_closure_matches_independent_minute_exhaustive_oracle(ranges,blocked):
    # Tiny exact oracle considers every minute, rather than using production candidates.
    duration=45
    best=(-1,float('inf'))
    def visit(index,chosen):
        nonlocal best
        if index==len(ranges):
            score=(len(chosen),sum(chosen))
            if score[0]>best[0] or (score[0]==best[0] and score[1]<best[1]):best=score
            return
        visit(index+1,chosen)
        begin,end=ranges[index]
        for start in range(begin,end-duration+1):
            if start<blocked[1] and blocked[0]<start+duration:continue
            if any(start<other+duration and other<start+duration for other in chosen):continue
            visit(index+1,(*chosen,start))
    visit(0,())
    at=lambda minutes:(datetime.combine(SEMESTER_START,time(8))+timedelta(minutes=minutes)).time()
    courses=[replace(optimization_course(i,total_units=1,min_units=1,max_units=1,cohort_id=1,
        lecturer_ids=(1,),room_ids=(1,)),planning_period=PlanningPeriodPlan(SEMESTER_START,SEMESTER_START),
        windows=(TimeWindowPlan(i,0,at(begin),at(end)),)) for i,(begin,end) in enumerate(ranges,1)]
    fixed=[FixedSession(99,1,1,1,SEMESTER_START,at(blocked[0]),at(blocked[1]))]
    if best[0]==0:
        with pytest.raises(NoGeneratedAlternative):optimize_semester(courses,fixed,generated_only=True)
    else:
        result=optimize_semester(courses,fixed,generated_only=True,deadline_seconds=10)
        starts=[s.start_time.hour*60+s.start_time.minute-8*60 for c in result.courses for s in c.sessions]
        assert (result.total_units,sum(starts))==best


def test_shared_deadline_stops_candidate_enumeration_before_solver(monkeypatch):
    from app.services import semester_optimization as service
    from tests.optimization_fixtures import OptimizationClock
    clock = OptimizationClock()
    control = service.OptimizationSearchControl(deadline=2, clock=clock)
    original = service._candidate_resources
    calls = []
    def consume_time(*args, **kwargs):
        calls.append(1)
        clock.advance(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(service, "_candidate_resources", consume_time)
    with pytest.raises(service.OptimalResultNotProven):
        service.optimize_semester([optimization_course(1)], [], control=control)
    assert 0 < len(calls) <= 2


def test_registered_cancellation_prevents_model_build_and_solve(monkeypatch):
    from app.services import semester_optimization as service
    control = service.OptimizationSearchControl(deadline=float('inf'), cancelled=lambda: True)
    def forbidden():
        pytest.fail("Cancellation must be checked before model creation")
    monkeypatch.setattr(service.cp_model, "CpModel", forbidden)
    with pytest.raises(service.OptimizationCancelled):
        service.optimize_semester([optimization_course(1)], [], control=control)


def test_native_search_is_stopped_when_cancellation_registers(monkeypatch):
    from threading import Event
    from app.services import semester_optimization as service
    cancelled = Event()
    stopped = Event()
    class ControlledSolver:
        def __init__(self):
            from types import SimpleNamespace
            self.parameters = SimpleNamespace()
        def solve(self, model):
            cancelled.set()
            assert stopped.wait(2), "Native solve was not interrupted"
            return service.cp_model.UNKNOWN
        def stop_search(self):
            stopped.set()
    monkeypatch.setattr(service.cp_model, "CpSolver", ControlledSolver)
    control = service.OptimizationSearchControl(
        deadline=service.monotonic() + 30, cancelled=cancelled.is_set,
    )
    with pytest.raises(service.OptimizationCancelled):
        service.optimize_semester([optimization_course(1)], [], control=control)
    assert stopped.is_set()


def solver_statuses(monkeypatch, statuses):
    from app.services import semester_optimization as service
    original = service.cp_model.CpSolver
    remaining = iter(statuses)
    calls = []
    class ControlledStatusSolver:
        def __init__(self):
            self.real=original()
            self.parameters=self.real.parameters
            self.reported=None
        def solve(self, model, callback=None):
            self.reported=next(remaining)
            calls.append(self.reported)
            if self.reported in (service.cp_model.UNKNOWN, service.cp_model.MODEL_INVALID): return self.reported
            self.real.solve(model, callback)
            return self.reported
        def value(self, variable):
            assert self.reported != service.cp_model.UNKNOWN, 'UNKNOWN is not an assignment'
            return self.real.value(variable)
        @property
        def objective_value(self): return self.real.objective_value
        @property
        def best_objective_bound(self): return self.real.best_objective_bound
        def stop_search(self): self.real.stop_search()
    monkeypatch.setattr(service.cp_model,'CpSolver',ControlledStatusSolver)
    return calls


def test_feasible_candidate_is_retained_without_later_search_or_fabricated_proof(monkeypatch):
    from app.services import semester_optimization as service
    calls=solver_statuses(monkeypatch,[service.cp_model.FEASIBLE])
    from dataclasses import replace
    from app.services.schedule_generation import PlanningPeriodPlan
    course = optimization_course(1,total_units=4,min_units=2,max_units=2)
    course = replace(course, planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START))
    result=optimize_semester([course],[],generated_only=True,allow_unproven=True)
    assert result.total_units == 2 and not result.optimal
    assert [o.proof_status for o in result.objectives] == ['unfinished']+['not_attempted']*9
    assert calls == [service.cp_model.FEASIBLE]


def test_full_required_coverage_proves_first_stage_even_with_feasible_status(monkeypatch):
    from app.services import semester_optimization as service
    calls=solver_statuses(monkeypatch,[service.cp_model.FEASIBLE, service.cp_model.UNKNOWN])
    result=optimize_semester([optimization_course(1,total_units=2)],[],generated_only=True,allow_unproven=True)
    assert result.objectives[0].proof_status == 'proven'
    assert result.objectives[4].proof_status == 'unfinished'
    assert calls == [service.cp_model.FEASIBLE, service.cp_model.UNKNOWN]


def test_later_unknown_preserves_earlier_exact_candidate_with_its_evidence(monkeypatch):
    from app.services import semester_optimization as service
    calls=solver_statuses(monkeypatch,[service.cp_model.OPTIMAL,service.cp_model.UNKNOWN])
    checkpoints=[]
    control=service.OptimizationSearchControl(deadline=service.monotonic()+30,checkpoint=checkpoints.append)
    result=optimize_semester([optimization_course(1,total_units=2)],[],generated_only=True,control=control,allow_unproven=True)
    assert not result.optimal and result.total_units == 2
    assert result.objectives[0].proof_status == 'proven'
    assert [o.proof_status for o in result.objectives[1:4]] == ['proven','proven','proven']
    assert result.objectives[4].objective_key == 'schedule_shape'
    assert result.objectives[4].proof_status == 'unfinished'
    assert result.unit_upper_bound == 2
    assert checkpoints and checkpoints[-1].courses == result.courses
    assert calls == [service.cp_model.OPTIMAL,service.cp_model.UNKNOWN]


def test_unknown_without_assignment_is_not_decoded(monkeypatch):
    from app.services import semester_optimization as service
    solver_statuses(monkeypatch,[service.cp_model.UNKNOWN])
    with pytest.raises(service.OptimalResultNotProven):
        optimize_semester([optimization_course(1)],[],generated_only=True)


@pytest.mark.parametrize('bound,objective,same_problem,expected', [
    (90,'total_units',True,90), (90.2,'total_units',True,91),
    (120,'total_units',True,100), (79,'total_units',True,None),
    (float('inf'),'total_units',True,None), (float('nan'),'total_units',True,None),
    (90,'conflicts',True,None), (90,'total_units',False,None),
    (None,'total_units',True,None), (True,'total_units',True,None),
])
def test_coverage_bound_requires_finite_matching_coverage_evidence(bound,objective,same_problem,expected):
    from app.services.semester_optimization import valid_unit_upper_bound
    assert valid_unit_upper_bound(80,100,bound,objective_key=objective,same_problem=same_problem) == expected


def test_candidate_generation_obeys_unavailable_dates_sizes_windows_and_resource_eligibility():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=3),
        planning_period=PlanningPeriodPlan(SEMESTER_START, date(2026, 9, 14)),
    )
    candidates = generate_candidates(course, [], frozenset({SEMESTER_START}))

    assert candidates.candidates
    assert {item.date for item in candidates.candidates} == {date(2026, 9, 14)}
    assert {item.units for item in candidates.candidates} == {2, 3}
    assert all(item.lecturer_ids == (1,) and item.room_ids == (1,) for item in candidates.candidates)
    assert any(item.code == "UNAVAILABLE_DATE" for item in candidates.evidence)


def test_candidate_generation_excludes_named_holiday_and_keeps_it_distinct_from_caller_unavailability():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, date(2026, 9, 14)),
    )
    holiday = HolidayReference(1, SEMESTER_START, "Founders Day", 1)

    candidates = generate_candidates(
        course,
        [],
        frozenset({SEMESTER_START}),
        {SEMESTER_START: holiday},
    )

    assert {item.date for item in candidates.candidates} == {date(2026, 9, 14)}
    evidence = next(item for item in candidates.evidence if item.code == "INSTITUTION_HOLIDAY")
    assert evidence.holiday_date == SEMESTER_START
    assert evidence.holiday_name == "Founders Day"
    assert not any(item.code == "UNAVAILABLE_DATE" for item in candidates.evidence)


def test_holiday_without_an_otherwise_feasible_candidate_is_not_reported():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
        windows=(TimeWindowPlan(1, 0, time(8), time(8, 30)),),
    )
    holiday = HolidayReference(1, SEMESTER_START, "Founders Day", 1)

    candidates = generate_candidates(course, [], frozenset(), {SEMESTER_START: holiday})

    assert not candidates.candidates
    assert not any(item.code == "INSTITUTION_HOLIDAY" for item in candidates.evidence)


def test_global_optimization_beats_request_order_and_allows_zero_without_fairness():
    one_day = PlanningPeriodPlan(SEMESTER_START, SEMESTER_START)
    shared = {
        "lecturers": (ResourceCandidatePlan(1, "LEC-001"),),
        "rooms": (ResourceCandidatePlan(1, "ROOM-001", capacity=40),),
        "windows": (TimeWindowPlan(1, 0, time(8), time(12)),),
        "planning_period": one_day,
    }
    small = replace(optimization_course(1, total_units=2, min_units=2, max_units=2), **shared)
    large = replace(optimization_course(2, total_units=4, min_units=4, max_units=4), **shared)

    result = optimize_semester([small, large], [], deadline_seconds=10)

    assert result.total_units == 4
    by_course = {item.course_id: item.scheduled_units for item in result.courses}
    assert by_course == {1: 0, 2: 4}


def test_resource_assignment_is_conflict_free_contiguous_and_deterministic():
    course = replace(
        optimization_course(1, total_units=8),
        lecturers=(ResourceCandidatePlan(2, "LEC-002"), ResourceCandidatePlan(1, "LEC-001")),
        rooms=(ResourceCandidatePlan(2, "ROOM-002", capacity=40), ResourceCandidatePlan(1, "ROOM-001", capacity=40)),
    )
    signatures = []
    for _ in range(20):
        result = optimize_semester([course], [], deadline_seconds=10)
        sessions = result.courses[0].sessions
        signatures.append(tuple((item.date, item.units, item.lecturer_id, item.room_id) for item in sessions))
        assert result.lecturer_changes == 0
        assert result.room_changes == 0
    assert len(set(signatures)) == 1
    assert {item[2] for item in signatures[0]} == {1}
    assert {item[3] for item in signatures[0]} == {1}


def test_partial_result_uses_valid_session_sizes_and_reports_competition():
    course = replace(
        optimization_course(1, total_units=5, min_units=2, max_units=3),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
    )
    result = optimize_semester([course], [], deadline_seconds=10)
    assert result.total_units == 3
    assert [item.units for item in result.courses[0].sessions] == [3]
    assert {item.code for item in result.courses[0].evidence} >= {"COURSE_CONSTRAINT"}


def test_over_scheduled_baseline_is_preserved_and_equal_legacy_size_is_improved():
    current = CurrentSession(1, 1, 1, 1, SEMESTER_START, time(8), time(12), 6, 1, 0)
    over_scheduled = replace(optimization_course(1, total_units=4), current_sessions=(current,))
    result = optimize_semester([over_scheduled], [], deadline_seconds=10)
    assert result.total_units == 6
    assert result.courses[0].retained_current is True

    equal_current = replace(over_scheduled, total_units=6)
    equal = optimize_semester([equal_current], [], deadline_seconds=10)
    assert equal.total_units == 6
    assert equal.courses[0].retained_current is False
    assert [item.units for item in equal.courses[0].sessions] == [3, 3]


def test_current_draft_outside_active_course_dates_is_replaced():
    current = CurrentSession(1, 1, 1, 1, SEMESTER_START, time(8), time(11, 30), 4, 1, 0)
    valid_date = date(2026, 9, 14)
    course = replace(
        optimization_course(1, total_units=4, min_units=4, max_units=4),
        planning_period=PlanningPeriodPlan(valid_date, valid_date),
        current_sessions=(current,),
    )

    result = optimize_semester([course], [], deadline_seconds=10)

    optimized = result.courses[0]
    assert optimized.retained_current is False
    assert [(item.date, item.start_time, item.units) for item in optimized.sessions] == [
        (valid_date, time(8), 4)
    ]


def test_current_draft_outside_active_cohort_calendar_window_is_replaced():
    current = CurrentSession(1, 1, 1, 1, SEMESTER_START, time(8), time(11, 30), 4, 1, 0)
    course = replace(
        optimization_course(1, total_units=4, min_units=4, max_units=4),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
        windows=(TimeWindowPlan(2, 0, time(13), time(16, 30)),),
        current_sessions=(current,),
    )

    result = optimize_semester([course], [], deadline_seconds=10)

    optimized = result.courses[0]
    assert optimized.retained_current is False
    assert [(item.date, item.start_time, item.units) for item in optimized.sessions] == [
        (SEMESTER_START, time(13), 4)
    ]


def test_equal_unit_current_conflicts_are_replaced_before_preservation_tier():
    current_one = CurrentSession(1, 1, 1, 1, SEMESTER_START, time(8), time(10), 2, 1, 0)
    current_two = CurrentSession(2, 1, 1, 1, SEMESTER_START, time(8), time(10), 2, 1, 0)
    first = replace(optimization_course(1, total_units=2, min_units=2, max_units=2), current_sessions=(current_one,))
    second = replace(optimization_course(2, total_units=2, min_units=2, max_units=2, cohort_id=1, lecturer_ids=(1,), room_ids=(1,)), current_sessions=(current_two,))
    result = optimize_semester([first, second], [], deadline_seconds=10)
    assert result.total_units == 4
    assert result.conflicts == 0
    assert not all(item.retained_current for item in result.courses)


def test_resource_occupancy_does_not_report_missing_date_or_window():
    course = replace(
        optimization_course(1, total_units=4),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
    )
    fixed = FixedSession(99, 99, 1, 1, SEMESTER_START, time(8), time(12))

    evidence = generate_candidates(course, [fixed], frozenset()).evidence
    codes = {item.code for item in evidence}

    assert codes >= {"LECTURER_OCCUPIED", "ROOM_OCCUPIED"}
    assert "NO_ALLOWED_DATE_OR_WINDOW" not in codes


def test_once_per_week_precedes_midpoint_size_adjustment_when_needed():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=4),
        planning_period=PlanningPeriodPlan(SEMESTER_START, date(2026, 9, 14)),
        windows=(
            TimeWindowPlan(1, 0, time(8), time(10)),
            TimeWindowPlan(2, 2, time(8), time(12)),
        ),
    )

    result = optimize_semester([course], [], deadline_seconds=10)

    assert [(item.date, item.units) for item in result.courses[0].sessions] == [
        (date(2026, 9, 9), 4),
    ]


def test_midpoint_session_size_is_preferred_and_sessions_are_once_per_week():
    course = replace(
        optimization_course(1, total_units=28, min_units=2, max_units=4),
        windows=(
            TimeWindowPlan(1, 0, time(8), time(12)),
            TimeWindowPlan(2, 1, time(8), time(12)),
            TimeWindowPlan(3, 2, time(8), time(12)),
        ),
    )

    result = optimize_semester([course], [], deadline_seconds=10)
    sessions = result.courses[0].sessions

    assert len(sessions) == 9
    assert sorted(item.units for item in sessions) == [3] * 8 + [4]
    assert len({item.date - timedelta(days=item.date.weekday()) for item in sessions}) == 9


def test_fixed_session_size_uses_one_session_per_week_when_enough_weeks_exist():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, date(2026, 9, 14)),
        windows=(
            TimeWindowPlan(1, 0, time(8), time(10)),
            TimeWindowPlan(2, 2, time(8), time(10)),
        ),
    )

    result = optimize_semester([course], [], deadline_seconds=10)

    assert [(item.date, item.units) for item in result.courses[0].sessions] == [
        (date(2026, 9, 7), 2),
        (date(2026, 9, 14), 2),
    ]


def test_additional_sessions_are_balanced_across_weeks_only_as_fallback():
    course = replace(
        optimization_course(1, total_units=10, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, date(2026, 9, 20)),
        windows=(
            TimeWindowPlan(1, 0, time(8), time(10)),
            TimeWindowPlan(2, 2, time(8), time(10)),
            TimeWindowPlan(3, 4, time(8), time(10)),
        ),
    )

    result = optimize_semester([course], [], deadline_seconds=10)
    sessions = result.courses[0].sessions
    sessions_per_week = Counter(
        item.date - timedelta(days=item.date.weekday()) for item in sessions
    )

    assert len(sessions) == 5
    assert sorted(sessions_per_week.values()) == [2, 3]
    assert len({item.date for item in sessions}) == 5


def test_active_exam_is_fixed_occupancy_with_source_evidence_and_half_open_boundaries():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=3),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
    )
    exam = FixedSession(
        99,
        1,
        1,
        1,
        SEMESTER_START,
        time(9, 40),
        time(12),
        source_kind="active_exam",
        source_id=77,
    )

    candidates = generate_candidates(course, [exam], frozenset())

    assert [(item.units, item.end_time) for item in candidates.candidates] == [
        (2, time(9, 40))
    ]
    sourced = {
        (item.code, item.source_kind, item.source_id)
        for item in candidates.evidence
    }
    assert sourced >= {
        ("LECTURER_OCCUPIED", "active_exam", 77),
        ("ROOM_OCCUPIED", "active_exam", 77),
        ("COHORT_OCCUPIED", "active_exam", 77),
    }


def test_same_course_exam_deadline_allows_exact_end_and_reports_later_candidates():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=3),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
        latest_teaching_end=datetime.combine(SEMESTER_START, time(9, 40)),
        latest_teaching_source_id=88,
    )

    candidates = generate_candidates(course, [], frozenset())
    result = optimize_semester([course], [], deadline_seconds=10)

    assert [(item.units, item.end_time) for item in candidates.candidates] == [
        (2, time(9, 40))
    ]
    boundary = next(item for item in candidates.evidence if item.code == "ACTIVE_EXAM_BOUNDARY")
    assert (boundary.source_kind, boundary.source_id) == ("active_exam", 88)
    assert result.total_units == 2
    assert result.courses[0].sessions[0].end_time == time(9, 40)


def test_too_short_cohort_calendar_windows_are_reported_precisely():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=2),
        windows=(TimeWindowPlan(1, 0, time(8), time(9)),),
    )

    candidates = generate_candidates(course, [], frozenset())

    assert candidates.candidates == ()
    assert {item.code for item in candidates.evidence} == {
        "COHORT_CALENDAR_WINDOW_UNAVAILABLE"
    }


def test_generated_only_mode_never_retains_current_or_enforces_its_unit_floor():
    current = CurrentSession(
        1, 1, 1, 1, SEMESTER_START, time(8), time(11, 30), 4, 1, 0
    )
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
        windows=(TimeWindowPlan(1, 0, time(8), time(10)),),
        current_sessions=(current,),
    )

    result = optimize_semester(
        [course], [], deadline_seconds=10, generated_only=True
    )

    assert result.total_units == 2
    assert result.courses[0].retained_current is False
    assert [item.units for item in result.courses[0].sessions] == [2]


def test_generated_only_mode_allows_zero_for_one_course_in_nonempty_joint_result():
    blocked = replace(
        optimization_course(1, total_units=2, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
    )
    available = replace(
        optimization_course(2, total_units=2, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
    )
    fixed = FixedSession(99, 1, 1, 1, SEMESTER_START, time(8), time(12))

    result = optimize_semester(
        [blocked, available], [fixed], deadline_seconds=10, generated_only=True
    )

    by_course = {item.course_id: item for item in result.courses}
    assert by_course[1].scheduled_units == 0
    assert by_course[2].scheduled_units == 2


def test_generated_only_mode_rejects_an_all_zero_joint_result():
    course = replace(
        optimization_course(1, total_units=2, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START),
    )
    fixed = FixedSession(99, 1, 1, 1, SEMESTER_START, time(8), time(12))

    with pytest.raises(NoGeneratedAlternative):
        optimize_semester(
            [course], [fixed], deadline_seconds=10, generated_only=True
        )
