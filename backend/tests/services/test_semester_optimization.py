from dataclasses import replace
from datetime import date, datetime, time

from app.services.schedule_generation import PlanningPeriodPlan, ResourceCandidatePlan, TimeWindowPlan
from app.services.holiday_calendar import HolidayReference
import pytest

from app.services.semester_optimization import CurrentSession, FixedSession, NoGeneratedAlternative, generate_candidates, optimize_semester
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


def test_current_draft_outside_active_study_type_window_is_replaced():
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


def test_too_short_study_type_windows_are_reported_precisely():
    course = replace(
        optimization_course(1, total_units=4, min_units=2, max_units=2),
        windows=(TimeWindowPlan(1, 0, time(8), time(9)),),
    )

    candidates = generate_candidates(course, [], frozenset())

    assert candidates.candidates == ()
    assert {item.code for item in candidates.evidence} == {
        "STUDY_TYPE_WINDOW_UNAVAILABLE"
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
