from datetime import date, time

from app.schemas.draft_schedule import FailureCode
from app.services.schedule_generation import (
    CoursePlan,
    SemesterPlan,
    TimeWindowPlan,
    distribute_units,
    generate_schedule,
    session_duration_minutes,
)


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
        time_windows=make_windows(),
        selected_time_window_id=1,
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


def test_prefers_selected_window_and_falls_back_to_another_allowed_window():
    windows = [
        TimeWindowPlan(id=1, weekday=0, start_time=time(8, 0), end_time=time(10, 0)),
        TimeWindowPlan(id=2, weekday=1, start_time=time(8, 0), end_time=time(12, 0)),
    ]

    result = generate_schedule(
        course=make_course(total_units=4),
        semester=make_semester(),
        time_windows=windows,
        selected_time_window_id=1,
    )

    assert result.ok
    assert result.sessions[0].time_window_id == 2
    assert result.sessions[0].date == date(2026, 9, 8)


def test_places_multiple_sessions_in_week_without_same_day_when_weeks_are_insufficient():
    result = generate_schedule(
        course=make_course(total_units=8),
        semester=make_semester(start=date(2026, 9, 7), end=date(2026, 9, 13)),
        time_windows=make_windows(),
        selected_time_window_id=1,
    )

    assert result.ok
    assert [session.date for session in result.sessions] == [date(2026, 9, 7), date(2026, 9, 9)]
    assert len({session.date for session in result.sessions}) == 2


def test_rejects_insufficient_room_capacity_and_invalid_preference():
    result = generate_schedule(
        course=make_course(room_capacity=40, cohort_size=45, min_session_units=5, max_session_units=4),
        semester=make_semester(),
        time_windows=make_windows(),
        selected_time_window_id=1,
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
        time_windows=[TimeWindowPlan(id=1, weekday=0, start_time=time(8, 0), end_time=time(9, 0))],
        selected_time_window_id=1,
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.NO_FITTING_TIME_WINDOW]


def test_rejects_insufficient_semester_capacity():
    result = generate_schedule(
        course=make_course(total_units=12),
        semester=make_semester(start=date(2026, 9, 7), end=date(2026, 9, 13)),
        time_windows=make_windows(),
        selected_time_window_id=1,
    )

    assert not result.ok
    assert [error.code for error in result.errors] == [FailureCode.INSUFFICIENT_SEMESTER_CAPACITY]
