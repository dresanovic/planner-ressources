"""Independent exact-accounting and small feasible-alternative I-009 oracles."""
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from fractions import Fraction
from itertools import product

import pytest

from app.services.schedule_generation import TimeWindowPlan, PlanningPeriodPlan
from app.services.semester_optimization import optimize_semester, FixedSession
from tests.optimization_fixtures import optimization_course

MONDAY = date(2026,9,7)
LE = 2_700_000_000


def window(day, start=time(9), end=time(12,20), marked=True, identifier=1):
    return TimeWindowPlan(identifier,None,start,end,kind='dated',date=day,is_intensive=marked)


def unmarked_window(start,end):
    # Independent dated availability keeps marker-accounting scenarios distinct
    # from the weekly-window replacement rule tested in dated_intensive_windows.
    return window(MONDAY,start,end,marked=False,identifier=1)


def course(identifier=1, *, windows=None, total=2, minimum=1, maximum=2, cohort=1):
    windows = windows or (window(MONDAY),window(MONDAY+timedelta(days=1),identifier=2))
    return replace(optimization_course(identifier,total_units=total,min_units=minimum,max_units=maximum,
        cohort_id=cohort,lecturer_ids=(identifier,),room_ids=(identifier,)),windows=windows,
        planning_period=PlanningPeriodPlan(MONDAY,MONDAY+timedelta(days=8)))


def independent_minutes(start, units, markers):
    """Minute-cell enumeration independent of production interval/union helpers."""
    return sum(any(a <= start + offset < b for a,b in markers)
        for unit in range(units) for minute in range(45)
        for offset in (unit*55+minute,))


@pytest.mark.parametrize('resource_kind', ['lecturer', 'room'])
@pytest.mark.parametrize('period_kind', ['recurring', 'dated'])
@pytest.mark.parametrize('marker_start,marker_end,unavailable_start,expected_start,expected_minutes', [
    (time(10), time(10, 40), time(10, 15), time(9, 30), 15),
    (time(11, 20), time(11, 55), time(11, 50), time(11, 5), 30),
])
def test_intensive_optimum_immediately_before_resource_unavailability(
        resource_kind, period_kind, marker_start, marker_end, unavailable_start, expected_start, expected_minutes):
    from app.models.planning import ResourceUnavailabilityPeriod, ResourceUnavailabilityWeekday

    windows = (unmarked_window( time(9), time(12)),
               window(MONDAY, marker_start, marker_end, identifier=2))
    value = replace(course(windows=windows, total=1, minimum=1, maximum=1),
                    planning_period=PlanningPeriodPlan(MONDAY, MONDAY))
    period = ResourceUnavailabilityPeriod(kind=period_kind, start_time=unavailable_start, end_time=time(12),
        weekdays=[ResourceUnavailabilityWeekday(weekday=0)] if period_kind == 'recurring' else [],
        start_date=MONDAY if period_kind == 'dated' else None,
        end_date=MONDAY + timedelta(days=1) if period_kind == 'dated' else None)
    field = 'lecturers' if resource_kind == 'lecturer' else 'rooms'
    value = replace(value, **{field: (replace(getattr(value, field)[0], unavailable_periods=(period,)),)})
    # Independently enumerate every feasible minute start before unavailability.
    # Include boundaries beyond the latest session start: they still seed ends.
    offset = lambda clock: clock.hour * 60 + clock.minute - 9 * 60
    expected = max((independent_minutes(start, 1, [(offset(marker_start), offset(marker_end))]), start)
                   for start in range(offset(unavailable_start) - 45 + 1))
    assert expected == (expected_minutes, offset(expected_start))
    result = optimize_semester([value], [], generated_only=True, deadline_seconds=10)
    assert result.optimal and result.total_units == 1
    assert Fraction(result.intensive_teaching_time, 60_000_000) == expected[0]
    assert result.courses[0].sessions[0].start_time == expected_start


@pytest.mark.parametrize('markers,expected', [
    ([(time(9),time(10,40)),(time(9,30),time(10,40))],Fraction(2)),
    ([(time(9,30),time(10,10))],Fraction(2,3)),
    ([(time(9,45),time(9,55))],Fraction(0)),
    ([(time(10,40),time(11))],Fraction(0)),
    ([(time(8),time(9))],Fraction(0)),
])
def test_instructional_union_is_exact_and_excludes_breaks_endpoints(markers, expected):
    from app.services.schedule_generation import intensive_instruction_ticks
    windows = tuple(window(MONDAY,a,b,identifier=i+1) for i,(a,b) in enumerate(markers))
    assert Fraction(intensive_instruction_ticks(MONDAY,time(9),time(10,40),2,windows),LE) == expected


def test_microsecond_overlap_is_not_rounded_and_wrong_dates_do_not_score():
    from app.services.schedule_generation import intensive_instruction_ticks
    windows = (window(MONDAY,time(9,44,59,999999),time(9,45)),)
    assert intensive_instruction_ticks(MONDAY,time(9),time(9,45),1,windows) == 1
    assert intensive_instruction_ticks(MONDAY+timedelta(days=7),time(9),time(9,45),1,windows) == 0


def test_variety_beats_weekly_and_size_preferences_with_independent_assignment_oracle():
    courses = [course(1),course(2)]
    # Enumerate all per-course LE splits across two dates independently of CP-SAT.
    choices = [(a,b) for a,b in product(range(3),repeat=2) if a+b <= 2]
    alternatives = []
    for one,two in product(choices,repeat=2):
        if any(sum(45*u+10*max(0,u-1) for u in (one[d],two[d])) > 200 for d in range(2)):
            continue
        total = sum(one)+sum(two)
        variety = sum(max(0,int(one[d]>0)+int(two[d]>0)-1) for d in range(2))
        alternatives.append((total,total,variety))
    expected = max(alternatives)
    result = optimize_semester(courses,[],generated_only=True,deadline_seconds=10)
    observed = [(item.course_id,s.date,s.units) for item in result.courses for s in item.sessions]
    counts = {day:len({c for c,d,_ in observed if d==day}) for day in {d for _,d,_ in observed}}
    assert (result.total_units, Fraction(result.intensive_teaching_time,LE),sum(max(0,k-1) for k in counts.values())) == expected == (4,4,2)
    assert len(observed) == 4  # Both LVs on both days, despite once-per-week cost.


def test_total_coverage_cannot_be_sacrificed_for_intensive_or_variety():
    windows = (window(MONDAY,end=time(10,40)),window(MONDAY+timedelta(days=1),end=time(13),marked=False,identifier=2))
    result = optimize_semester([course(windows=windows,total=4,minimum=2,maximum=4)],[],generated_only=True,deadline_seconds=10)
    assert result.total_units == 4
    assert result.intensive_teaching_time == 2*LE


def test_intensive_time_outranks_weekly_shape_without_compelling_full_lv_placement():
    windows = (window(MONDAY),window(MONDAY+timedelta(days=1),identifier=2),window(MONDAY+timedelta(days=7),marked=False,identifier=3))
    result = optimize_semester([course(windows=windows,total=4,minimum=2,maximum=2)],[],generated_only=True,deadline_seconds=10)
    assert result.total_units == 4 and result.intensive_teaching_time == 4*LE
    assert {s.date for s in result.courses[0].sessions} == {MONDAY,MONDAY+timedelta(days=1)}


def test_candidate_closure_includes_instruction_boundary_alignment_inside_wider_permission():
    windows = (unmarked_window(time(8),time(13)),window(MONDAY,time(10,7),time(10,52),identifier=2))
    value = course(windows=windows,total=2,minimum=2,maximum=2)
    result = optimize_semester([value],[],generated_only=True,deadline_seconds=10)
    # Enumerating each minute proves 09:12 is the first full 45-minute overlap.
    markers = [(127,172)] # Minutes since 08:00, independent of the production helper.
    best = max((independent_minutes(start,2,markers),-start) for start in range(201))
    assert best == (45,-72)
    session = result.courses[0].sessions[0]
    assert session.start_time == time(9,12)
    assert result.intensive_teaching_time == LE
    assert session.time_window_id == 1 # Marked source is too short for two LE.


@pytest.mark.parametrize('fixed_cohort,source_kind,expected_day,expected_variety', [
    (1,'teaching_session',MONDAY,1),
    (2,'teaching_session',MONDAY,0),
    (1,'active_exam',MONDAY+timedelta(days=1),0),
])
def test_fixed_teaching_contributes_unique_lv_presence_but_not_coverage(fixed_cohort,source_kind,expected_day,expected_variety):
    fixed = FixedSession(99,fixed_cohort,99,99,MONDAY,time(8),time(8,45),source_kind=source_kind,
        units=1,cohort_calendar_id=2,marked_windows=(window(MONDAY,time(8),time(9)),))
    value = course(total=1,minimum=1,maximum=1)
    result = optimize_semester([value],[fixed],generated_only=True,deadline_seconds=10)
    assert result.total_units == 1
    assert result.daily_variety == expected_variety
    assert result.courses[0].sessions[0].date == expected_day


def test_no_marker_preserves_the_same_arrangement_and_lower_objective_values():
    value = course(windows=(unmarked_window(time(9),time(12)),),total=2,minimum=2,maximum=2)
    result = optimize_semester([value],[],generated_only=True,deadline_seconds=10)
    assert result.courses[0].sessions[0].start_time == time(9)
    assert (result.intensive_teaching_time,result.daily_variety) == (0,0)
    assert [e.objective_key for e in result.objectives][:3] == ['total_units','intensive_teaching_time','daily_variety']


@pytest.mark.parametrize('slack,marker_start,marker_end',[(4,1,3),(6,2,5),(3,0,2),(4,1,2)])
def test_exhaustive_microsecond_shared_packing_oracle(slack,marker_start,marker_end):
    # Two45-minute sessions in90minutes+slack ticks. Every feasible full packing
    # is one of two LV orders, a leading gap0..slack and internal gap0..remaining.
    # This exhausts the actual integer-microsecond clock, not production seeds.
    duration=45*60*1_000_000
    alternatives=[]
    for order in ((1,2),(2,1)):
        for leading in range(slack+1):
            for gap in range(slack-leading+1):
                starts=(leading,leading+duration+gap)
                overlaps=[max(0,min(start+duration,duration+marker_end)-max(start,duration+marker_start)) for start in starts]
                score=(2,sum(overlaps),max(0,sum(value>0 for value in overlaps)-1))
                alternatives.append((score,dict(zip(order,starts))))
    optimum=max(score for score,_ in alternatives)
    origin=datetime.combine(MONDAY,time(9))
    at=lambda tick:(origin+timedelta(microseconds=tick)).time()
    windows=(unmarked_window(time(9),at(2*duration+slack)),window(MONDAY,at(duration+marker_start),at(duration+marker_end),identifier=2))
    courses=[replace(course(i,windows=windows,total=1,minimum=1,maximum=1),
        lecturers=course(1).lecturers,rooms=course(1).rooms) for i in (1,2)]
    result=optimize_semester(courses,[],generated_only=True,deadline_seconds=10)
    actual=(result.total_units,result.intensive_teaching_time,result.daily_variety)
    observed={c.course_id:int((datetime.combine(MONDAY,c.sessions[0].start_time)-origin)/timedelta(microseconds=1)) for c in result.courses}
    assert actual == optimum
    assert any(score==optimum and positions==observed for score,positions in alternatives)
    assert result.daily_variety == (0 if marker_end-marker_start==1 else 1)


def test_exhaustive_variety_cannot_sacrifice_intensive_time_at_equal_total():
    day2=MONDAY+timedelta(days=1)
    windows=(window(MONDAY),window(day2,marked=False,identifier=2),window(day2,time(9,10),time(9,20),identifier=3))
    fixed=FixedSession(99,1,99,99,day2,time(8),time(8,45),units=1,marked_windows=(window(day2,time(8),time(9)),))
    # All feasible minute starts on each day independently scored; fixedLV makes
    # day2's variety1, but its10intensive minutes cannot defeat45 on day1.
    oracle=max((1,independent_minutes(start,1,[(0,200)] if day==0 else [(10,20)]),int(day==1 and independent_minutes(start,1,[(10,20)])>0))
               for day in (0,1) for start in range(156))
    result=optimize_semester([course(windows=windows,total=1,minimum=1,maximum=1)],[fixed],generated_only=True,deadline_seconds=10)
    assert (result.total_units,Fraction(result.intensive_teaching_time,60_000_000),result.daily_variety) == oracle == (1,45,0)
