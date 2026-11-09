"""Exact-date permission must agree in validation and the real optimizer."""
from dataclasses import replace
from datetime import date, time, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.services.draft_schedule_repository import load_time_windows
from app.services.draft_schedule_validation import fits_any_validation_window
from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan
from app.services.semester_optimization import generate_candidates, optimize_semester
from tests.optimization_fixtures import optimization_course
from tests.fixtures.dated_intensive_windows import seed_forms, weekly_window

MONDAY = date(2026, 11, 9)


def dated(day=MONDAY, start=time(9), end=time(12), **changes):
    return TimeWindowPlan(1, None, start, end, kind='dated', date=day, **changes)


@pytest.mark.parametrize('day,expected', [(MONDAY, True), (MONDAY + timedelta(days=7), False), (date(2027,11,9), False)])
def test_exact_date_validation_never_recurs(day, expected):
    assert fits_any_validation_window(day, time(9), time(10), [dated()]) is expected


def test_adjacent_and_overlapping_windows_cannot_be_stitched():
    for second_start in (time(10), time(9,30)):
        windows = [dated(end=time(10)), dated(start=second_start, end=time(11))]
        assert not fits_any_validation_window(MONDAY, time(9), time(11), windows)
    assert fits_any_validation_window(MONDAY, time(9), time(12), [dated(is_intensive=True)])


@pytest.mark.parametrize('day_offset', range(7))
def test_real_solver_can_use_each_independent_dated_day_including_sunday(day_offset):
    day = MONDAY + timedelta(days=day_offset)
    course = replace(optimization_course(1, total_units=2, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(MONDAY, MONDAY + timedelta(days=13)),
        windows=(dated(day),))
    candidates = generate_candidates(course, [], frozenset()).candidates
    assert candidates and {candidate.date for candidate in candidates} == {day}
    result = optimize_semester([course], [], generated_only=True, deadline_seconds=10)
    assert result.total_units == 2
    assert [s.date for s in result.courses[0].sessions] == [day]


def test_dated_out_of_period_never_produces_candidates_and_mixed_sorting_is_safe():
    course = replace(optimization_course(1), planning_period=PlanningPeriodPlan(MONDAY, MONDAY),
        windows=(dated(MONDAY + timedelta(days=7)), TimeWindowPlan(2,4,time(9),time(12))))
    candidates = generate_candidates(course, [], frozenset()).candidates
    assert not candidates


def test_window_loader_preserves_form_activity_kind_date_marker():
    engine = create_engine('sqlite://')
    initialize_database(engine)
    with Session(engine) as db:
        seed_forms(db)
        db.add_all([weekly_window(), weekly_window(id=11, kind='dated', weekday=None, date=MONDAY, is_intensive=True),
                    weekly_window(id=12, study_type_id=2), weekly_window(id=13, weekday=5,is_active=False)])
        db.commit()
        windows = load_time_windows(db, 1)
        assert {w.id for w in windows} == {10,11}
        specific = next(w for w in windows if w.id == 11)
        assert (specific.kind,specific.date,specific.weekday,specific.is_intensive) == ('dated',MONDAY,None,True)
        from app.models.planning import StudyType
        db.get(StudyType,1).is_active = False
        db.commit()
        assert load_time_windows(db,1) == []


def test_calendar_and_lifecycle_capture_keep_dated_facts_without_mutating_saved_sessions():
    from app.services.calendar_workspace import get_calendar_workspace
    from app.services.schedule_lifecycle import get_lifecycle_overview, create_working_revision, get_revision_content
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester
    from app.models.planning import StudyTypeTimeWindow, DraftSession
    engine = create_engine('sqlite://')
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db)
        db.add(StudyTypeTimeWindow(study_type_id=1,kind='dated',date=date(2026,10,5),weekday=None,
            start_time=time(8),end_time=time(12),is_intensive=True))
        db.commit()
        before = [(s.id,s.date,s.start_time,s.end_time,s.units) for s in db.query(DraftSession)]
        overview = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, overview['stateToken'])
        workspace = get_calendar_workspace(db, 1)
        snapshot = get_revision_content(db, created['activeWorkingRevision']['revisionId'])['snapshot']
        window = snapshot['courses'][0]['constraintProfile']['allowedTeachingWindows'][0]
        assert (window['kind'],window['date'],window['isIntensive']) == ('dated','2026-10-05',True)
        assert not any(f['category'] == 'study_type_window' for f in workspace['validationFindings'])
        assert [(s.id,s.date,s.start_time,s.end_time,s.units) for s in db.query(DraftSession)] == before


def test_published_dated_capture_remains_immutable_after_source_marker_and_date_changes():
    from copy import deepcopy
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester
    from app.models.planning import StudyTypeTimeWindow, ScheduleRevision
    from app.services.schedule_lifecycle import get_lifecycle_overview,create_working_revision,prepare_publication,transition_revision,get_revision_content
    engine=create_engine('sqlite://')
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db)
        window_row=StudyTypeTimeWindow(study_type_id=1,kind='dated',weekday=None,date=date(2026,10,5),is_intensive=True,start_time=time(8),end_time=time(12))
        db.add(window_row);db.commit()
        created=create_working_revision(db,1,get_lifecycle_overview(db,1)['stateToken'])
        revision=created['activeWorkingRevision']
        preparation=prepare_publication(db,revision['revisionId'],revision['revisionVersion'],created['stateToken'])
        transition_revision(db,revision['revisionId'],action='publish',expected_revision_version=revision['revisionVersion'],
            expected_state_token=created['stateToken'],confirmed=True,publication_token=preparation['preparationToken'])
        db.commit()
        captured=deepcopy(db.get(ScheduleRevision,revision['revisionId']).snapshot_document)
        window_row.date=date(2026,10,6);window_row.is_intensive=False;window_row.revision+=1
        db.commit()
        assert get_revision_content(db,revision['revisionId'])['snapshot'] == captured
        saved_window=captured['courses'][0]['constraintProfile']['allowedTeachingWindows'][0]
        assert (saved_window['date'],saved_window['isIntensive']) == ('2026-10-05',True)
