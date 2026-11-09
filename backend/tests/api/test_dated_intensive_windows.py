"""I-009 wire contracts, through authenticated disposable HTTP sessions."""
import json
from pathlib import Path

import pytest

from tests.api.test_academic_catalog import client, db_session  # noqa: F401

FIXTURE = Path(__file__).parents[1] / "fixtures/dated_intensive_contracts.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_backend_and_client_contract_examples_are_identical():
    client_fixture = Path(__file__).parents[3] / "client/src/test/datedIntensiveContracts.json"
    assert json.loads(client_fixture.read_text(encoding="utf-8")) == CASES


def test_precise_generated_sessions_round_trip_calendar_and_unchanged_edit(client, db_session):
    from dataclasses import replace
    from datetime import date, time
    from app.models.planning import Course, CourseEligibleLecturer, CourseEligibleRoom
    from app.services.draft_schedule_repository import load_course_plan, replace_draft_schedule, get_draft_schedule
    from app.services.schedule_generation import TimeWindowPlan, PlanningPeriodPlan, intensive_instruction_ticks
    from app.services.semester_optimization import optimize_semester
    from app.services.schedule_lifecycle import get_lifecycle_overview, create_working_revision
    from tests.optimization_fixtures import optimization_course
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester

    day = date(2026, 9, 7)
    _, first = seed_lifecycle_semester(db_session, with_schedule=False)
    first.total_units = first.min_session_units = first.max_session_units = 1
    db_session.add(Course(id=2, name='Second', total_units=1, min_session_units=1, max_session_units=1,
        cohort_id=1, study_type_id=1, current_semester_id=1,
        eligible_lecturers=[CourseEligibleLecturer(lecturer_id=1)],
        eligible_rooms=[CourseEligibleRoom(room_id=1)]))
    db_session.commit()
    weekly = post_window(client, {'id': 1}, kind='weekly', weekday=0, date=None,
        startTime='09:00', endTime='10:31').json()
    marked = post_window(client, {'id': 1}, date=day.isoformat(),
        startTime='09:45', endTime='09:46', isIntensive=True).json()
    windows = (TimeWindowPlan(weekly['id'], 0, time(9), time(10, 31)),
        TimeWindowPlan(marked['id'], None, time(9, 45), time(9, 46), kind='dated', date=day, is_intensive=True))
    base = optimization_course(1, total_units=1, min_units=1, max_units=1, cohort_id=1)
    courses = [replace(base, course_id=i, windows=windows, planning_period=PlanningPeriodPlan(day, day)) for i in (1, 2)]
    solution = optimize_semester(courses, [], generated_only=True, deadline_seconds=10)
    assert solution.daily_variety == 1
    revision = create_working_revision(db_session, 1, get_lifecycle_overview(db_session, 1)['stateToken'])['activeWorkingRevision']['revisionId']
    for item in solution.courses:
        replace_draft_schedule(db_session, load_course_plan(db_session, item.course_id), 1, list(item.sessions))
    db_session.commit()
    all_before = [(s.date, s.start_time, s.end_time) for i in (1, 2) for s in get_draft_schedule(db_session, i, 1).sessions]
    later = max(solution.courses, key=lambda c: c.sessions[0].start_time)
    actual = later.sessions[0]
    assert actual.start_time.microsecond == 1
    read = client.get(f'/api/courses/{later.course_id}/draft-schedule?semesterId=1').json()['sessions'][0]
    assert time.fromisoformat(read['startTime']) == actual.start_time
    assert time.fromisoformat(read['endTime']) == actual.end_time
    workspace = client.get('/api/semesters/1/calendar-workspace').json()
    occurrence = next(o for o in workspace['occurrences'] if o['occurrenceRef'] == f'teaching:{read["id"]}')
    assert occurrence['startTime'] == read['startTime']
    assert occurrence['endTime'] == read['endTime']
    saved = client.patch(f'/api/draft-sessions/{read["id"]}', json={
        key: read[key] for key in ('date', 'startTime', 'endTime', 'units', 'lecturerId', 'roomId')
    } | {'scheduleRevisionId': revision})
    assert saved.status_code == 200, saved.text
    assert saved.json()['sessions'][0]['validationAlerts'] == []
    all_after = [(s.date, s.start_time, s.end_time) for i in (1, 2) for s in get_draft_schedule(db_session, i, 1).sessions]
    assert all_after == all_before
    assert sum(intensive_instruction_ticks(s.date, s.start_time, s.end_time, s.units, windows)
        for i in (1, 2) for s in get_draft_schedule(db_session, i, 1).sessions) == solution.intensive_teaching_time


@pytest.mark.parametrize("payload", CASES["windows"])
def test_window_wire_shape_round_trip(client, payload):
    owner = client.post("/api/academic/study-types", json={"name": "Form"}).json()
    response = client.post(f'/api/academic/study-types/{owner["id"]}/time-windows', json=payload)
    assert response.status_code == 201, response.text
    row = response.json()
    assert {key: row.get(key) for key in payload} == payload
    assert row["overlapNotice"] is None
    assert client.get(f'/api/academic/time-windows/{row["id"]}').json() == row


def test_invalid_dated_fields_return_aggregate_german_envelope(client):
    owner = client.post("/api/academic/study-types", json={"name": "Form"}).json()
    response = client.post(f'/api/academic/study-types/{owner["id"]}/time-windows', json=CASES["invalid"])
    assert response.status_code == 422
    errors = response.json()["errors"]
    assert set(CASES["errorFields"]) <= {error["field"] for error in errors}
    assert all(error["code"] == "VALIDATION_ERROR" and error["message"] for error in errors)
    assert all("Input should" not in error["message"] for error in errors)


def create_form(client, name="Form"):
    return client.post('/api/academic/study-types', json={"name": name}).json()


def post_window(client, owner, **changes):
    return client.post(f'/api/academic/study-types/{owner["id"]}/time-windows', json={**CASES['windows'][1], **changes})


def test_dated_edit_owner_kind_lock_stale_and_lifecycle(client):
    owner, other = create_form(client), create_form(client, 'Andere')
    result = post_window(client, owner)
    assert result.status_code == 201, result.text
    row = result.json()
    payload = {**CASES['windows'][1], 'studyTypeId': other['id'], 'expectedRevision': row['revision'], 'isIntensive': True}
    url = f'/api/academic/time-windows/{row["id"]}'
    moved = client.patch(url, json=payload)
    assert moved.status_code == 200, moved.text
    assert moved.json()['id'] == row['id']
    assert moved.json()['studyTypeId'] == other['id']
    assert moved.json()['revision'] == row['revision'] + 1
    assert client.patch(url, json=payload).status_code == 409
    payload.update(expectedRevision=moved.json()['revision'], kind='weekly', weekday=0, date=None, isIntensive=False)
    assert client.patch(url, json=payload).status_code == 422
    assert client.get(url).json() == moved.json()
    archived = client.post(url + '/archive', json={'expectedRevision': moved.json()['revision']})
    assert archived.status_code == 200, archived.text
    assert post_window(client, other, isIntensive=False).status_code == 409


def test_overlap_not_capacity_and_adjacency_not_overlap(client):
    owner = create_form(client)
    first = post_window(client, owner)
    assert first.status_code == 201
    overlap = post_window(client, owner, startTime='11:00', endTime='13:00')
    assert overlap.status_code == 201
    assert 'Kapazität' in overlap.json()['overlapNotice']
    adjacent = post_window(client, owner, startTime='13:00', endTime='14:00')
    assert adjacent.status_code == 201
    assert adjacent.json()['overlapNotice'] is None
    assert post_window(client, create_form(client, 'Andere')).status_code == 201


def test_inactive_form_blocks_creation_and_reactivation(client):
    owner = create_form(client)
    row = post_window(client, owner).json()
    assert 'id' in row
    url = f'/api/academic/time-windows/{row["id"]}'
    archived = client.post(url + '/archive', json={'expectedRevision': row['revision']})
    assert archived.status_code == 200
    assert client.post(f'/api/academic/study-types/{owner["id"]}/archive', json={'expectedRevision': owner['revision']}).status_code == 200
    assert post_window(client, owner, date='2026-11-10').status_code == 422
    assert client.post(url + '/reactivate', json={'expectedRevision': archived.json()['revision']}).status_code == 409


@pytest.mark.parametrize('changes,fields', [
    ({'kind':'unexpected'}, {'kind'}),
    ({'date':'09.11.2026'}, {'date'}),
    ({'date':'2026-11-09T09:00:00'}, {'date'}),
    ({'date':None}, {'date'}),
    ({'weekday':False, 'isIntensive':1}, {'weekday','isIntensive'}),
    ({'startTime':'23:00', 'endTime':'01:00'}, {'endTime'}),
    ({'startTime':'bad', 'endTime':'bad'}, {'startTime','endTime'}),
    ({'kind':'weekly','weekday':7,'date':None,'isIntensive':True}, {'weekday','isIntensive'}),
])
def test_invalid_shapes_never_write(client, changes, fields):
    owner = create_form(client)
    response = post_window(client, owner, **changes)
    assert response.status_code == 422, response.text
    assert fields <= {e['field'] for e in response.json()['errors']}
    assert client.get(f'/api/academic/study-types/{owner["id"]}/time-windows').json() == []


def test_legacy_weekly_requests_remain_weekly(client):
    owner = create_form(client)
    payload = {'weekday': 4, 'startTime':'09:00', 'endTime':'12:00', 'sortOrder':5}
    row = client.post(f'/api/academic/study-types/{owner["id"]}/time-windows', json=payload).json()
    assert row.get('kind') == 'weekly'
    assert row.get('date') is None and row.get('isIntensive') is False
    updated = client.patch(f'/api/academic/time-windows/{row["id"]}', json={**payload,'expectedRevision':row['revision']})
    assert updated.status_code == 200
    assert updated.json()['kind'] == 'weekly'


def test_precise_window_clocks_survive_catalog_and_derived_context(client, db_session):
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester
    seed_lifecycle_semester(db_session, with_schedule=False)
    row = post_window(client, {'id': 1}, startTime='09:00:30.000001', endTime='12:00:30.000001').json()
    assert row['startTime'] == '09:00:30.000001'
    assert row['endTime'] == '12:00:30.000001'
    for window in [client.get(f'/api/academic/time-windows/{row["id"]}').json(),
                   client.get('/api/planning-options?semesterId=1').json()['timeWindows'][0],
                   client.get('/api/courses/1/generation-constraints?semesterId=1').json()['allowedTeachingWindows'][0]]:
        assert window['startTime'] == row['startTime']
        assert window['endTime'] == row['endTime']


def test_planning_options_and_direct_constraints_preserve_dated_facts(client, db_session):
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester
    from app.services.schedule_lifecycle import get_lifecycle_overview, create_working_revision
    seed_lifecycle_semester(db_session, with_schedule=True)
    created = post_window(client, {'id':1}, isIntensive=True)
    assert created.status_code == 201
    initial = get_lifecycle_overview(db_session, 1)
    create_working_revision(db_session, 1, initial['stateToken'])
    db_session.commit()
    options = client.get('/api/planning-options?semesterId=1')
    assert options.status_code == 200, options.text
    window = options.json()['timeWindows'][0]
    assert (window['kind'],window['date'],window['weekday'],window['isIntensive']) == ('dated','2026-11-09',None,True)
    constraints = client.get('/api/courses/1/generation-constraints?semesterId=1')
    assert constraints.status_code == 200, constraints.text
    assert constraints.json()['allowedTeachingWindows'][0]['date'] == '2026-11-09'


def test_dated_only_minimum_occurrence_controls_availability(client, db_session):
    from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester
    seed_lifecycle_semester(db_session, with_schedule=False)
    for day, end, expected in [('2027-11-09','12:00',False), ('2026-11-09','09:45',False), ('2026-11-09','12:00',True)]:
        row = post_window(client, {'id':1}, date=day, endTime=end).json()
        options = client.get('/api/planning-options?semesterId=1')
        assert options.status_code == 200, options.text
        assert options.json()['courses'][0]['availability']['available'] is expected
        assert client.delete(f'/api/academic/time-windows/{row["id"]}?expectedRevision={row["revision"]}').status_code == 204


@pytest.mark.parametrize('payload', [CASES['windows'][0],CASES['windows'][2]])
def test_copy_is_an_ordinary_independent_create_even_if_source_changes_or_is_deleted(client,payload):
    owner,other=create_form(client),create_form(client,'Andere')
    source=client.post(f'/api/academic/study-types/{owner["id"]}/time-windows',json=payload).json()
    captured={key:source[key] for key in payload}
    url=f'/api/academic/time-windows/{source["id"]}'
    changed=client.patch(url,json={**captured,'startTime':'09:35','expectedRevision':source['revision']}).json()
    copy=client.post(f'/api/academic/study-types/{other["id"]}/time-windows',json=captured)
    assert copy.status_code == 201,copy.text
    assert copy.json()['id'] != source['id'] and copy.json()['startTime'] == captured['startTime']
    assert client.delete(url+f'?expectedRevision={changed["revision"]}').status_code == 204
    assert client.get(f'/api/academic/time-windows/{copy.json()["id"]}').json() == copy.json()
    assert client.post(f'/api/academic/study-types/{owner["id"]}/time-windows',json=captured).status_code == 201
