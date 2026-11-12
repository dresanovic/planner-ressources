from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import (
    Course,
    DraftSchedule,
    DraftSession,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    Lecturer,
    Room,
    CohortCalendarTimeWindow,
)
from tests.planner_auth_fixtures import authenticate_test_client


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    with TestClient(app) as value:
        authenticate_test_client(value, db_session)
        yield value
    app.dependency_overrides.clear()


def seed_resources(db):
    db.add_all([Lecturer(id=1, name="Ada"), Room(id=1, name="R1", capacity=40)])
    db.commit()


def create_academic_chain(client):
    semester = client.post("/api/academic/semesters", json={"name": "Fall 2026", "startDate": "2026-09-01", "endDate": "2026-12-20"})
    cohort = client.post("/api/academic/cohorts", json={"name": "AI 1", "studentCount": 30})
    cohort_calendar = client.post("/api/academic/cohort-calendars", json={"cohortId": cohort.json()["id"], "semesterId": semester.json()["id"], "startDate":"2026-09-01", "endDate":"2026-12-20"})
    window = client.post(f"/api/academic/cohort-calendars/{cohort_calendar.json()['id']}/time-windows", json={"weekday": 0, "startTime": "08:00", "endTime": "12:00", "sortOrder": 0})
    return semester.json(), cohort.json(), cohort_calendar.json(), window.json()


def test_overall_units_default_persist_and_do_not_affect_planning(client, db_session):
    from app.services.draft_schedule_repository import course_semester_progress

    seed_resources(db_session)
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    payload = dict(name="Independent course total", totalUnits=8, minSessionUnits=2,
        maxSessionUnits=4, semesterId=semester['id'], cohortId=cohort['id'],
        lecturerId=1, roomId=1)
    created = client.post('/api/academic/courses', json=payload)
    assert created.status_code == 201, created.text
    row = created.json()
    assert row['overallUnits'] == row['totalUnits'] == 8
    update = {k: v for k, v in payload.items() if k not in ('lecturerId', 'roomId')}
    for extra, expected_total in [({'overallUnits': 20}, 20), ({'totalUnits': 6}, 20)]:
        update.update(extra)
        result = client.patch(f"/api/academic/courses/{row['id']}",
            json={**update, 'expectedRevision': row['revision']})
        assert result.status_code == 200, result.text
        row = result.json()
        assert row['overallUnits'] == expected_total
        update.pop('overallUnits', None)
        assert course_semester_progress(db_session, row['id'], semester['id']) == (row['totalUnits'], 0, row['totalUnits'])
    listed = client.get('/api/academic/courses').json()['items']
    assert next(item for item in listed if item['id'] == row['id'])['overallUnits'] == 20
    explicit = client.post('/api/academic/courses', json={**payload, 'name': 'Explicit total', 'overallUnits': 30})
    assert explicit.status_code == 201, explicit.text
    assert explicit.json()['overallUnits'] == 30
    invalid = client.patch(f"/api/academic/courses/{row['id']}",
        json={**update, 'overallUnits': 0, 'expectedRevision': row['revision']})
    assert invalid.status_code == 422


def test_optional_preferred_units_create_update_clear_and_bounds(client, db_session):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    payload = dict(name="Preferred length", totalUnits=12, minSessionUnits=2, maxSessionUnits=6,
        semesterId=semester["id"], cohortId=cohort["id"], lecturerId=1, roomId=1, preferredSessionUnits=3)
    response = client.post('/api/academic/courses', json=payload)
    assert response.status_code == 201
    row = response.json()
    assert row['preferredSessionUnits'] == 3
    update = {k: v for k, v in payload.items() if k not in ('lecturerId', 'roomId')}
    for value, expected_status in [(7, 422), (2.25, 422), (3.5, 200), (None, 200)]:
        result = client.patch(f"/api/academic/courses/{row['id']}",
            json={**update, 'preferredSessionUnits': value, 'expectedRevision': row['revision']})
        assert result.status_code == expected_status, result.text
        if expected_status == 200:
            row = result.json()
            assert row['preferredSessionUnits'] == value
    stored = client.get('/api/academic/courses').json()['items']
    assert next(item for item in stored if item['id'] == row['id'])['preferredSessionUnits'] is None


def test_create_list_and_revisit_complete_academic_catalog(client, db_session):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, window = create_academic_chain(client)
    course = client.post("/api/academic/courses", json={
        "name": "Scheduling 101", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    })

    assert course.status_code == 201
    assert course.json()["semester"] == {"id": semester["id"], "name": "Fall 2026"}
    assert course.json()["availability"] == {"available": True, "reasons": []}
    assert client.get("/api/academic/semesters").json()["total"] == 1
    assert client.get("/api/academic/cohorts").json()["items"][0]["studentCount"] == 30
    assert client.get("/api/academic/cohort-calendars").json()["items"][0]["timeWindows"][0]["id"] == window["id"]
    assert client.get("/api/academic/courses").json()["items"][0]["name"] == "Scheduling 101"


def test_validation_returns_all_fields_and_preserves_no_partial_record(client, db_session):
    seed_resources(db_session)
    response = client.post("/api/academic/semesters", json={"name": " ", "startDate": "2026-12-20", "endDate": "2026-09-01"})
    assert response.status_code == 422
    assert {error["field"] for error in response.json()["errors"]} == {"name", "endDate"}
    assert client.get("/api/academic/semesters").json()["total"] == 0


@pytest.mark.parametrize(("resource", "first", "duplicate"), [
    ("semesters", {"name": "Fall 2026", "startDate": "2026-09-01", "endDate": "2026-12-20"}, {"name": "  fall 2026  ", "startDate": "2027-01-01", "endDate": "2027-06-01"}),
    ("cohorts", {"name": "AI 1", "studentCount": 20}, {"name": "  ai 1  ", "studentCount": 25}),
])
def test_normalized_names_are_unique_for_each_named_catalog(client, resource, first, duplicate):
    assert client.post(f"/api/academic/{resource}", json=first).status_code == 201
    response = client.post(f"/api/academic/{resource}", json=duplicate)
    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "DUPLICATE_NORMALIZED_NAME"


def test_course_normalized_name_is_unique(client, db_session):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    payload = {
        "name": "Scheduling 101", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    }
    assert client.post("/api/academic/courses", json=payload).status_code == 201
    duplicate = client.post("/api/academic/courses", json={**payload, "name": " scheduling 101 "})
    assert duplicate.status_code == 409
    assert duplicate.json()["errors"][0]["code"] == "DUPLICATE_NORMALIZED_NAME"


def test_course_creation_rejects_inactive_lecturer_and_undersized_room(client, db_session):
    db_session.add_all([
        Lecturer(id=1, name="Inactive", is_active=False),
        Room(id=1, name="Small", capacity=20),
    ])
    db_session.commit()
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)

    response = client.post("/api/academic/courses", json={
        "name": "Invalid resources", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    })

    assert response.status_code == 422
    assert {error["code"] for error in response.json()["errors"]} == {
        "RESOURCE_INACTIVE", "ROOM_CAPACITY_INSUFFICIENT",
    }


def test_course_metadata_update_preserves_complete_resource_eligibility(client, db_session):
    seed_resources(db_session)
    db_session.add_all([Lecturer(id=2, name="Grace"), Room(id=2, name="R2", capacity=50)])
    db_session.commit()
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    course = client.post("/api/academic/courses", json={
        "name": "Scheduling", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    }).json()
    eligibility_url = f"/api/academic/courses/{course['id']}/resource-eligibility"
    configured = client.put(eligibility_url, json={
        "expectedRevision": course["revision"], "lecturerIds": [1, 2], "roomIds": [1, 2],
    }).json()

    changed = client.patch(f"/api/academic/courses/{course['id']}", json={
        "name": "Scheduling renamed", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "expectedRevision": configured["courseRevision"],
    })

    assert changed.status_code == 200
    db_session.expire_all()
    persisted = db_session.get(Course, course["id"])
    assert [item.lecturer_id for item in persisted.eligible_lecturers] == [1, 2]
    assert [item.room_id for item in persisted.eligible_rooms] == [1, 2]

    scalar_attempt = client.patch(f"/api/academic/courses/{course['id']}", json={
        "name": "Scheduling renamed", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1, "expectedRevision": changed.json()["revision"],
    })
    assert scalar_attempt.status_code == 422


@pytest.mark.parametrize("payload", [
    {"name": "C", "totalUnits": 0, "minSessionUnits": 1, "maxSessionUnits": 1},
    {"name": "C", "totalUnits": 4, "minSessionUnits": 3, "maxSessionUnits": 2},
    {"name": "C", "totalUnits": 4, "minSessionUnits": 2, "maxSessionUnits": 5},
])
def test_course_numeric_and_relationship_validation(client, db_session, payload):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    response = client.post("/api/academic/courses", json={
        **payload, "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    })
    assert response.status_code == 422
    assert response.json()["errors"]


def test_course_validation_reports_numeric_and_relationship_corrections_together(client, db_session):
    seed_resources(db_session)
    response = client.post("/api/academic/courses", json={
        "name": "Broken", "totalUnits": 0, "minSessionUnits": 0, "maxSessionUnits": 5,
        "semesterId": 999, "cohortId": 999, "cohortCalendarId": 999,
        "lecturerId": 999, "roomId": 999,
    })

    assert response.status_code == 422
    assert {error["field"] for error in response.json()["errors"]} == {
        "totalUnits", "minSessionUnits", "semesterId", "cohortId", "lecturerId", "roomId",
    }


def test_course_semester_filter_is_applied_before_pagination(client, db_session):
    seed_resources(db_session)
    target, cohort, cohort_calendar, _ = create_academic_chain(client)
    other = client.post("/api/academic/semesters", json={
        "name": "Spring 2027", "startDate": "2027-01-01", "endDate": "2027-06-01",
    }).json()
    client.post("/api/academic/cohort-calendars", json={"cohortId":cohort["id"],"semesterId":other["id"],"startDate":"2027-01-01","endDate":"2027-06-01"})
    base = {
        "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    }
    for name, semester_id in (("A other", other["id"]), ("B target", target["id"]), ("C target", target["id"])):
        assert client.post("/api/academic/courses", json={**base, "name": name, "semesterId": semester_id}).status_code == 201

    first = client.get(f"/api/academic/courses?semesterId={target['id']}&pageSize=1&page=1")
    second = client.get(f"/api/academic/courses?semesterId={target['id']}&pageSize=1&page=2")

    assert first.json()["total"] == 2
    assert [item["name"] for item in first.json()["items"]] == ["B target"]
    assert [item["name"] for item in second.json()["items"]] == ["C target"]


def test_exact_window_duplicate_rejected_but_partial_overlap_allowed(client):
    _, _, cohort_calendar, _ = create_academic_chain(client)
    url = f"/api/academic/cohort-calendars/{cohort_calendar['id']}/time-windows"
    assert client.post(url, json={"weekday": 1, "startTime": "08:00", "endTime": "12:00", "sortOrder": 0}).status_code == 201
    assert client.post(url, json={"weekday": 1, "startTime": "08:00", "endTime": "12:00", "sortOrder": 1}).status_code == 409
    assert client.post(url, json={"weekday": 1, "startTime": "10:00", "endTime": "14:00", "sortOrder": 1}).status_code == 201


def test_nested_time_window_list_is_scoped_before_any_global_limit(client, db_session):
    semester, _, first, _ = create_academic_chain(client)
    cohort = client.post('/api/academic/cohorts',json={'name':'Second','studentCount':30}).json()
    target = client.post('/api/academic/cohort-calendars',json={'cohortId':cohort['id'],'semesterId':semester['id'],'startDate':'2026-09-01','endDate':'2026-12-20'}).json()
    db_session.add_all([
        CohortCalendarTimeWindow(
            cohort_calendar_id=first["id"], weekday=index % 7,
            start_time=time(0, index // 7), end_time=time(1, index // 7), sort_order=index,
        )
        for index in range(200)
    ])
    db_session.flush()
    target_window = CohortCalendarTimeWindow(
        cohort_calendar_id=target["id"], weekday=0, start_time=time(8), end_time=time(10), sort_order=0,
    )
    db_session.add(target_window)
    db_session.commit()

    response = client.get(f"/api/academic/cohort-calendars/{target['id']}/time-windows")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [target_window.id]


def test_course_creation_reports_missing_read_only_resources(client):
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    response = client.post("/api/academic/courses", json={
        "name": "C", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    })
    assert response.status_code == 422
    assert {error["field"] for error in response.json()["errors"]} == {"lecturerId", "roomId"}


def test_revisioned_edit_returns_canonical_record_and_stale_metadata(client, db_session):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    response = client.patch(f"/api/academic/cohorts/{cohort['id']}", json={
        "name": "AI 2026", "studentCount": 35, "expectedRevision": cohort["revision"],
    })
    assert response.status_code == 200
    assert response.json()["revision"] == 2
    assert response.json()["studentCount"] == 35

    stale = client.patch(f"/api/academic/cohorts/{cohort['id']}", json={
        "name": "Old edit", "studentCount": 20, "expectedRevision": 1,
    })
    assert stale.status_code == 409
    assert stale.json()["errors"][0]["code"] == "STALE_REVISION"
    assert stale.json()["errors"][0]["meta"]["currentRevision"] == 2


def test_usage_protects_referenced_records_and_unused_records_delete(client, db_session):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, _ = create_academic_chain(client)
    course = client.post("/api/academic/courses", json={
        "name": "Scheduling 101", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    }).json()
    usage = client.get(f"/api/academic/cohorts/{cohort['id']}/usage")
    assert usage.status_code == 200
    assert usage.json()["canDelete"] is False
    assert usage.json()["dependentRecords"] == [{"type": "course", "count": 1}, {"type":"cohort_calendar","count":1}]
    protected = client.delete(f"/api/academic/cohorts/{cohort['id']}?expectedRevision={cohort['revision']}")
    assert protected.status_code == 409
    assert protected.json()["errors"][0]["code"] == "DELETE_PROTECTED"

    deleted = client.delete(f"/api/academic/courses/{course['id']}?expectedRevision={course['revision']}")
    assert deleted.status_code == 204
    assert db_session.get(Course, course["id"]) is None


def test_usage_and_delete_cover_every_dependent_and_saved_schedule_blocker(client, db_session):
    seed_resources(db_session)
    semester, cohort, cohort_calendar, window = create_academic_chain(client)
    course = client.post("/api/academic/courses", json={
        "name": "Scheduling 101", "totalUnits": 8, "minSessionUnits": 2, "maxSessionUnits": 4,
        "semesterId": semester["id"], "cohortId": cohort["id"], "lecturerId": 1, "roomId": 1,
    }).json()
    selected_only_window = client.post(
        f"/api/academic/cohort-calendars/{cohort_calendar['id']}/time-windows",
        json={"weekday": 1, "startTime": "09:00", "endTime": "11:00", "sortOrder": 1},
    ).json()
    constraint = GenerationConstraintSet(
        course_id=course["id"], semester_id=semester["id"],
        planning_start_date=date(2026, 9, 1), planning_end_date=date(2026, 12, 20),
    )
    db_session.add(constraint)
    db_session.flush()
    db_session.add(GenerationConstraintWindow(
        constraint_set_id=constraint.id, source_time_window_id=window["id"],
        weekday=0, start_time=time(8), end_time=time(12), sort_order=0,
    ))
    draft = DraftSchedule(
        course_id=course["id"], semester_id=semester["id"], selected_time_window_id=selected_only_window["id"],
        course_name_snapshot="Scheduling 101", course_total_units_snapshot=8,
        course_min_session_units_snapshot=2, course_max_session_units_snapshot=4,
        cohort_id_snapshot=cohort["id"], cohort_name_snapshot="AI 1", cohort_size_snapshot=30,
        cohort_calendar_id_snapshot=cohort_calendar["id"], cohort_calendar_name_snapshot="Full-time",
        semester_name_snapshot="Fall 2026", semester_start_date_snapshot=date(2026, 9, 1),
        semester_end_date_snapshot=date(2026, 12, 20),
    )
    db_session.add(draft)
    db_session.flush()
    db_session.add_all([
        DraftSession(
            draft_schedule_id=draft.id, course_id=course["id"], lecturer_id=1, cohort_id=cohort["id"], room_id=1,
            date=date(2026, 9, 7), start_time=time(8), end_time=time(10), units=2,
            time_window_id=window["id"], constraint_window_index=0,
        ),
        DraftSession(
            draft_schedule_id=draft.id, course_id=course["id"], lecturer_id=1, cohort_id=cohort["id"], room_id=1,
            date=date(2026, 9, 14), start_time=time(8), end_time=time(10), units=2,
            time_window_id=window["id"], constraint_window_index=0,
        ),
    ])
    db_session.commit()

    expected = {
        ("semesters", semester["id"]): {"course", "generation_constraint_set", "cohort_calendar"},
        ("cohorts", cohort["id"]): {"course", "cohort_calendar"},
        ("courses", course["id"]): {"generation_constraint_set"},
        ("cohort-calendars", cohort_calendar["id"]): {"course", "time_window"},
        ("time-windows", window["id"]): {"generation_constraint_window"},
        ("time-windows", selected_only_window["id"]): set(),
    }
    revisions = {
        ("semesters", semester["id"]): semester["revision"],
        ("cohorts", cohort["id"]): cohort["revision"],
        ("courses", course["id"]): course["revision"],
        ("cohort-calendars", cohort_calendar["id"]): cohort_calendar["revision"],
        ("time-windows", window["id"]): window["revision"],
        ("time-windows", selected_only_window["id"]): selected_only_window["revision"],
    }
    for key, dependent_types in expected.items():
        resource, record_id = key
        usage = client.get(f"/api/academic/{resource}/{record_id}/usage").json()
        assert usage["canDelete"] is False
        assert usage["savedSchedules"]["count"] == 1
        assert {item["type"] for item in usage["dependentRecords"]} == dependent_types
        expected_kinds = {"saved_schedule"} | ({"dependent"} if dependent_types else set())
        assert {item["kind"] for item in usage["blockers"]} == expected_kinds
        response = client.delete(f"/api/academic/{resource}/{record_id}?expectedRevision={revisions[key]}")
        assert response.status_code == 409
        assert response.json()["errors"][0]["code"] == "DELETE_PROTECTED"

    next_semester = client.post("/api/academic/semesters", json={
        "name": "Spring 2027", "startDate": "2027-01-01", "endDate": "2027-06-01",
    }).json()
    client.post("/api/academic/cohort-calendars",json={"cohortId":cohort["id"],"semesterId":next_semester["id"],"startDate":"2027-01-01","endDate":"2027-06-01"})
    reassigned = client.patch(f"/api/academic/courses/{course['id']}", json={
        "name": "Scheduling 201", "totalUnits": 10, "minSessionUnits": 2, "maxSessionUnits": 5,
        "semesterId": next_semester["id"], "cohortId": cohort["id"], "expectedRevision": course["revision"],
    })
    assert reassigned.status_code == 200
    assert reassigned.json()["semester"]["id"] == next_semester["id"]
    db_session.expire_all()
    historical = db_session.get(DraftSchedule, draft.id)
    assert historical.semester_id == semester["id"]
    assert historical.course_name_snapshot == "Scheduling 101"
    assert historical.course_total_units_snapshot == 8

    blocked_dates = client.patch(f"/api/academic/semesters/{semester['id']}", json={
        "name": "Fall 2026", "startDate": "2026-10-01", "endDate": "2026-12-20",
        "expectedRevision": semester["revision"],
    })
    assert blocked_dates.status_code == 422
    assert blocked_dates.json()["errors"][0]["code"] == "SAVED_SESSION_OUTSIDE_SEMESTER"
    db_session.expire_all()
    assert historical.semester_start_date_snapshot == date(2026, 9, 1)


def test_archive_and_reactivate_are_revisioned_and_non_cascading(client, db_session):
    seed_resources(db_session)
    _, cohort, _, _ = create_academic_chain(client)
    archived = client.post(f"/api/academic/cohorts/{cohort['id']}/archive", json={"expectedRevision": 1})
    assert archived.status_code == 200
    assert archived.json()["isActive"] is False
    assert archived.json()["revision"] == 2
    active = client.post(f"/api/academic/cohorts/{cohort['id']}/reactivate", json={"expectedRevision": 2})
    assert active.status_code == 200
    assert active.json()["isActive"] is True
    assert active.json()["revision"] == 3
