from datetime import date, time, timedelta
from time import perf_counter
from types import SimpleNamespace

from app.services.draft_schedule_repository import GenerationConstraints
from app.services.draft_schedule_validation import ValidationAlertCode, collect_validation_alerts
from app.services.holiday_calendar import HolidayReference
from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan


def test_fifty_holidays_and_five_hundred_sessions_are_validated_within_two_seconds():
    start = date(2026, 9, 7)
    holiday_dates = [start + timedelta(days=index) for index in range(50)]
    holidays = {
        day: HolidayReference(index + 1, day, f"Holiday {index + 1}", 1)
        for index, day in enumerate(holiday_dates)
    }
    sessions = [
        SimpleNamespace(
            id=index + 1,
            date=holiday_dates[index % len(holiday_dates)],
            start_time=time(8),
            end_time=time(9),
            lecturer_id=index + 1,
            room_id=index + 1,
            cohort_id=index + 1,
        )
        for index in range(500)
    ]
    draft = SimpleNamespace(
        id=1,
        course_id=1,
        course_name_snapshot="Reference Course",
        cohort_name_snapshot="Reference Cohort",
        cohort_size_snapshot=30,
        study_type_id_snapshot=1,
        sessions=sessions,
    )
    rooms = {
        index + 1: SimpleNamespace(id=index + 1, name=f"Room {index + 1}", capacity=40)
        for index in range(500)
    }
    windows = [TimeWindowPlan(index + 1, index, time(8), time(12)) for index in range(7)]
    constraints = GenerationConstraints(
        1,
        1,
        PlanningPeriodPlan(start, start + timedelta(days=90)),
        windows,
        False,
    )

    started = perf_counter()
    alerts = collect_validation_alerts(
        [draft],
        rooms_by_id=rooms,
        constraints_by_course_id={1: constraints},
        study_windows_by_study_type_id={1: windows},
        holidays_by_date=holidays,
    )
    elapsed = perf_counter() - started

    assert elapsed < 2
    assert len(alerts) == 500
    assert all(
        any(alert.code == ValidationAlertCode.INSTITUTION_HOLIDAY for alert in session_alerts)
        for session_alerts in alerts.values()
    )
