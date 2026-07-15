from datetime import date, datetime, time

from app.models.planning import DraftSchedule, DraftSession, ResourceUnavailabilityPeriod, ResourceUnavailabilityWeekday, Room
from app.services.draft_schedule_validation import ValidationAlertCode, collect_validation_alerts
from app.services.resource_rules import (
    ResourceChoice,
    assign_resource_sequence,
    intervals_overlap,
    period_overlaps_session,
    resource_is_unavailable,
)


def recurring(weekdays: list[int], start: time, end: time):
    period = ResourceUnavailabilityPeriod(lecturer_id=1, kind="recurring", start_time=start, end_time=end)
    period.weekdays = [ResourceUnavailabilityWeekday(weekday=value) for value in weekdays]
    return period


def test_half_open_overlap_requires_positive_shared_duration():
    assert intervals_overlap(datetime(2026, 9, 7, 9), datetime(2026, 9, 7, 11), datetime(2026, 9, 7, 10), datetime(2026, 9, 7, 12))
    assert not intervals_overlap(datetime(2026, 9, 7, 9), datetime(2026, 9, 7, 11), datetime(2026, 9, 7, 11), datetime(2026, 9, 7, 12))


def test_recurring_period_expands_on_each_selected_weekday_only():
    period = recurring([0, 2], time(9), time(11))
    assert period_overlaps_session(period, date(2026, 9, 7), time(10), time(12))
    assert period_overlaps_session(period, date(2026, 9, 9), time(10), time(12))
    assert not period_overlaps_session(period, date(2026, 9, 8), time(10), time(12))


def test_dated_period_may_span_dates_and_uses_exact_boundaries():
    period = ResourceUnavailabilityPeriod(room_id=1, kind="dated", start_date=date(2026, 9, 7), end_date=date(2026, 9, 9), start_time=time(15), end_time=time(10))
    assert period_overlaps_session(period, date(2026, 9, 8), time(8), time(9))
    assert not period_overlaps_session(period, date(2026, 9, 9), time(10), time(11))


def test_recurring_and_dated_periods_combine_as_unavailability_union():
    recurring_period = recurring([0], time(9), time(11))
    dated_period = ResourceUnavailabilityPeriod(lecturer_id=1, kind="dated", start_date=date(2026, 9, 7), end_date=date(2026, 9, 7), start_time=time(10), end_time=time(12))
    assert resource_is_unavailable([recurring_period, dated_period], date(2026, 9, 7), time(9, 30), time(11, 30))


def test_validation_reports_separate_unavailability_alerts_without_mutating_session():
    lecturer_period = recurring([0], time(9), time(11))
    room_period = ResourceUnavailabilityPeriod(room_id=1, kind="dated", start_date=date(2026, 9, 7), end_date=date(2026, 9, 7), start_time=time(10), end_time=time(12))
    draft = DraftSchedule(id=1, course_id=1, semester_id=1, course_name_snapshot="Course", course_total_units_snapshot=4, course_min_session_units_snapshot=2, course_max_session_units_snapshot=4, cohort_id_snapshot=1, cohort_name_snapshot="Cohort", cohort_size_snapshot=20, study_type_id_snapshot=1, study_type_name_snapshot="Type", semester_name_snapshot="Fall", semester_start_date_snapshot=date(2026, 9, 1), semester_end_date_snapshot=date(2026, 12, 20))
    session = DraftSession(id=1, draft_schedule_id=1, course_id=1, lecturer_id=1, cohort_id=1, room_id=1, date=date(2026, 9, 7), start_time=time(10), end_time=time(11), units=2, constraint_window_index=0)
    draft.sessions = [session]
    before = (session.lecturer_id, session.room_id, session.date, session.start_time, session.end_time)
    alerts = collect_validation_alerts([draft], rooms_by_id={1: Room(id=1, name="R", capacity=10)}, constraints_by_course_id={}, study_windows_by_study_type_id={}, unavailability_by_resource={("lecturer", 1): [lecturer_period], ("room", 1): [room_period]}, eligible_lecturer_ids_by_course={1: {2}}, eligible_room_ids_by_course={1: {2}}, active_lecturer_ids={1, 2}, active_room_ids={1, 2})
    codes = {alert.code for alert in alerts[1]}
    assert {ValidationAlertCode.LECTURER_UNAVAILABLE, ValidationAlertCode.ROOM_UNAVAILABLE}.issubset(codes)
    assert {ValidationAlertCode.LECTURER_INELIGIBLE, ValidationAlertCode.ROOM_INELIGIBLE, ValidationAlertCode.ROOM_CAPACITY}.issubset(codes)
    assert (session.lecturer_id, session.room_id, session.date, session.start_time, session.end_time) == before


def test_assignment_minimizes_transitions_after_hard_feasibility_filtering():
    choices = [
        ResourceChoice(id=2, normalized_code="beta"),
        ResourceChoice(id=1, normalized_code="alpha"),
    ]

    assigned = assign_resource_sequence(
        choices,
        feasible_ids_by_session=[{1, 2}, {2}, {1, 2}],
    )

    assert assigned == [2, 2, 2]


def test_assignment_uses_normalized_code_then_id_as_stable_tie_breakers():
    assigned = assign_resource_sequence(
        [
            ResourceChoice(id=3, normalized_code="same"),
            ResourceChoice(id=2, normalized_code="beta"),
            ResourceChoice(id=1, normalized_code="alpha"),
        ],
        feasible_ids_by_session=[{1, 2, 3}, {1, 2, 3}],
    )

    assert assigned == [1, 1]
    assert assign_resource_sequence(
        [ResourceChoice(id=3, normalized_code="same"), ResourceChoice(id=4, normalized_code="same")],
        feasible_ids_by_session=[{3, 4}],
    ) == [3]


def test_assignment_returns_none_when_any_session_has_no_feasible_candidate():
    assert assign_resource_sequence(
        [ResourceChoice(id=1, normalized_code="alpha")],
        feasible_ids_by_session=[{1}, set()],
    ) is None
