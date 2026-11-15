from __future__ import annotations

from datetime import date, timedelta


SEMESTER_START = date(2026, 9, 1)
SEMESTER_END = date(2027, 1, 31)


def calendar_workspace_scale_fixture(
    *,
    course_count: int = 100,
    occurrence_count: int = 500,
    holiday_count: int = 50,
) -> dict:
    """Return deterministic, bounded source records for workspace tests."""

    courses = [
        {
            "course_id": index,
            "name": f"Course {index:03d}",
            "total_units": 10,
            "cohort_id": index,
            "cohort_name": f"Cohort {index:03d}",
            "cohort_size": 20 + index % 25,
            "cohort_calendar_id": 1 + index % 3,
            "cohort_calendar_name": ("Full-time", "Part-time", "Evening")[index % 3],
            "lecturer_id": 1 + index % 20,
            "lecturer_name": f"Lecturer {1 + index % 20:02d}",
            "room_id": 1 + index % 30,
            "room_name": f"Room {1 + index % 30:02d}",
            "room_capacity": 20 + (index % 6) * 10,
        }
        for index in range(1, course_count + 1)
    ]
    occurrences = []
    for index in range(1, occurrence_count + 1):
        course = courses[(index - 1) % course_count]
        occurrence_date = SEMESTER_START + timedelta(days=(index * 3) % 145)
        kind = "exam" if index % 10 == 0 else "teaching"
        occurrences.append(
            {
                "id": index,
                "kind": kind,
                "course_id": course["course_id"],
                "date": occurrence_date,
                "start_hour": 8 + index % 8,
                "units": 0 if kind == "exam" else 2,
                "lecturer_id": course["lecturer_id"],
                "room_id": course["room_id"],
                "cohort_id": course["cohort_id"],
            }
        )
    holidays = [
        {
            "id": index,
            "date": SEMESTER_START + timedelta(days=(index * 2) % 145),
            "name": f"Institution holiday {index:02d}",
        }
        for index in range(1, holiday_count + 1)
    ]
    return {
        "semester": {
            "semester_id": 1,
            "name": "Reference Semester",
            "start_date": SEMESTER_START,
            "end_date": SEMESTER_END,
        },
        "courses": courses,
        "occurrences": occurrences,
        "holidays": holidays,
    }


def small_calendar_workspace_fixture() -> dict:
    return calendar_workspace_scale_fixture(
        course_count=4,
        occurrence_count=12,
        holiday_count=2,
    )


def seed_time_grid_workspace(db, *, second_calendar=False, dated=False, capture='working'):
    """June reference facts, through the existing isolated lifecycle conventions."""
    from datetime import time
    from sqlalchemy import select
    from app.models.planning import CohortCalendar, CohortCalendarTimeWindow, DraftSchedule, DraftSession, Lecturer
    from app.services.schedule_lifecycle import create_working_revision, get_lifecycle_overview, prepare_publication, transition_revision
    from app.models.planning import ScheduleRevision
    from copy import deepcopy
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester

    semester, course = seed_lifecycle_semester(db)
    semester.start_date, semester.end_date = date(2027, 6, 1), date(2027, 6, 30)
    calendar = db.get(CohortCalendar, 1)
    calendar.start_date, calendar.end_date = semester.start_date, semester.end_date
    calendar.name = "Calendar A"
    draft = db.scalar(select(DraftSchedule))
    draft.semester_start_date_snapshot = semester.start_date
    draft.semester_end_date_snapshot = semester.end_date
    draft.cohort_calendar_name_snapshot = calendar.name
    db.get(Lecturer, 1).name = "Höber, Angelika"
    session = db.scalar(select(DraftSession))
    session.date, session.start_time, session.end_time = date(2027, 6, 26), time(12, 15), time(17, 20)
    db.add(CohortCalendarTimeWindow(cohort_calendar_id=1, weekday=5,
        start_time=time(8), end_time=time(16), sort_order=0))
    if dated:
        db.add_all([
            CohortCalendarTimeWindow(cohort_calendar_id=1, weekday=0,
                start_time=time(8), end_time=time(16), sort_order=1),
            CohortCalendarTimeWindow(cohort_calendar_id=1, kind='dated', weekday=None,
                date=date(2027, 6, 7), is_intensive=True,
                start_time=time(10), end_time=time(12), sort_order=2),
        ])
    if second_calendar:
        _, second_course = seed_lifecycle_semester(db, semester_id=2, with_schedule=False)
        second_course.current_semester_id = 1
        calendar_b = db.get(CohortCalendar, 2)
        calendar_b.semester_id = 1
        calendar_b.start_date, calendar_b.end_date = semester.start_date, semester.end_date
        calendar_b.name = 'Calendar B'
        db.add(CohortCalendarTimeWindow(cohort_calendar_id=2, weekday=5,
            start_time=time(10), end_time=time(18), sort_order=0))
    db.commit()
    create_working_revision(db, 1, get_lifecycle_overview(db, 1)["stateToken"])
    db.commit()
    if capture != 'working':
        lifecycle = get_lifecycle_overview(db, 1)
        revision = lifecycle['activeWorkingRevision']
        prepared = prepare_publication(db, revision['revisionId'], revision['revisionVersion'], lifecycle['stateToken'])
        transition_revision(db, revision['revisionId'], action='publish',
            expected_revision_version=revision['revisionVersion'], expected_state_token=lifecycle['stateToken'],
            confirmed=True, publication_token=prepared['preparationToken'])
        row = db.get(ScheduleRevision, revision['revisionId'])
        snapshot = deepcopy(row.snapshot_document)
        for index, source in enumerate(snapshot['courses']):
            if capture == 'legacy' or (capture == 'mixed' and index == 1):
                source.pop('constraintProfile', None)
            if capture == 'missing_identity':
                source['cohortCalendar'].pop('sourceId', None)
            if capture == 'legacy_metadata':
                for window in source['constraintProfile']['allowedTeachingWindows']:
                    window.pop('kind', None)
                    window.pop('isIntensive', None)
                    window['sourceTimeWindowId'] = None
        row.snapshot_document = snapshot
        db.commit()
    return semester, course


def time_grid_reference_intervals():
    """Independent explicit saved-time oracles (including break-inclusive gaps)."""
    return [
        ('overrun', '12:15', '17:20'),
        ('in_window', '09:00', '10:30'),
        ('gap_before', '09:00', '10:00'),
        ('gap_after', '12:00', '13:00'),
        ('boundary', '08:00', '16:00'),
        ('outside', '18:00', '19:00'),
        ('early', '00:00', '00:45'),
        ('late', '23:00', '23:45'),
    ]
