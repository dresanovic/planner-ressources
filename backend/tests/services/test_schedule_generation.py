from datetime import date, time

from app.schemas.draft_schedule import FailureCode
from app.services.schedule_generation import (
    CoursePlan,
    PlanningPeriodPlan,
    ResourceCandidatePlan,
    SemesterPlan,
    TimeWindowPlan,
    distribute_units,
    generate_schedule,
    session_duration_minutes,
)
from app.models.planning import ResourceUnavailabilityPeriod, ResourceUnavailabilityWeekday
from app.services.holiday_calendar import HolidayReference


def make_course(**overrides) -> CoursePlan:
    values = {
        "id": 1,
        "total_units": 20,
        "min_session_units": 2,
        "max_session_units": 4,
        "lecturer_id": 1,
        "cohort_id": 1,
        "room_id": 1,
        "study_type_id": 1,
        "cohort_size": 30,
        "room_capacity": 40,
    }
    values.update(overrides)
    return CoursePlan(**values)


def make_semester(start: date = date(2026, 9, 7), end: date = date(2026, 12, 20)):
    return SemesterPlan(id=1, start_date=start, end_date=end)


def make_period(start: date = date(2026, 9, 7), end: date = date(2026, 12, 20)):
    return PlanningPeriodPlan(start_date=start, end_date=end)


def make_windows() -> list[TimeWindowPlan]:
    return [
        TimeWindowPlan(id=1, weekday=0, start_time=time(8, 0), end_time=time(12, 0)),
        TimeWindowPlan(id=2, weekday=2, start_time=time(8, 0), end_time=time(12, 0)),
    ]


def test_distributes_20_units_into_five_four_unit_sessions():
    assert distribute_units(total_units=20, min_units=2, max_units=4) == [4, 4, 4, 4, 4]


def test_adjusts_final_below_minimum_remainder():
    assert distribute_units(total_units=18, min_units=3, max_units=4) == [4, 4, 4, 3, 3]


def test_session_duration_includes_breaks_between_units():
    assert session_duration_minutes(1) == 45
    assert session_duration_minutes(2) == 100
    assert session_duration_minutes(4) == 210


def test_generates_weekly_sessions_with_expected_end_times_and_units():
    result = generate_schedule(
        course=make_course(),
        semester=make_semester(),
        planning_period=make_period(),
        time_windows=make_windows(),
    )

    assert result.ok
    assert [session.units for session in result.sessions] == [4, 4, 4, 4, 4]
    assert sum(session.units for session in result.sessions) == 20
    assert {session.start_time for session in result.sessions} == {time(8, 0)}
    assert {session.end_time for session in result.sessions} == {time(11, 30)}
    assert [session.date for session in result.sessions] == [
        date(2026, 9, 7),
        date(2026, 9, 14),
        date(2026, 9, 21),
        date(2026, 9, 28),
        date(2026, 10, 5),
    ]


def test_holidays_are_hard_constraints_and_named_when_they_remove_feasibility():
    holiday = HolidayReference(1, date(2026, 9, 7), "Institution Day", 1)
    result = generate_schedule(
        course=make_course(total_units=4, min_session_units=4, max_session_units=4),
        semester=make_semester(end=date(2026, 9, 7)),
        planning_period=make_period(end=date(2026, 9, 7)),
        time_windows=[TimeWindowPlan(id=1, weekday=0, start_time=time(8), end_time=time(12))],
        holidays={holiday.date: holiday},
    )
    assert not result.ok
    assert [error.code for error in result.errors] == [
        FailureCode.INSUFFICIENT_SEMESTER_CAPACITY,
        FailureCode.INSTITUTION_HOLIDAY,
    ]
    evidence = [error for error in result.errors if error.code == FailureCode.INSTITUTION_HOLIDAY]
    assert [(item.holiday_date, item.holiday_name) for item in evidence] == [(date(2026, 9, 7), "Institution Day")]


def test_generator_skips_holiday_and_uses_next_allowed_date():
    holiday = HolidayReference(1, date(2026, 9, 7), "Institution Day", 1)
    result = generate_schedule(
        course=make_course(total_units=4, min_session_units=4, max_session_units=4),
        semester=make_semester(end=date(2026, 9, 14)),
        planning_period=make_period(end=date(2026, 9, 14)),
        time_windows=[TimeWindowPlan(id=1, weekday=0, start_time=time(8), end_time=time(12))],
        holidays={holiday.date: holiday},
    )
    assert result.ok
    assert [item.date for item in result.sessions] == [date(2026, 9, 14)]


def test_uses_ordered_allowed_windows_and_falls_back_to_another_allowed_window():
    windows = [
        TimeWindowPlan(id=1, weekday=0, start_time=time(8, 0), end_time=time(10, 0)),
        TimeWindowPlan(id=2, weekday=1, start_time=time(8, 0), end_time=time(12, 0)),
    ]

    result = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        planning_period=make_period(),
        time_windows=windows,
    )

    assert result.ok
    assert result.sessions[0].time_window_id == 2
    assert result.sessions[0].date == date(2026, 9, 8)


def test_places_multiple_sessions_in_week_without_same_day_when_weeks_are_insufficient():
    result = generate_schedule(
        course=make_course(total_units=8),
        semester=make_semester(start=date(2026, 9, 7), end=date(2026, 9, 13)),
        planning_period=make_period(start=date(2026, 9, 7), end=date(2026, 9, 13)),
        time_windows=make_windows(),
    )

    assert result.ok
    assert [session.date for session in result.sessions] == [date(2026, 9, 7), date(2026, 9, 9)]
    assert len({session.date for session in result.sessions}) == 2


def test_rejects_insufficient_room_capacity_and_invalid_preference():
    result = generate_schedule(
        course=make_course(room_capacity=40, cohort_size=45, min_session_units=5, max_session_units=4),
        semester=make_semester(),
        planning_period=make_period(),
        time_windows=make_windows(),
    )

    assert not result.ok
    assert {error.code for error in result.errors} == {
        FailureCode.INSUFFICIENT_ROOM_CAPACITY,
        FailureCode.INVALID_SESSION_PREFERENCE,
    }


def test_rejects_no_fitting_time_window():
    result = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        planning_period=make_period(),
        time_windows=[TimeWindowPlan(id=1, weekday=0, start_time=time(8, 0), end_time=time(9, 0))],
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.NO_FITTING_TIME_WINDOW]


def test_rejects_insufficient_semester_capacity():
    result = generate_schedule(
        course=make_course(total_units=12),
        semester=make_semester(start=date(2026, 9, 7), end=date(2026, 9, 13)),
        planning_period=make_period(start=date(2026, 9, 7), end=date(2026, 9, 13)),
        time_windows=make_windows(),
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.INSUFFICIENT_SEMESTER_CAPACITY]


def test_uses_custom_planning_period_bounds():
    result = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        planning_period=make_period(start=date(2026, 9, 21), end=date(2026, 9, 27)),
        time_windows=make_windows(),
    )

    assert result.ok
    assert [session.date for session in result.sessions] == [date(2026, 9, 21)]


def test_rejects_planning_period_outside_semester():
    result = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        planning_period=make_period(start=date(2026, 9, 1), end=date(2026, 9, 7)),
        time_windows=make_windows(),
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.INVALID_PLANNING_PERIOD]


def test_rejects_missing_and_invalid_allowed_windows():
    missing = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        planning_period=make_period(),
        time_windows=[],
    )
    invalid = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        planning_period=make_period(),
        time_windows=[TimeWindowPlan(id=None, weekday=7, start_time=time(9, 0), end_time=time(8, 0))],
    )

    assert [error.code for error in missing.errors] == [FailureCode.MISSING_TEACHING_WINDOW]
    assert [error.code for error in invalid.errors] == [FailureCode.INVALID_TEACHING_WINDOW]


def test_generation_assigns_exactly_one_feasible_resource_and_minimizes_switches():
    monday_block = ResourceUnavailabilityPeriod(
        lecturer_id=1,
        kind="recurring",
        start_time=time(8),
        end_time=time(12),
    )
    monday_block.weekdays = [ResourceUnavailabilityWeekday(weekday=0)]
    course = make_course(
        total_units=8,
        lecturer_candidates=(
            ResourceCandidatePlan(id=1, normalized_code="lec-a", unavailable_periods=(monday_block,)),
            ResourceCandidatePlan(id=2, normalized_code="lec-b"),
        ),
        room_candidates=(
            ResourceCandidatePlan(id=1, normalized_code="room-small", capacity=20),
            ResourceCandidatePlan(id=2, normalized_code="room-main", capacity=40),
        ),
    )

    result = generate_schedule(course, make_semester(), make_period(), make_windows())

    assert result.ok
    assert [session.lecturer_id for session in result.sessions] == [2, 2]
    assert [session.room_id for session in result.sessions] == [2, 2]
    assert all(session.lecturer_id is not None and session.room_id is not None for session in result.sessions)


def test_generation_reports_resource_infeasibility_when_every_candidate_is_blocked():
    block = ResourceUnavailabilityPeriod(
        lecturer_id=1,
        kind="recurring",
        start_time=time(8),
        end_time=time(12),
    )
    block.weekdays = [ResourceUnavailabilityWeekday(weekday=0), ResourceUnavailabilityWeekday(weekday=2)]
    result = generate_schedule(
        make_course(
            total_units=4,
            lecturer_candidates=(ResourceCandidatePlan(id=1, normalized_code="lec-a", unavailable_periods=(block,)),),
            room_candidates=(ResourceCandidatePlan(id=1, normalized_code="room-a", capacity=40),),
        ),
        make_semester(),
        make_period(start=date(2026, 9, 7), end=date(2026, 9, 9)),
        make_windows(),
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.NO_FEASIBLE_RESOURCE]


def test_resource_blocked_holiday_is_not_reported_as_generation_evidence():
    block = ResourceUnavailabilityPeriod(
        lecturer_id=1,
        kind="recurring",
        start_time=time(8),
        end_time=time(12),
    )
    block.weekdays = [ResourceUnavailabilityWeekday(weekday=0), ResourceUnavailabilityWeekday(weekday=2)]
    holiday = HolidayReference(1, date(2026, 9, 7), "Institution Day", 1)
    result = generate_schedule(
        make_course(
            total_units=4,
            lecturer_candidates=(ResourceCandidatePlan(id=1, normalized_code="lec-a", unavailable_periods=(block,)),),
            room_candidates=(ResourceCandidatePlan(id=1, normalized_code="room-a", capacity=40),),
        ),
        make_semester(),
        make_period(start=date(2026, 9, 7), end=date(2026, 9, 9)),
        make_windows(),
        holidays={holiday.date: holiday},
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.NO_FEASIBLE_RESOURCE]


def test_temporal_placement_skips_a_blocked_window_when_a_later_window_is_resource_feasible():
    monday_block = ResourceUnavailabilityPeriod(
        lecturer_id=1, kind="recurring", start_time=time(8), end_time=time(12)
    )
    monday_block.weekdays = [ResourceUnavailabilityWeekday(weekday=0)]
    result = generate_schedule(
        make_course(
            total_units=4,
            lecturer_candidates=(ResourceCandidatePlan(id=1, normalized_code="lec-a", unavailable_periods=(monday_block,)),),
            room_candidates=(ResourceCandidatePlan(id=1, normalized_code="room-a", capacity=40),),
        ),
        make_semester(),
        make_period(),
        make_windows(),
    )

    assert result.ok
    assert result.sessions[0].date == date(2026, 9, 9)
