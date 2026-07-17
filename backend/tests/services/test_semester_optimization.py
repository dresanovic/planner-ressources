from dataclasses import replace
from datetime import date, time

from app.services.schedule_generation import PlanningPeriodPlan, ResourceCandidatePlan, TimeWindowPlan
from app.services.semester_optimization import CurrentSession, FixedSession, generate_candidates, optimize_semester
from tests.optimization_fixtures import SEMESTER_START, optimization_course


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


def test_actual_over_scheduled_baseline_and_equal_current_draft_are_preserved_whole():
    current = CurrentSession(1, 1, 1, 1, SEMESTER_START, time(8), time(12), 6, 1, 0)
    over_scheduled = replace(optimization_course(1, total_units=4), current_sessions=(current,))
    result = optimize_semester([over_scheduled], [], deadline_seconds=10)
    assert result.total_units == 6
    assert result.courses[0].retained_current is True

    equal_current = replace(over_scheduled, total_units=6)
    equal = optimize_semester([equal_current], [], deadline_seconds=10)
    assert equal.total_units == 6
    assert equal.courses[0].retained_current is True


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


def test_canonical_tie_break_prefers_earlier_session_sequence():
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
        (date(2026, 9, 7), 2),
        (date(2026, 9, 9), 2),
    ]
