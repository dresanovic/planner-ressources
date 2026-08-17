from __future__ import annotations

from copy import deepcopy
import importlib
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from icalendar import Calendar
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.db.session import get_db
from app.models.planning import (
    LecturerReviewActivityEvent,
    LecturerReviewLink,
    ScheduleRevision,
    Semester,
)
from app.services.lecturer_calendar_export import ASCII_FILENAME, calendar_filename
from tests.lecturer_calendar_fixtures import (
    CALENDAR_SOURCE_FINGERPRINT_KEY,
    remove_all_assignments,
    seed_lecturer_calendar_fixture,
)


app_main = importlib.import_module("app.main")
lecturer_review_service = importlib.import_module("app.services.lecturer_review")


@pytest.fixture()
def client_and_db(monkeypatch):
    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY",
        CALENDAR_SOURCE_FINGERPRINT_KEY,
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    db = Session(engine)
    app_main.app.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(app_main, "SessionLocal", lambda: Session(engine))
    try:
        with TestClient(app_main.app) as client:
            yield client, db
    finally:
        app_main.app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def _issue(client: TestClient, lecturer_id: int = 1) -> dict:
    response = client.post(
        "/api/schedule-revisions/2/lecturer-review-links",
        json={"lecturerId": lecturer_id},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _events(response) -> list:
    calendar = Calendar.from_ical(response.content)
    return [component for component in calendar.walk() if component.name == "VEVENT"]


def test_calendar_route_delivers_one_complete_bearer_scoped_ics(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={
            "Authorization": f"Bearer {issued['secret']}",
            "Accept": "text/calendar",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/calendar")
    assert len(_events(response)) == 9
    assert response.content.count(b"BEGIN:VCALENDAR") == 1
    assert b"Grace Hopper" not in response.content
    assert issued["secret"].encode() not in response.content


def test_calendar_route_delivers_a_valid_explicit_empty_calendar(client_and_db):
    client, db = client_and_db
    fixture = seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    remove_all_assignments(db, fixture.review.primary_lecturer_id)
    db.commit()

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 200, response.text
    assert _events(response) == []
    assert Calendar.from_ical(response.content).name == "VCALENDAR"


def test_calendar_route_accepts_no_client_scope_arguments(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)

    response = client.get(
        "/api/public/lecturer-review/calendar?course=course%3A1",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 404
    assert "text/calendar" not in response.headers.get("content-type", "")
    assert b"VCALENDAR" not in response.content


def test_calendar_route_rejects_a_non_empty_request_body(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)

    response = client.request(
        "GET",
        "/api/public/lecturer-review/calendar",
        headers={
            "Authorization": f"Bearer {issued['secret']}",
            "Content-Type": "application/json",
        },
        content=b'{"course":999}',
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable.",
    }
    assert "content-disposition" not in response.headers
    assert b"VCALENDAR" not in response.content


def test_calendar_route_never_crosses_lecturer_scope(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    first = _issue(client, lecturer_id=1)
    second = _issue(client, lecturer_id=2)

    first_response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {first['secret']}"},
    )
    second_response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {second['secret']}"},
    )

    assert first_response.status_code == second_response.status_code == 200
    assert len(_events(first_response)) == 9
    assert len(_events(second_response)) == 6
    assert first_response.content != second_response.content


def test_calendar_success_has_exact_media_attachment_and_privacy_headers(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    semester = db.get(Semester, 1)
    assert semester is not None
    semester.name = "Wïnter / 2026"
    db.commit()
    issued = _issue(client)

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    filename = calendar_filename("Terminplanung", semester.name, "Revision 2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{ASCII_FILENAME}"; filename*=UTF-8\'\'{quote(filename, safe="")}'
    )
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_calendar_success_exposes_filename_to_allowed_cross_origin_client(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={
            "Authorization": f"Bearer {issued['secret']}",
            "Origin": "http://localhost:5173",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:5173"
    )
    exposed_headers = {
        value.strip().lower()
        for value in response.headers["access-control-expose-headers"].split(",")
    }
    assert "content-disposition" in exposed_headers


@pytest.mark.parametrize("authorization", [None, "Bearer malformed", "Basic abc"])
def test_calendar_failure_never_returns_calendar_bytes_or_attachment_metadata(
    client_and_db, authorization
):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    headers = {} if authorization is None else {"Authorization": authorization}

    response = client.get("/api/public/lecturer-review/calendar", headers=headers)

    assert response.status_code == 404
    assert "content-disposition" not in response.headers
    assert "x-content-type-options" not in response.headers
    assert response.headers["content-type"].startswith("application/json")
    assert b"VCALENDAR" not in response.content


@pytest.mark.parametrize(
    "case",
    ["expired", "revoked", "replaced", "abandoned", "superseded", "malformed", "unknown"],
)
def test_calendar_lifecycle_and_bearer_failures_are_indistinguishable_and_non_mutating(
    client_and_db, case
):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    link = db.get(LecturerReviewLink, issued["issuedLink"]["id"])
    assert link is not None
    revision = db.get(ScheduleRevision, link.schedule_revision_id)
    assert revision is not None
    if case == "expired":
        link.issued_at = datetime.now(timezone.utc) - timedelta(days=4)
        link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    elif case == "revoked":
        response = client.post(f"/api/lecturer-review-links/{link.id}/revoke")
        assert response.status_code == 200
    elif case == "replaced":
        response = client.post(
            f"/api/lecturer-review-links/{link.id}/replace",
            json={"durationDays": 3},
        )
        assert response.status_code == 201
    elif case in {"abandoned", "superseded"}:
        revision.state = case
        revision.snapshot_schema_version = 1
        revision.snapshot_document = {"courses": [], "examSessions": []}
        revision.published_at = (
            datetime.now(timezone.utc) if case == "superseded" else None
        )
    db.commit()
    db.expire_all()
    link = db.get(LecturerReviewLink, issued["issuedLink"]["id"])
    assert link is not None
    bearer = (
        "malformed"
        if case == "malformed"
        else "A" * 43
        if case == "unknown"
        else issued["secret"]
    )
    before = (
        link.status,
        link.ended_at,
        link.end_reason,
        link.access_blocked_until,
        db.query(LecturerReviewActivityEvent).count(),
    )

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {bearer}"},
    )

    db.expire_all()
    stored = db.get(LecturerReviewLink, link.id)
    assert response.status_code == 404
    assert response.json() == {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable.",
    }
    assert "content-disposition" not in response.headers
    assert b"VCALENDAR" not in response.content
    assert stored is not None
    assert (
        stored.status,
        stored.ended_at,
        stored.end_reason,
        stored.access_blocked_until,
        db.query(LecturerReviewActivityEvent).count(),
    ) == before


def test_calendar_rejects_exactly_at_expiry_but_succeeds_immediately_before(
    client_and_db, monkeypatch
):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    link = db.get(LecturerReviewLink, issued["issuedLink"]["id"])
    assert link is not None
    expires_at = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    link.expires_at = expires_at
    db.commit()

    monkeypatch.setattr(
        lecturer_review_service,
        "_now",
        lambda _clock: expires_at - timedelta(microseconds=1),
    )
    before = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    monkeypatch.setattr(
        lecturer_review_service,
        "_now",
        lambda _clock: expires_at,
    )
    at_expiry = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert before.status_code == 200
    assert at_expiry.status_code == 404
    assert at_expiry.json() == {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable.",
    }


def test_incomplete_published_projection_returns_safe_retryable_no_file(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    link = db.query(LecturerReviewLink).one()
    revision = db.query(ScheduleRevision).filter_by(state="published").one()
    link.schedule_revision_id = revision.id
    revision.snapshot_document = {"examSessions": []}
    db.commit()

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "code": "CALENDAR_EXPORT_UNAVAILABLE",
        "message": "Calendar download is temporarily unavailable. Try again.",
    }
    assert "content-disposition" not in response.headers
    assert "text/calendar" not in response.headers["content-type"]
    assert b"VCALENDAR" not in response.content


@pytest.mark.parametrize(
    "snapshot",
    [
        {
            "courses": [
                {"sourceCourseId": 1, "teachingSessions": [None]},
            ],
            "examSessions": [],
        },
        {
            "courses": [],
            "examSessions": [{"lecturer": None}],
        },
    ],
)
def test_nested_corrupt_published_projection_returns_safe_retryable_no_file(
    client_and_db, snapshot
):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    link = db.query(LecturerReviewLink).one()
    revision = db.query(ScheduleRevision).filter_by(state="published").one()
    link.schedule_revision_id = revision.id
    revision.snapshot_document = snapshot
    db.commit()

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "code": "CALENDAR_EXPORT_UNAVAILABLE",
        "message": "Calendar download is temporarily unavailable. Try again.",
    }
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "content-disposition" not in response.headers
    assert "text/calendar" not in response.headers["content-type"]
    assert b"VCALENDAR" not in response.content


def test_exam_only_course_with_corrupt_metadata_returns_safe_retryable_no_file(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    link = db.query(LecturerReviewLink).one()
    revision = db.query(ScheduleRevision).filter_by(state="published").one()
    link.schedule_revision_id = revision.id
    snapshot = deepcopy(revision.snapshot_document)
    snapshot["courses"][0]["studyType"] = []
    snapshot["courses"][0]["teachingSessions"][0]["lecturer"]["sourceId"] = 2
    revision.snapshot_document = snapshot
    db.commit()

    response = client.get(
        "/api/public/lecturer-review/calendar",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 503
    assert response.json() == {
        "code": "CALENDAR_EXPORT_UNAVAILABLE",
        "message": "Calendar download is temporarily unavailable. Try again.",
    }
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "content-disposition" not in response.headers
    assert "text/calendar" not in response.headers["content-type"]
    assert b"VCALENDAR" not in response.content


def test_runtime_openapi_uses_the_calendar_specific_404_schema():
    response_schema = (
        app_main.app.openapi()["paths"]["/api/public/lecturer-review/calendar"]
        ["get"]["responses"]["404"]["content"]["application/json"]["schema"]
    )

    assert response_schema == {
        "$ref": "#/components/schemas/PublicCalendarUnavailableError"
    }


def test_unchanged_repeat_requests_have_identical_bytes_filename_and_safe_disposition(client_and_db):
    client, db = client_and_db
    seed_lecturer_calendar_fixture(db)
    issued = _issue(client)
    headers = {"Authorization": f"Bearer {issued['secret']}"}

    responses = [
        client.get("/api/public/lecturer-review/calendar", headers=headers)
        for _ in range(3)
    ]

    assert all(response.status_code == 200 for response in responses)
    assert len({response.content for response in responses}) == 1
    dispositions = {response.headers["content-disposition"] for response in responses}
    assert len(dispositions) == 1
    disposition = dispositions.pop()
    assert issued["secret"] not in disposition
    assert "Ada" not in disposition
