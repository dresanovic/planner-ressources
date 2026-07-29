from __future__ import annotations

import asyncio
import hashlib
import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.db.session import get_db
from app.models.planning import (
    DraftSession,
    LecturerReviewActivityEvent,
    LecturerReviewFeedback,
    LecturerReviewInvalidSourceState,
    LecturerReviewLink,
    ScheduleRevision,
)
from tests.lecturer_review_fixtures import (
    DeterministicUtcClock,
    FIXED_UTC,
    seed_lecturer_review_fixture,
)


app_main = importlib.import_module("app.main")
if not any(
    "lecturer-review" in getattr(route, "path", "")
    for route in app_main.app.routes
):
    app_main = importlib.reload(app_main)


SOURCE_FINGERPRINT_KEY = "fs015-test-source-fingerprint-key-" + ("a" * 32)
PUBLIC_HEADERS = {
    "cache-control": "no-store",
    "pragma": "no-cache",
    "referrer-policy": "no-referrer",
    "x-robots-tag": "noindex, nofollow",
}


@pytest.fixture()
def client_and_db(monkeypatch):
    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY", SOURCE_FINGERPRINT_KEY
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    with Session(engine) as db:
        app_main.app.dependency_overrides[get_db] = lambda: db
        with TestClient(app_main.app, client=("198.51.100.7", 43000)) as client:
            yield client, db
        app_main.app.dependency_overrides.clear()


def _assert_public_headers(response) -> None:
    for name, expected in PUBLIC_HEADERS.items():
        assert response.headers[name] == expected


def _install_api_clock(monkeypatch, clock: DeterministicUtcClock) -> None:
    api = importlib.import_module("app.api.lecturer_review")
    service = importlib.import_module("app.services.lecturer_review")
    for name in (
        "get_lecturer_review_overview",
        "get_public_lecturer_review",
        "issue_lecturer_review_link",
        "replace_lecturer_review_link",
        "reject_invalid_feedback_attempt",
        "revoke_lecturer_review_link",
        "submit_lecturer_review_feedback",
    ):
        original = getattr(service, name)

        def with_clock(*args, _original=original, **kwargs):
            kwargs["clock"] = clock
            return _original(*args, **kwargs)

        monkeypatch.setattr(api, name, with_clock)


def test_public_feedback_keeps_sync_database_work_off_the_event_loop():
    api = importlib.import_module("app.api.lecturer_review")

    assert inspect.iscoroutinefunction(api._parse_feedback_payload)
    assert not inspect.iscoroutinefunction(api.submit_public_lecturer_feedback)


def test_privacy_cleanup_loop_runs_immediately_and_compensates_for_work_time(
    monkeypatch,
):
    cleanup_calls: list[object] = []
    commits: list[object] = []
    sleeps: list[float] = []
    times = iter([100.0, 103.0])

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def commit(self):
            commits.append(self)

    class StopCleanupLoop(RuntimeError):
        pass

    async def stop_after_first_sleep(delay: float):
        sleeps.append(delay)
        raise StopCleanupLoop

    monkeypatch.setattr(app_main, "SessionLocal", FakeSession)
    monkeypatch.setattr(
        app_main,
        "cleanup_invalid_source_states",
        lambda db: cleanup_calls.append(db),
    )
    monkeypatch.setattr(app_main, "monotonic", lambda: next(times), raising=False)
    monkeypatch.setattr(app_main.asyncio, "sleep", stop_after_first_sleep)

    with pytest.raises(StopCleanupLoop):
        asyncio.run(app_main._cleanup_lecturer_review_source_state())

    assert len(cleanup_calls) == 1
    assert len(commits) == 1
    assert sleeps == [pytest.approx(27.0)]


@pytest.fixture()
def persistent_api(tmp_path: Path, monkeypatch):
    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY", SOURCE_FINGERPRINT_KEY
    )
    engine = create_engine(
        f"sqlite:///{tmp_path / 'lecturer-review-api.db'}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )
    initialize_database(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with session_factory() as db:
            yield db

    app_main.app.dependency_overrides[get_db] = override_db
    try:
        yield engine
    finally:
        app_main.app.dependency_overrides.clear()
        engine.dispose()


def _issue_link(client: TestClient, *, revision_id: int = 2, lecturer_id: int = 1):
    response = client.post(
        f"/api/schedule-revisions/{revision_id}/lecturer-review-links",
        json={"lecturerId": lecturer_id},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _submit_feedback(
    client: TestClient,
    secret: str,
    *,
    submission_number: int,
    kind: str,
    session_ref: str | None = None,
    comment: str | None = None,
) -> dict:
    payload = {
        "clientSubmissionId": (
            f"00000000-0000-0000-0000-{submission_number:012d}"
        ),
        "kind": kind,
    }
    if session_ref is not None:
        payload["sessionRef"] = session_ref
    if comment is not None:
        payload["comment"] = comment
    response = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {secret}"},
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()["item"]


def test_planner_overview_and_issue_reveal_secret_once_without_persisting_it(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)

    empty = client.get("/api/schedule-revisions/2/lecturer-review")
    assert empty.status_code == 200
    assert empty.json()["revision"]["state"] == "draft"
    assert empty.json()["links"] == []

    issued = _issue_link(client)
    secret = issued["secret"]
    assert len(secret) == 43
    assert issued["issuedLink"]["durationDays"] == 3
    issued_at = datetime.fromisoformat(
        issued["issuedLink"]["issuedAt"].replace("Z", "+00:00")
    )
    expires_at = datetime.fromisoformat(
        issued["issuedLink"]["expiresAt"].replace("Z", "+00:00")
    )
    assert (expires_at - issued_at).total_seconds() == 3 * 24 * 60 * 60
    assert issued["overview"]["links"][0]["id"] == issued["issuedLink"]["id"]

    stored = db.scalar(select(LecturerReviewLink))
    assert stored is not None
    assert secret not in repr(stored.__dict__)
    assert stored.secret_digest != secret

    overview = client.get("/api/schedule-revisions/2/lecturer-review").json()
    assert "secret" not in str(overview).lower()
    assert overview["links"][0]["id"] == issued["issuedLink"]["id"]


def test_public_contract_has_exactly_two_operations_and_uses_bearer_header(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)

    document = client.get("/openapi.json").json()
    public_paths = {
        path: sorted(document["paths"][path])
        for path in document["paths"]
        if path.startswith("/api/public/lecturer-review")
    }
    assert public_paths == {
        "/api/public/lecturer-review": ["get"],
        "/api/public/lecturer-review/feedback": ["post"],
    }

    missing = client.get("/api/public/lecturer-review")
    assert missing.status_code == 404
    _assert_public_headers(missing)

    query_transport = client.get(
        f"/api/public/lecturer-review?token={issued['secret']}"
    )
    assert query_transport.status_code == 404
    _assert_public_headers(query_transport)

    response = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )
    assert response.status_code == 200, response.text
    _assert_public_headers(response)


def test_public_projection_is_complete_and_minimum_scope(client_and_db):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)

    response = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "intendedLecturer",
        "identityDisclaimer",
        "revision",
        "accessExpiresAt",
        "timeZone",
        "courses",
        "submittedFeedback",
    }
    assert payload["intendedLecturer"] == "Ada Lovelace"
    assert {course["sourceCourseId"] for course in payload["courses"]} == {1, 2}
    session_refs = {
        session["sessionRef"]
        for course in payload["courses"]
        for session in course["sessions"]
    }
    assert session_refs == {
        "teaching:101",
        "teaching:102",
        "teaching:201",
        "exam:401",
    }
    serialized = str(payload).casefold()
    for forbidden in (
        "grace hopper",
        "katherine johnson",
        "referencecode",
        "student",
        "planner",
        "validationalerts",
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        "",
        "Bearer",
        "Bearer short",
        "Basic Zm9vOmJhcg==",
        "Bearer " + ("x" * 43),
    ],
)
def test_every_unusable_credential_returns_identical_safe_response(
    client_and_db, authorization
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    headers = {} if authorization is None else {"Authorization": authorization}

    response = client.get("/api/public/lecturer-review", headers=headers)

    assert response.status_code == 404
    assert response.json() == {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable. Contact the planner for a new link.",
    }
    _assert_public_headers(response)


def test_request_client_host_is_used_and_forwarding_headers_cannot_change_bucket(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)

    for spoofed in ("203.0.113.1", "203.0.113.2"):
        response = client.get(
            "/api/public/lecturer-review",
            headers={
                "Authorization": "Bearer " + ("x" * 43),
                "Forwarded": f"for={spoofed}",
                "X-Forwarded-For": spoofed,
            },
        )
        assert response.status_code == 404

    states = list(db.scalars(select(LecturerReviewInvalidSourceState)))
    assert len(states) == 1
    assert states[0].source_fingerprint not in {
        "198.51.100.7",
        "203.0.113.1",
        "203.0.113.2",
    }
    assert len(states[0].attempt_timestamps) == 2


@pytest.mark.parametrize("configured_key", [None, "", "too-short"])
def test_source_fingerprint_key_requires_256_bit_configuration(
    monkeypatch, configured_key
):
    if configured_key is None:
        monkeypatch.delenv("LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY", raising=False)
    else:
        monkeypatch.setenv(
            "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY", configured_key
        )
    service = importlib.import_module("app.services.lecturer_review")

    with pytest.raises(RuntimeError, match="256"):
        service.source_fingerprint_key_from_environment(production=True)


def test_valid_long_key_is_accepted_without_exposing_it(monkeypatch):
    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY", SOURCE_FINGERPRINT_KEY
    )
    service = importlib.import_module("app.services.lecturer_review")

    configured = service.source_fingerprint_key_from_environment(production=True)

    assert isinstance(configured, bytes)
    assert len(configured) >= 32
    assert SOURCE_FINGERPRINT_KEY not in repr(configured)


@pytest.mark.parametrize(
    ("payload", "expected_kind", "expected_session_ref"),
    [
        (
            {
                "clientSubmissionId": "00000000-0000-0000-0000-000000000301",
                "kind": "revision_comment",
                "comment": "The plan is workable.",
            },
            "revision_comment",
            None,
        ),
        (
            {
                "clientSubmissionId": "00000000-0000-0000-0000-000000000302",
                "kind": "session_comment",
                "sessionRef": "teaching:101",
                "comment": "Please schedule this after 10:00.",
            },
            "session_comment",
            "teaching:101",
        ),
        (
            {
                "clientSubmissionId": "00000000-0000-0000-0000-000000000303",
                "kind": "impossible_session",
                "sessionRef": "exam:401",
            },
            "impossible_session",
            "exam:401",
        ),
    ],
)
def test_feedback_endpoint_accepts_every_kind_with_public_headers(
    client_and_db, payload, expected_kind, expected_session_ref
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)

    response = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {issued['secret']}"},
        json=payload,
    )

    assert response.status_code == 201, response.text
    _assert_public_headers(response)
    assert response.json()["outcome"] == "created"
    assert response.json()["item"]["kind"] == expected_kind
    assert response.json()["item"]["sessionRef"] == expected_session_ref
    assert db.query(LecturerReviewFeedback).count() == 1


@pytest.mark.parametrize(
    "comment",
    ["", " \t\n ", "x" * 2001],
)
def test_feedback_endpoint_rejects_invalid_comment_without_partial_item(
    client_and_db, comment
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)

    response = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {issued['secret']}"},
        json={
            "clientSubmissionId": "00000000-0000-0000-0000-000000000310",
            "kind": "revision_comment",
            "comment": comment,
        },
    )

    assert response.status_code == 422
    _assert_public_headers(response)
    assert response.json()["code"] == "INVALID_FEEDBACK"
    assert db.query(LecturerReviewFeedback).count() == 0


def test_feedback_endpoint_returns_created_then_idempotently_accepted(client_and_db):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)
    payload = {
        "clientSubmissionId": "00000000-0000-0000-0000-000000000320",
        "kind": "session_comment",
        "sessionRef": "teaching:101",
        "comment": "One logical request.",
    }

    created = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {issued['secret']}"},
        json=payload,
    )
    replayed = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {issued['secret']}"},
        json=payload,
    )

    assert created.status_code == 201
    assert created.json()["outcome"] == "created"
    assert replayed.status_code == 200
    assert replayed.json()["outcome"] == "already_accepted"
    assert replayed.json()["item"]["id"] == created.json()["item"]["id"]
    _assert_public_headers(created)
    _assert_public_headers(replayed)
    assert db.query(LecturerReviewFeedback).count() == 1


def test_idempotent_feedback_replays_are_counted_by_the_feedback_limiter(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)
    payload = {
        "clientSubmissionId": "00000000-0000-0000-0000-000000000321",
        "kind": "session_comment",
        "sessionRef": "teaching:101",
        "comment": "One logical request.",
    }
    headers = {"Authorization": f"Bearer {issued['secret']}"}

    responses = [
        client.post(
            "/api/public/lecturer-review/feedback",
            headers=headers,
            json=payload,
        )
        for _ in range(11)
    ]

    assert [response.status_code for response in responses[:10]] == [201] + [200] * 9
    assert responses[10].status_code == 429
    assert db.query(LecturerReviewFeedback).count() == 1


def test_schema_invalid_feedback_attempts_are_counted_by_the_feedback_limiter(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)
    headers = {"Authorization": f"Bearer {issued['secret']}"}
    invalid_payload = {
        "clientSubmissionId": "00000000-0000-0000-0000-000000000322",
        "kind": "revision_comment",
    }

    responses = [
        client.post(
            "/api/public/lecturer-review/feedback",
            headers=headers,
            json=invalid_payload,
        )
        for _ in range(11)
    ]

    assert [response.status_code for response in responses[:10]] == [422] * 10
    assert responses[10].status_code == 429
    assert db.query(LecturerReviewFeedback).count() == 0
    assert (
        db.query(LecturerReviewActivityEvent)
        .filter_by(event_type="feedback_rejected", reason_code="invalid_feedback")
        .count()
        == 10
    )


def test_malformed_json_feedback_is_safely_rejected_and_audited(client_and_db):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)

    response = client.post(
        "/api/public/lecturer-review/feedback",
        headers={
            "Authorization": f"Bearer {issued['secret']}",
            "Content-Type": "application/json",
        },
        content="{",
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_FEEDBACK"
    assert (
        db.query(LecturerReviewActivityEvent)
        .filter_by(event_type="feedback_rejected", reason_code="invalid_feedback")
        .count()
        == 1
    )
def test_feedback_endpoint_preserves_markup_as_literal_text(client_and_db):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)
    markup = "<script>alert('inert')</script>"

    submitted = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {issued['secret']}"},
        json={
            "clientSubmissionId": "00000000-0000-0000-0000-000000000330",
            "kind": "revision_comment",
            "comment": markup,
        },
    )
    reopened = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert submitted.status_code == 201
    assert submitted.json()["item"]["comment"] == markup
    assert reopened.json()["submittedFeedback"][0]["comment"] == markup
    assert db.scalar(select(LecturerReviewFeedback)).comment_text == markup


def test_planner_revoke_route_returns_history_and_generic_public_failure(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)
    link_id = issued["issuedLink"]["id"]

    revoked = client.post(f"/api/lecturer-review-links/{link_id}/revoke")
    ended = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["links"][0]["status"] == "revoked"
    assert ended.status_code == 404
    assert ended.json() == {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable. Contact the planner for a new link.",
    }
    _assert_public_headers(ended)
    assert db.scalar(select(LecturerReviewLink)).status == "revoked"


def test_planner_replace_route_defaults_duration_and_invalidates_old_secret(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)
    link_id = issued["issuedLink"]["id"]

    replaced = client.post(
        f"/api/lecturer-review-links/{link_id}/replace",
        json={},
    )
    old = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert replaced.status_code == 201, replaced.text
    assert replaced.json()["issuedLink"]["durationDays"] == 3
    assert replaced.json()["secret"] != issued["secret"]
    assert old.status_code == 404
    _assert_public_headers(old)
    current = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {replaced.json()['secret']}"},
    )
    assert current.status_code == 200
    links = db.scalars(
        select(LecturerReviewLink).order_by(LecturerReviewLink.id)
    ).all()
    assert [link.status for link in links] == ["replaced", "active"]


def test_planner_overview_groups_retained_feedback_with_exact_flag_counts(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    primary = _issue_link(client, lecturer_id=1)
    second = _issue_link(client, lecturer_id=2)

    primary_items = [
        _submit_feedback(
            client,
            primary["secret"],
            submission_number=401,
            kind="revision_comment",
            comment="The overall sequence is workable.",
        ),
        _submit_feedback(
            client,
            primary["secret"],
            submission_number=402,
            kind="impossible_session",
            session_ref="teaching:101",
            comment="Not possible on Monday.",
        ),
        _submit_feedback(
            client,
            primary["secret"],
            submission_number=403,
            kind="impossible_session",
            session_ref="teaching:101",
            comment="Still not possible at this time.",
        ),
        _submit_feedback(
            client,
            primary["secret"],
            submission_number=404,
            kind="session_comment",
            session_ref="teaching:101",
            comment="Wednesday after 10:00 would work.",
        ),
        _submit_feedback(
            client,
            primary["secret"],
            submission_number=405,
            kind="impossible_session",
            session_ref="exam:401",
        ),
        _submit_feedback(
            client,
            primary["secret"],
            submission_number=406,
            kind="session_comment",
            session_ref="teaching:102",
            comment="Please retain the original context.",
        ),
    ]
    second_items = [
        _submit_feedback(
            client,
            second["secret"],
            submission_number=407,
            kind="revision_comment",
            comment="The second lecturer's review.",
        ),
        _submit_feedback(
            client,
            second["secret"],
            submission_number=408,
            kind="impossible_session",
            session_ref="teaching:301",
        ),
    ]

    reassigned = db.get(DraftSession, 102)
    assert reassigned is not None
    reassigned.lecturer_id = 2
    db.commit()
    revoked = client.post(
        f"/api/lecturer-review-links/{primary['issuedLink']['id']}/revoke"
    )
    assert revoked.status_code == 200, revoked.text

    response = client.get("/api/schedule-revisions/2/lecturer-review")

    assert response.status_code == 200, response.text
    overview = response.json()
    assert overview["feedbackAvailability"] == "complete"
    assert overview["totalFeedbackCount"] == 8
    assert overview["impossibleFlagCount"] == 4
    groups = {group["groupRef"]: group for group in overview["feedbackGroups"]}
    assert set(groups) == {
        "revision",
        "teaching:101",
        "teaching:102",
        "teaching:301",
        "exam:401",
    }
    assert {
        group_ref
        for group_ref, group in groups.items()
        if group["impossibleFlagCount"] > 0
    } == {"teaching:101", "teaching:301", "exam:401"}
    assert groups["teaching:101"]["impossibleFlagCount"] == 2
    assert groups["revision"]["level"] == "revision"
    assert groups["revision"]["sessionContext"] is None
    assert groups["revision"]["currentNavigation"] is None

    revision_items = groups["revision"]["items"]
    assert {
        (item["intendedLecturerId"], item["intendedLecturerName"])
        for item in revision_items
    } == {(1, "Ada Lovelace"), (2, "Grace Hopper")}
    for item in revision_items:
        assert "intended for" in item["attribution"]
        assert "identity was not authenticated" in item["attribution"]

    retained = groups["teaching:102"]
    assert retained["sessionContext"] == {
        "sessionRef": "teaching:102",
        "sessionKind": "teaching",
        "sourceSessionId": 102,
        "sessionType": "Lecture",
        "courseSourceId": 1,
        "courseCode": "COURSE-1",
        "courseTitle": "Analytical Methods",
        "date": "2026-09-28",
        "startTime": "09:00",
        "endTime": "11:00",
        "timeZone": "Europe/Vienna",
        "roomName": "Room 101",
        "cohortName": "Cohort 1",
    }
    assert retained["currentNavigation"] is None
    for group_ref in ("teaching:101", "teaching:301", "exam:401"):
        assert groups[group_ref]["currentNavigation"] == {
            "revisionId": 2,
            "occurrenceRef": group_ref,
        }

    retained_item_ids = {
        item["id"] for group in groups.values() for item in group["items"]
    }
    assert retained_item_ids == {
        item["id"] for item in [*primary_items, *second_items]
    }
    link_statuses = {
        link["lecturerId"]: link["status"] for link in overview["links"]
    }
    assert link_statuses == {1: "revoked", 2: "active"}


def test_complete_planner_overview_reports_definitive_zero_feedback(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)

    response = client.get("/api/schedule-revisions/2/lecturer-review")

    assert response.status_code == 200
    overview = response.json()
    assert overview["feedbackAvailability"] == "complete"
    assert overview["totalFeedbackCount"] == 0
    assert overview["impossibleFlagCount"] == 0
    assert overview["feedbackGroups"] == []


@pytest.mark.parametrize("availability", ["partial", "unavailable"])
def test_incomplete_planner_overview_never_reports_definitive_counts(
    client_and_db,
    monkeypatch,
    availability,
):
    client, _db = client_and_db
    api = importlib.import_module("app.api.lecturer_review")
    monkeypatch.setattr(
        api,
        "get_lecturer_review_overview",
        lambda _db, revision_id: {
            "revision": {
                "id": revision_id,
                "semesterId": 1,
                "semesterName": "Autumn 2026",
                "label": "Revision 2",
                "state": "draft",
            },
            "lecturers": [],
            "links": [],
            "feedbackAvailability": availability,
            "totalFeedbackCount": None,
            "impossibleFlagCount": None,
            "feedbackGroups": [],
        },
    )

    response = client.get("/api/schedule-revisions/2/lecturer-review")

    assert response.status_code == 200, response.text
    overview = response.json()
    assert overview["feedbackAvailability"] == availability
    assert overview["totalFeedbackCount"] is None
    assert overview["impossibleFlagCount"] is None


def test_public_failure_equivalence_activity_evidence_and_privacy_canaries(
    client_and_db,
    monkeypatch,
):
    client, db = client_and_db
    fixture = seed_lecturer_review_fixture(db)
    clock = DeterministicUtcClock()
    _install_api_clock(monkeypatch, clock)
    service = importlib.import_module("app.services.lecturer_review")

    revoked = _issue_link(client)
    revoked_secret = revoked["secret"]
    revoked_link_id = revoked["issuedLink"]["id"]
    assert client.post(
        f"/api/lecturer-review-links/{revoked_link_id}/revoke"
    ).status_code == 200

    expired = _issue_link(client)
    expired_secret = expired["secret"]
    clock.advance(days=3)
    expired_response = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {expired_secret}"},
    )

    replaceable = _issue_link(client)
    replaced_secret = replaceable["secret"]
    replaced = client.post(
        f"/api/lecturer-review-links/{replaceable['issuedLink']['id']}/replace",
        json={"durationDays": 3},
    )
    assert replaced.status_code == 201
    replaced_active_secret = replaced.json()["secret"]

    active_link = db.scalar(
        select(LecturerReviewLink).where(
            LecturerReviewLink.secret_digest
            == hashlib.sha256(replaced_active_secret.encode("ascii")).hexdigest()
        )
    )
    assert active_link is not None
    service.terminalize_revision_links(
        db,
        fixture.working_revision_id,
        reason="abandoned",
        clock=clock,
    )
    db.commit()
    abandoned_secret = replaced_active_secret

    superseded = _issue_link(client)
    superseded_secret = superseded["secret"]
    service.terminalize_revision_links(
        db,
        fixture.working_revision_id,
        reason="superseded",
        clock=clock,
    )
    db.commit()

    accepted = _issue_link(client)
    accepted_secret = accepted["secret"]
    successful_view = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {accepted_secret}"},
    )
    assert successful_view.status_code == 200
    comment_canary = "COMMENT-CANARY-FR059-7b9d20"
    accepted_feedback = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {accepted_secret}"},
        json={
            "clientSubmissionId": "00000000-0000-0000-0000-000000059001",
            "kind": "session_comment",
            "sessionRef": "teaching:101",
            "comment": comment_canary,
        },
    )
    assert accepted_feedback.status_code == 201
    rejected_feedback = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {accepted_secret}"},
        json={
            "clientSubmissionId": "00000000-0000-0000-0000-000000059002",
            "kind": "session_comment",
            "sessionRef": "teaching:301",
            "comment": "OUT-OF-SCOPE-COMMENT-CANARY",
        },
    )
    assert rejected_feedback.status_code == 409

    generic_body = {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable. Contact the planner for a new link.",
    }
    cases = {
        "missing": None,
        "malformed": "short",
        "unknown": "u" * 43,
        "expired": expired_secret,
        "revoked": revoked_secret,
        "replaced": replaced_secret,
        "abandoned": abandoned_secret,
        "superseded": superseded_secret,
    }
    responses = {}
    for name, secret in cases.items():
        headers = {} if secret is None else {"Authorization": f"Bearer {secret}"}
        response = (
            expired_response
            if name == "expired"
            else client.get("/api/public/lecturer-review", headers=headers)
        )
        responses[name] = (
            response.status_code,
            response.json(),
            {header: response.headers[header] for header in PUBLIC_HEADERS},
        )
        assert response.status_code == 404
        assert response.json() == generic_body
        _assert_public_headers(response)
        serialized = response.text.casefold()
        assert "ada lovelace" not in serialized
        assert "analytical methods" not in serialized

    assert len(set(str(item) for item in responses.values())) == 1

    for _attempt in range(18):
        response = client.get(
            "/api/public/lecturer-review",
            headers={"Authorization": "Bearer " + ("z" * 43)},
        )
        assert response.status_code == 404

    db.expire_all()
    events = list(
        db.scalars(
            select(LecturerReviewActivityEvent).order_by(
                LecturerReviewActivityEvent.occurred_at,
                LecturerReviewActivityEvent.id,
            )
        )
    )
    assert {event.event_type for event in events} == {
        "link_issued",
        "link_expired",
        "link_revoked",
        "link_replaced",
        "revision_ended",
        "access_accepted",
        "access_rejected",
        "feedback_accepted",
        "feedback_rejected",
        "misuse_limit_activated",
    }
    assert [event.occurred_at for event in events] == sorted(
        event.occurred_at for event in events
    )
    assert set(LecturerReviewActivityEvent.__table__.columns.keys()) == {
        "id",
        "event_type",
        "review_link_id",
        "schedule_revision_id",
        "lecturer_id",
        "feedback_id",
        "reason_code",
        "occurred_at",
    }
    activity_text = repr(
        [
            {
                column.name: getattr(event, column.name)
                for column in LecturerReviewActivityEvent.__table__.columns
            }
            for event in events
        ]
    )
    source_state = db.scalar(select(LecturerReviewInvalidSourceState))
    assert source_state is not None
    for forbidden in (
        revoked_secret,
        expired_secret,
        replaced_secret,
        abandoned_secret,
        superseded_secret,
        accepted_secret,
        comment_canary,
        "OUT-OF-SCOPE-COMMENT-CANARY",
        "198.51.100.7",
        source_state.source_fingerprint,
    ):
        assert forbidden not in activity_text


def test_exact_source_boundary_valid_request_21_and_source_state_retention(
    client_and_db,
    monkeypatch,
):
    client, db = client_and_db
    fixture = seed_lecturer_review_fixture(db)
    clock = DeterministicUtcClock()
    _install_api_clock(monkeypatch, clock)
    service = importlib.import_module("app.services.lecturer_review")
    issued = _issue_link(client)
    secret = issued["secret"]
    link = db.get(LecturerReviewLink, issued["issuedLink"]["id"])
    assert link is not None
    original_expiry = link.expires_at
    original_revision_state = db.get(
        ScheduleRevision, fixture.working_revision_id
    ).state
    original_session_count = db.query(DraftSession).count()

    for attempt in range(1, 21):
        response = client.get(
            "/api/public/lecturer-review",
            headers={
                "Authorization": "Bearer " + ("i" * 42) + chr(64 + attempt)
            },
        )
        assert response.status_code == 404
        assert response.json()["code"] == "REVIEW_UNAVAILABLE"

    state = db.scalar(select(LecturerReviewInvalidSourceState))
    assert state is not None
    assert len(state.attempt_timestamps) == 20
    assert state.blocked_until.replace(tzinfo=clock().tzinfo) == (
        clock() + timedelta(minutes=10)
    )

    valid_request_21 = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert valid_request_21.status_code == 404
    assert valid_request_21.json() == {
        "code": "REVIEW_UNAVAILABLE",
        "message": "This review is unavailable. Contact the planner for a new link.",
    }
    _assert_public_headers(valid_request_21)

    with TestClient(
        app_main.app,
        client=("198.51.100.8", 43000),
    ) as independent_client:
        independent = independent_client.get(
            "/api/public/lecturer-review",
            headers={"Authorization": f"Bearer {secret}"},
        )
    assert independent.status_code == 200

    db.expire_all()
    link = db.get(LecturerReviewLink, issued["issuedLink"]["id"])
    assert link is not None
    assert link.status == "active"
    assert link.expires_at == original_expiry
    assert db.query(LecturerReviewFeedback).count() == 0
    assert db.query(DraftSession).count() == original_session_count
    assert (
        db.get(ScheduleRevision, fixture.working_revision_id).state
        == original_revision_state
    )

    state.last_relevant_at = clock() - timedelta(minutes=15)
    state.blocked_until = clock() + timedelta(seconds=1)
    db.commit()
    assert service.cleanup_invalid_source_states(db, clock=clock) == 0
    assert db.scalar(select(LecturerReviewInvalidSourceState)) is not None

    state = db.scalar(select(LecturerReviewInvalidSourceState))
    assert state is not None
    state.blocked_until = clock()
    db.commit()
    assert service.cleanup_invalid_source_states(db, clock=clock) == 1
    db.commit()
    assert db.scalar(select(LecturerReviewInvalidSourceState)) is None

    with TestClient(
        app_main.app,
        client=("198.51.100.9", 43000),
    ) as retained_client:
        response = retained_client.get(
            "/api/public/lecturer-review",
            headers={"Authorization": "Bearer " + ("r" * 43)},
        )
        assert response.status_code == 404
    retained_state = db.scalar(select(LecturerReviewInvalidSourceState))
    assert retained_state is not None
    clock.advance(minutes=13, seconds=59)
    assert service.cleanup_invalid_source_states(db, clock=clock) == 0
    clock.advance(seconds=1)
    assert service.cleanup_invalid_source_states(db, clock=clock) == 1
    db.commit()
    assert db.scalar(select(LecturerReviewInvalidSourceState)) is None


def test_exact_120_121_protected_view_boundary_preserves_review_state(
    client_and_db,
    monkeypatch,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    clock = DeterministicUtcClock()
    _install_api_clock(monkeypatch, clock)
    issued = _issue_link(client)
    secret = issued["secret"]
    link_id = issued["issuedLink"]["id"]
    original_expiry = db.get(LecturerReviewLink, link_id).expires_at

    for request_number in range(1, 121):
        response = client.get(
            "/api/public/lecturer-review",
            headers={"Authorization": f"Bearer {secret}"},
        )
        assert response.status_code == 200, request_number
        _assert_public_headers(response)

    request_121 = client.get(
        "/api/public/lecturer-review",
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert request_121.status_code == 429
    assert request_121.json()["code"] == "REVIEW_TEMPORARILY_UNAVAILABLE"
    assert request_121.headers["Retry-After"] == "300"
    _assert_public_headers(request_121)

    db.expire_all()
    link = db.get(LecturerReviewLink, link_id)
    assert link is not None
    assert link.status == "active"
    assert link.expires_at == original_expiry
    assert link.access_blocked_until.replace(tzinfo=clock().tzinfo) == (
        clock() + timedelta(minutes=5)
    )
    assert db.query(LecturerReviewFeedback).count() == 0
    assert (
        db.query(LecturerReviewActivityEvent)
        .filter_by(
            review_link_id=link_id,
            event_type="misuse_limit_activated",
            reason_code="view_limited",
        )
        .count()
        == 1
    )
    assert (
        db.query(LecturerReviewActivityEvent)
        .filter_by(
            review_link_id=link_id,
            event_type="access_rejected",
            reason_code="view_limited",
        )
        .count()
        == 1
    )


def test_stable_source_key_survives_restart_during_window_and_active_block(
    persistent_api,
    monkeypatch,
):
    engine = persistent_api
    clock = DeterministicUtcClock()
    _install_api_clock(monkeypatch, clock)
    with Session(engine) as db:
        seed_lecturer_review_fixture(db)
    with TestClient(
        app_main.app,
        client=("203.0.113.50", 43000),
    ) as planner_client:
        issued = _issue_link(planner_client)
    secret = issued["secret"]

    with TestClient(
        app_main.app,
        client=("203.0.113.51", 43000),
    ) as first_process:
        for _attempt in range(10):
            assert first_process.get(
                "/api/public/lecturer-review",
                headers={"Authorization": "Bearer " + ("a" * 43)},
            ).status_code == 404

    with TestClient(
        app_main.app,
        client=("203.0.113.51", 43000),
    ) as restarted_process:
        for _attempt in range(10):
            assert restarted_process.get(
                "/api/public/lecturer-review",
                headers={"Authorization": "Bearer " + ("b" * 43)},
            ).status_code == 404

    with Session(engine) as db:
        state = db.scalar(select(LecturerReviewInvalidSourceState))
        assert state is not None
        assert len(state.attempt_timestamps) == 20
        blocked_until = state.blocked_until

    with TestClient(
        app_main.app,
        client=("203.0.113.51", 43000),
    ) as second_restart:
        blocked_valid = second_restart.get(
            "/api/public/lecturer-review",
            headers={
                "Authorization": f"Bearer {secret}",
                "Forwarded": "for=198.51.100.90",
                "X-Forwarded-For": "198.51.100.91",
            },
        )
    assert blocked_valid.status_code == 404
    assert blocked_valid.json()["code"] == "REVIEW_UNAVAILABLE"
    with Session(engine) as db:
        state = db.scalar(select(LecturerReviewInvalidSourceState))
        assert state is not None
        assert state.blocked_until == blocked_until


def test_concurrent_same_source_is_atomic_and_normalized_sources_are_independent(
    persistent_api,
    monkeypatch,
):
    engine = persistent_api
    clock = DeterministicUtcClock()
    _install_api_clock(monkeypatch, clock)
    with Session(engine) as db:
        seed_lecturer_review_fixture(db)

    def unusable_request(_request_number: int) -> int:
        with TestClient(
            app_main.app,
            client=("2001:0db8:0:0:0:0:0:1", 43000),
        ) as concurrent_client:
            return concurrent_client.get(
                "/api/public/lecturer-review",
                headers={"Authorization": "Bearer " + ("c" * 43)},
            ).status_code

    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses = list(pool.map(unusable_request, range(20)))
    assert statuses == [404] * 20

    with TestClient(
        app_main.app,
        client=("2001:db8::1", 43000),
    ) as normalized_client:
        assert normalized_client.get(
            "/api/public/lecturer-review",
            headers={"Authorization": "Bearer " + ("d" * 43)},
        ).status_code == 404
    with TestClient(
        app_main.app,
        client=("2001:db8::2", 43000),
    ) as independent_client:
        assert independent_client.get(
            "/api/public/lecturer-review",
            headers={
                "Authorization": "Bearer " + ("e" * 43),
                "Forwarded": "for=2001:db8::1",
                "X-Forwarded-For": "2001:db8::1",
            },
        ).status_code == 404

    with Session(engine) as db:
        states = list(db.scalars(select(LecturerReviewInvalidSourceState)))
        attempts_by_count = sorted(
            len(state.attempt_timestamps) for state in states
        )
        assert attempts_by_count == [1, 20]
        assert (
            db.query(LecturerReviewActivityEvent)
            .filter_by(
                event_type="misuse_limit_activated",
                reason_code="source_limited",
            )
            .count()
            == 1
        )


def test_fs015_route_and_payload_contract_excludes_out_of_scope_workflows(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue_link(client)

    multi_lecturer = client.post(
        "/api/schedule-revisions/1/lecturer-review-links",
        json={"lecturerIds": [1, 2], "durationDays": 3},
    )
    attachment_or_thread = client.post(
        "/api/public/lecturer-review/feedback",
        headers={"Authorization": f"Bearer {issued['secret']}"},
        json={
            "clientSubmissionId": "00000000-0000-0000-0000-000000000099",
            "kind": "revision_comment",
            "comment": "Plain text only.",
            "attachment": "agenda.pdf",
            "replyToFeedbackId": 1,
            "approval": "accepted",
        },
    )

    assert multi_lecturer.status_code == 422
    assert attachment_or_thread.status_code == 422
    assert client.patch("/api/public/lecturer-review/feedback").status_code == 405
    assert client.delete("/api/public/lecturer-review/feedback").status_code == 405
