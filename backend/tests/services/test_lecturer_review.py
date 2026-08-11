from __future__ import annotations

import base64
import hashlib
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.services.lecturer_review as lecturer_review_service
from app.db.schema import initialize_database
from app.models.planning import (
    LecturerReviewActivityEvent,
    LecturerReviewFeedback,
    LecturerReviewLink,
    ScheduleRevision,
    DraftSession,
)
from app.schemas.lecturer_review import FeedbackInput
from app.services.lecturer_review import (
    LecturerReviewFailure,
    get_lecturer_review_overview,
    get_public_lecturer_review,
    issue_lecturer_review_link,
    replace_lecturer_review_link,
    revoke_lecturer_review_link,
    submit_lecturer_review_feedback,
)
from app.services.schedule_lifecycle import (
    create_working_revision,
    get_lifecycle_overview,
    prepare_publication,
    transition_revision,
)
from tests.lecturer_review_fixtures import (
    DeterministicUtcClock,
    FIXED_UTC,
    reassign_session,
    remove_all_assignments,
    restore_assignments,
    seed_lecturer_review_fixture,
)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    with Session(engine) as session:
        fixture = seed_lecturer_review_fixture(session)
        yield session, fixture


@pytest.mark.parametrize("duration_days", [1, 2, 3])
def test_issue_generates_256_bit_opaque_secret_and_exact_duration(
    db, duration_days: int
):
    session, fixture = db
    clock = DeterministicUtcClock()

    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=duration_days,
        clock=clock,
    )
    session.commit()

    secret = _value(result, "secret")
    link = session.scalar(select(LecturerReviewLink))
    assert link is not None
    assert len(secret) == 43
    assert all(character.isalnum() or character in "_-" for character in secret)
    assert len(base64.urlsafe_b64decode(secret + "=")) == 32
    assert link.secret_digest == hashlib.sha256(secret.encode("ascii")).hexdigest()
    assert secret != link.secret_digest
    assert secret not in repr(link.__dict__)
    assert "Ada" not in secret
    assert "Autumn" not in secret
    assert "COURSE" not in secret
    assert _utc(link.issued_at) == FIXED_UTC
    assert _utc(link.expires_at) == FIXED_UTC + timedelta(days=duration_days)
    assert link.duration_days == duration_days


@pytest.mark.parametrize("duration_days", [0, 4])
def test_issue_rejects_duration_outside_the_permitted_choices_without_a_row(
    db, duration_days: int
):
    session, fixture = db

    with pytest.raises(LecturerReviewFailure) as failure:
        issue_lecturer_review_link(
            session,
            fixture.working_revision_id,
            fixture.primary_lecturer_id,
            duration_days=duration_days,
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    assert failure.value.status_code == 422
    assert session.query(LecturerReviewLink).count() == 0


def test_raw_secret_is_revealed_only_by_successful_issue(db):
    session, fixture = db
    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    secret = _value(result, "secret")

    overview = get_lecturer_review_overview(
        session,
        fixture.working_revision_id,
        clock=DeterministicUtcClock(),
    )
    public_review = get_public_lecturer_review(
        session,
        secret,
        clock=DeterministicUtcClock(),
    )

    assert secret not in repr(_json(overview))
    assert secret not in repr(_json(public_review))
    assert secret not in repr(session.scalars(select(LecturerReviewLink)).all())
    assert secret not in repr(
        session.scalars(select(LecturerReviewActivityEvent)).all()
    )
    assert secret not in repr(session.scalars(select(LecturerReviewFeedback)).all())
    assert "secret" not in _json(overview)
    for link_summary in _json(overview)["links"]:
        assert "secret" not in link_summary
        assert "secretDigest" not in link_summary


def test_initial_issue_allows_draft_and_ready_but_rejects_non_working_states(db):
    session, fixture = db
    working = session.get(ScheduleRevision, fixture.working_revision_id)
    assert working is not None
    working.state = "ready_for_review"
    working.row_version += 1
    session.commit()

    ready_result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    assert _value(ready_result, "secret")

    with pytest.raises(LecturerReviewFailure) as published_failure:
        issue_lecturer_review_link(
            session,
            fixture.published_revision_id,
            fixture.primary_lecturer_id,
            duration_days=3,
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    assert published_failure.value.status_code == 409
    assert (
        session.query(LecturerReviewLink)
        .filter(
            LecturerReviewLink.schedule_revision_id
            == fixture.published_revision_id
        )
        .count()
        == 0
    )


def test_initial_issue_requires_a_current_assignment(db):
    session, fixture = db
    changes = remove_all_assignments(session, fixture.second_lecturer_id)
    session.commit()

    with pytest.raises(LecturerReviewFailure) as failure:
        issue_lecturer_review_link(
            session,
            fixture.working_revision_id,
            fixture.second_lecturer_id,
            duration_days=3,
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    assert failure.value.status_code == 422
    assert session.query(LecturerReviewLink).count() == 0
    restore_assignments(session, changes)
    session.commit()


def test_one_active_link_per_pair_does_not_change_another_pair(db):
    session, fixture = db
    primary = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    second = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.second_lecturer_id,
        duration_days=2,
        clock=DeterministicUtcClock(),
    )
    session.commit()

    with pytest.raises(LecturerReviewFailure) as duplicate:
        issue_lecturer_review_link(
            session,
            fixture.working_revision_id,
            fixture.primary_lecturer_id,
            duration_days=1,
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    links = session.scalars(
        select(LecturerReviewLink).order_by(LecturerReviewLink.lecturer_id)
    ).all()
    assert duplicate.value.status_code == 409
    assert len(links) == 2
    assert all(link.status == "active" for link in links)
    assert links[0].lecturer_id == fixture.primary_lecturer_id
    assert links[0].secret_digest == hashlib.sha256(
        _value(primary, "secret").encode("ascii")
    ).hexdigest()
    assert links[1].lecturer_id == fixture.second_lecturer_id
    assert links[1].secret_digest == hashlib.sha256(
        _value(second, "secret").encode("ascii")
    ).hexdigest()


def test_public_projection_reloads_current_multi_course_assignments(db):
    session, fixture = db
    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    secret = _value(result, "secret")

    initial = _json(
        get_public_lecturer_review(
            session,
            secret,
            clock=DeterministicUtcClock(),
        )
    )
    assert _session_refs(initial) == {
        "teaching:101",
        "teaching:102",
        "teaching:201",
        "exam:401",
    }
    assert {course["sourceCourseId"] for course in initial["courses"]} == {1, 2}

    reassign_session(session, "teaching", 101, fixture.second_lecturer_id)
    reassign_session(session, "teaching", 202, fixture.primary_lecturer_id)
    session.commit()
    refreshed = _json(
        get_public_lecturer_review(
            session,
            secret,
            clock=DeterministicUtcClock(),
        )
    )

    assert _session_refs(refreshed) == {
        "teaching:102",
        "teaching:201",
        "teaching:202",
        "exam:401",
    }
    assert "teaching:101" not in _session_refs(refreshed)
    assert "teaching:1001" not in _session_refs(refreshed)
    assert "exam:4001" not in _session_refs(refreshed)


def test_valid_link_remains_empty_then_repopulates_after_assignment_restore(db):
    session, fixture = db
    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    secret = _value(result, "secret")
    changes = remove_all_assignments(session, fixture.primary_lecturer_id)
    session.commit()

    empty = _json(
        get_public_lecturer_review(
            session,
            secret,
            clock=DeterministicUtcClock(),
        )
    )
    link = session.scalar(select(LecturerReviewLink))
    assert empty["courses"] == []
    assert link is not None
    assert link.status == "active"

    restore_assignments(session, changes)
    session.commit()
    restored = _json(
        get_public_lecturer_review(
            session,
            secret,
            clock=DeterministicUtcClock(),
        )
    )
    assert _session_refs(restored) == {
        "teaching:101",
        "teaching:102",
        "teaching:201",
        "exam:401",
    }


def test_public_projection_is_exactly_minimum_scope(db):
    session, fixture = db
    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    public = _json(
        get_public_lecturer_review(
            session,
            _value(result, "secret"),
            clock=DeterministicUtcClock(),
        )
    )

    assert set(public) == {
        "intendedLecturer",
        "identityDisclaimer",
        "revision",
        "accessExpiresAt",
        "timeZone",
        "semesterStartDate",
        "semesterEndDate",
        "validationAvailability",
        "validationFindings",
        "filterFacets",
        "courses",
        "submittedFeedback",
    }
    assert set(public["revision"]) == {
        "id",
        "semesterId",
        "semesterName",
        "label",
        "state",
    }
    assert public["revision"]["id"] == fixture.working_revision_id
    assert public["revision"]["state"] == "draft"
    assert public["intendedLecturer"] == "Ada Lovelace"
    assert public["identityDisclaimer"] == (
        "Dieser Link ist für Ada Lovelace bestimmt; die Identität der "
        "verwendenden Person wird nicht authentifiziert."
    )
    assert {
        item["value"]: item["label"]
        for item in public["filterFacets"]["sessionTypes"]
    } == {"exam": "Prüfungstermin", "teaching": "Lehrtermin"}
    assert public["filterFacets"]["lifecycleContexts"] == [
        {"value": "draft", "label": "Entwurf"}
    ]
    assert all(
        "_" not in item["label"]
        for item in public["filterFacets"]["validationCategories"]
    )
    assert public["submittedFeedback"] == []
    assert {course["code"] for course in public["courses"]} == {
        "COURSE-1",
        "COURSE-2",
    }
    for course in public["courses"]:
        assert set(course) == {
            "sourceCourseId",
            "courseRef",
            "code",
            "title",
            "cohortName",
            "studyType",
            "sessions",
        }
        for item in course["sessions"]:
            assert set(item) == {
                "sessionRef",
                "sessionKind",
                "sourceSessionId",
                "courseRef",
                "sessionType",
                "date",
                "startTime",
                "endTime",
                "timeZone",
                "roomName",
                "roomRef",
                "cohortName",
                "teachingUnits",
                "examDurationMinutes",
                "validationFindingRefs",
            }
    assert "lecturers" not in public["filterFacets"]
    assert public["semesterStartDate"] == "2026-09-01"
    assert public["semesterEndDate"] == "2026-12-20"

    serialized = repr(public)
    assert "Grace Hopper" not in serialized
    assert "Katherine Johnson" not in serialized
    assert "Applied Physics" not in serialized
    assert "LECT-" not in serialized
    for forbidden_key in {
        "lecturerId",
        "referenceCode",
        "capacity",
        "studentCount",
        "plannerNotes",
        "events",
        "allowedActions",
        "stateToken",
        "secret",
        "secretDigest",
    }:
        assert forbidden_key not in serialized


@pytest.mark.parametrize(
    ("workspace_availability", "public_availability"),
    [("partial", "partial"), ("unavailable", "unavailable")],
)
def test_incomplete_validation_never_offers_a_no_issue_filter(
    db,
    monkeypatch,
    workspace_availability: str,
    public_availability: str,
):
    session, fixture = db
    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    original_get_calendar_workspace = (
        lecturer_review_service.get_calendar_workspace
    )

    def incomplete_workspace(*args, **kwargs):
        workspace = original_get_calendar_workspace(*args, **kwargs)
        workspace["sectionStatus"]["validationFindings"][
            "availability"
        ] = workspace_availability
        workspace["validationFindings"] = []
        return workspace

    monkeypatch.setattr(
        lecturer_review_service,
        "get_calendar_workspace",
        incomplete_workspace,
    )

    public = _json(
        get_public_lecturer_review(
            session,
            _value(result, "secret"),
            clock=DeterministicUtcClock(),
        )
    )

    assert public["validationAvailability"] == public_availability
    assert public["validationFindings"] == []
    assert "none" not in {
        facet["value"]
        for facet in public["filterFacets"]["validationCategories"]
    }


@pytest.mark.parametrize(
    ("payload", "expected_kind", "expected_session_ref", "expected_comment"),
    [
        (
            {
                "clientSubmissionId": str(UUID(int=1)),
                "kind": "revision_comment",
                "comment": "The overall plan works.",
            },
            "revision_comment",
            None,
            "The overall plan works.",
        ),
        (
            {
                "clientSubmissionId": str(UUID(int=2)),
                "kind": "session_comment",
                "sessionRef": "teaching:101",
                "comment": "Tuesday after 10:00 would be better.",
            },
            "session_comment",
            "teaching:101",
            "Tuesday after 10:00 would be better.",
        ),
        (
            {
                "clientSubmissionId": str(UUID(int=3)),
                "kind": "impossible_session",
                "sessionRef": "exam:401",
            },
            "impossible_session",
            "exam:401",
            None,
        ),
        (
            {
                "clientSubmissionId": str(UUID(int=4)),
                "kind": "impossible_session",
                "sessionRef": "teaching:102",
                "comment": "I can teach this on 30 September instead.",
            },
            "impossible_session",
            "teaching:102",
            "I can teach this on 30 September instead.",
        ),
    ],
)
def test_feedback_kinds_create_separate_immutable_items(
    db, payload, expected_kind, expected_session_ref, expected_comment
):
    session, fixture = db
    secret = _issue_secret(session, fixture)

    result = submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput.model_validate(payload),
        clock=DeterministicUtcClock(),
    )
    session.commit()
    item = _json(result)["item"]

    assert _json(result)["outcome"] == "created"
    assert item["kind"] == expected_kind
    assert item["sessionRef"] == expected_session_ref
    assert item["comment"] == expected_comment
    stored = session.scalar(select(LecturerReviewFeedback))
    assert stored is not None
    assert stored.kind == expected_kind
    assert stored.comment_text == expected_comment
    assert stored.submitted_at is not None


@pytest.mark.parametrize("comment_length", [1, 2000])
def test_comment_visible_character_boundaries_are_accepted(db, comment_length: int):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    comment = "x" * comment_length

    result = submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=comment_length),
            kind="revision_comment",
            comment=comment,
        ),
        clock=DeterministicUtcClock(),
    )
    session.commit()

    assert _json(result)["outcome"] == "created"
    assert _json(result)["item"]["comment"] == comment
    assert session.scalar(select(LecturerReviewFeedback)).comment_text == comment


@pytest.mark.parametrize("comment", ["", " \t\r\n ", "x" * 2001])
def test_invalid_comment_boundaries_create_no_partial_feedback(db, comment: str):
    session, fixture = db
    secret = _issue_secret(session, fixture)

    with pytest.raises(ValueError):
        payload = FeedbackInput(
            client_submission_id=UUID(int=10),
            kind="revision_comment",
            comment=comment,
        )
        submit_lecturer_review_feedback(
            session,
            secret,
            payload,
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    assert session.query(LecturerReviewFeedback).count() == 0


def test_markup_looking_feedback_is_retained_as_literal_plain_text(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    active_text = '<script>alert(1)</script><img src=x onerror="alert(2)">'

    result = submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=20),
            kind="session_comment",
            session_ref="teaching:101",
            comment=active_text,
        ),
        clock=DeterministicUtcClock(),
    )
    session.commit()
    public = _json(
        get_public_lecturer_review(
            session,
            secret,
            clock=DeterministicUtcClock(),
        )
    )

    assert _json(result)["item"]["comment"] == active_text
    assert public["submittedFeedback"][0]["comment"] == active_text
    assert session.scalar(select(LecturerReviewFeedback)).comment_text == active_text


def test_feedback_comment_limit_is_applied_after_surrounding_space_is_trimmed():
    payload = FeedbackInput(
        client_submission_id=UUID(int=19),
        kind="revision_comment",
        comment=(" " * 1_000) + ("x" * 2_000) + (" " * 1_000),
    )

    assert payload.comment == "x" * 2_000


@pytest.mark.parametrize("comment", ["\u200b", "\u200d", "\u0301"])
def test_feedback_comment_requires_visible_unicode_content(comment: str):
    with pytest.raises(ValueError):
        FeedbackInput(
            client_submission_id=UUID(int=19),
            kind="revision_comment",
            comment=comment,
        )


def test_session_feedback_captures_authoritative_current_context(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    teaching = session.get(DraftSession, 101)
    assert teaching is not None
    teaching.date = date(2026, 10, 12)
    teaching.start_time = time(13, 30)
    teaching.end_time = time(15, 30)
    teaching.room_id = 2
    session.commit()

    submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=30),
            kind="session_comment",
            session_ref="teaching:101",
            comment="This updated afternoon time works.",
        ),
        clock=DeterministicUtcClock(),
    )
    session.commit()
    stored = session.scalar(select(LecturerReviewFeedback))

    assert stored is not None
    assert stored.session_kind == "teaching"
    assert stored.source_session_id == 101
    assert stored.session_context == {
        "sessionRef": "teaching:101",
        "sessionKind": "teaching",
        "sourceSessionId": 101,
        "sessionType": "Lecture",
        "courseSourceId": 1,
        "courseCode": "COURSE-1",
        "courseTitle": "Analytical Methods",
        "date": "2026-10-12",
        "startTime": "13:30",
        "endTime": "15:30",
        "timeZone": "Europe/Vienna",
        "roomName": "Room 201",
        "cohortName": "Cohort 1",
        "studyType": "Full-time",
        "teachingUnits": 2,
        "examDurationMinutes": None,
    }


def test_public_validation_sanitizes_cross_scope_counterparts(db):
    session, fixture = db
    other = session.get(DraftSession, 301)
    scoped = session.get(DraftSession, 101)
    assert other is not None and scoped is not None
    other.date = scoped.date
    other.start_time = scoped.start_time
    other.end_time = scoped.end_time
    other.room_id = scoped.room_id
    issued = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        clock=DeterministicUtcClock(),
    )
    session.commit()

    public = _json(
        get_public_lecturer_review(
            session,
            _value(issued, "secret"),
            clock=DeterministicUtcClock(),
        )
    )

    room_conflict = next(
        finding
        for finding in public["validationFindings"]
        if finding["category"] == "room_conflict"
    )
    assert room_conflict["affectedSessionRefs"] == ["teaching:101"]
    assert "Betroffen:" in room_conflict["message"]
    assert "Dieser Hinweis blockiert die Rückmeldung nicht" in room_conflict["message"]
    serialized = repr(room_conflict)
    assert "teaching:301" not in serialized
    assert "Grace Hopper" not in serialized
    assert "room:1" not in serialized


def test_each_planner_feedback_item_retains_its_submission_context(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    clock = DeterministicUtcClock()

    submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=31),
            kind="session_comment",
            session_ref="teaching:101",
            comment="The original time is difficult.",
        ),
        clock=clock,
    )
    teaching = session.get(DraftSession, 101)
    assert teaching is not None
    teaching.date = date(2026, 10, 14)
    teaching.start_time = time(14, 0)
    teaching.end_time = time(16, 0)
    teaching.room_id = 2
    session.commit()
    clock.advance(minutes=1)
    submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=32),
            kind="session_comment",
            session_ref="teaching:101",
            comment="The revised time works.",
        ),
        clock=clock,
    )
    session.commit()

    overview = _json(
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=clock,
        )
    )
    items = overview["feedbackGroups"][0]["items"]

    assert items[0]["sessionContext"]["date"] != items[1]["sessionContext"]["date"]
    assert items[0]["sessionContext"]["roomName"] == "Room 101"
    assert items[1]["sessionContext"]["roomName"] == "Room 201"
    assert items[0]["sessionStatus"] == "changed"
    assert items[1]["sessionStatus"] == "current"


def test_changed_session_resolves_impossible_feedback_without_deleting_history(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=33),
            kind="impossible_session",
            session_ref="teaching:101",
            comment="The original appointment is not possible.",
        ),
        clock=DeterministicUtcClock(),
    )
    session.commit()

    before = _json(
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=DeterministicUtcClock(),
        )
    )
    assert before["feedbackGroups"][0]["items"][0]["sessionStatus"] == "current"

    teaching = session.get(DraftSession, 101)
    assert teaching is not None
    teaching.date = date(2026, 10, 14)
    teaching.start_time = time(14, 0)
    teaching.end_time = time(16, 0)
    session.commit()

    after = _json(
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=DeterministicUtcClock(),
        )
    )

    assert after["totalFeedbackCount"] == 1
    assert after["impossibleFlagCount"] == 0
    assert after["feedbackGroups"][0]["impossibleFlagCount"] == 0
    assert after["feedbackGroups"][0]["items"][0]["sessionStatus"] == "changed"


def test_feedback_rejects_session_reassigned_out_of_link_scope(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    reassign_session(
        session,
        "teaching",
        101,
        fixture.second_lecturer_id,
    )
    session.commit()

    with pytest.raises(LecturerReviewFailure) as failure:
        submit_lecturer_review_feedback(
            session,
            secret,
            FeedbackInput(
                client_submission_id=UUID(int=40),
                kind="session_comment",
                session_ref="teaching:101",
                comment="This must not be accepted against stale scope.",
            ),
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    assert failure.value.status_code == 409
    assert session.query(LecturerReviewFeedback).count() == 0


def test_deliberate_repeated_impossible_flags_remain_separate_and_immutable(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)

    first = submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=50),
            kind="impossible_session",
            session_ref="exam:401",
        ),
        clock=DeterministicUtcClock(),
    )
    second = submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=51),
            kind="impossible_session",
            session_ref="exam:401",
            comment="A different date is needed.",
        ),
        clock=DeterministicUtcClock(),
    )
    session.commit()

    rows = session.scalars(
        select(LecturerReviewFeedback).order_by(LecturerReviewFeedback.id)
    ).all()
    assert len(rows) == 2
    assert rows[0].id != rows[1].id
    assert rows[0].comment_text is None
    assert rows[1].comment_text == "A different date is needed."
    assert _json(first)["outcome"] == "created"
    assert _json(second)["outcome"] == "created"


def test_logical_retry_is_idempotent_and_fingerprint_conflict_changes_nothing(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    submission_id = UUID(int=60)
    payload = FeedbackInput(
        client_submission_id=submission_id,
        kind="session_comment",
        session_ref="teaching:101",
        comment="Prefer Wednesday.",
    )

    created = submit_lecturer_review_feedback(
        session,
        secret,
        payload,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    replayed = submit_lecturer_review_feedback(
        session,
        secret,
        payload,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    assert _json(created)["outcome"] == "created"
    assert _json(replayed)["outcome"] == "already_accepted"
    assert _json(replayed)["item"]["id"] == _json(created)["item"]["id"]
    assert session.query(LecturerReviewFeedback).count() == 1

    with pytest.raises(LecturerReviewFailure) as conflict:
        submit_lecturer_review_feedback(
            session,
            secret,
            FeedbackInput(
                client_submission_id=submission_id,
                kind="session_comment",
                session_ref="teaching:101",
                comment="Prefer Friday instead.",
            ),
            clock=DeterministicUtcClock(),
        )
    session.rollback()

    assert conflict.value.status_code == 409
    rows = session.scalars(select(LecturerReviewFeedback)).all()
    assert len(rows) == 1
    assert rows[0].comment_text == "Prefer Wednesday."


def test_same_link_public_history_contains_every_accepted_item_in_order(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    clock = DeterministicUtcClock()

    for index, payload in enumerate(
        [
            FeedbackInput(
                client_submission_id=UUID(int=70),
                kind="revision_comment",
                comment="First",
            ),
            FeedbackInput(
                client_submission_id=UUID(int=71),
                kind="session_comment",
                session_ref="teaching:101",
                comment="Second",
            ),
            FeedbackInput(
                client_submission_id=UUID(int=72),
                kind="impossible_session",
                session_ref="exam:401",
            ),
        ]
    ):
        clock.advance(seconds=index)
        submit_lecturer_review_feedback(
            session,
            secret,
            payload,
            clock=clock,
        )
    session.commit()

    review = _json(get_public_lecturer_review(session, secret, clock=clock))
    assert [
        (item["kind"], item["sessionRef"], item["comment"])
        for item in review["submittedFeedback"]
    ] == [
        ("revision_comment", None, "First"),
        ("session_comment", "teaching:101", "Second"),
        ("impossible_session", "exam:401", None),
    ]


def test_feedback_limit_accepts_ten_then_rejects_request_eleven_in_one_minute(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    clock = DeterministicUtcClock()

    for index in range(10):
        submit_lecturer_review_feedback(
            session,
            secret,
            _revision_comment(100 + index),
            clock=clock,
        )
    session.commit()
    with pytest.raises(LecturerReviewFailure) as limited:
        submit_lecturer_review_feedback(
            session,
            secret,
            _revision_comment(110),
            clock=clock,
        )
    session.rollback()

    assert limited.value.status_code == 429
    assert session.query(LecturerReviewFeedback).count() == 10


def test_feedback_limit_accepts_sixty_then_rejects_request_sixty_one_in_hour(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    clock = DeterministicUtcClock()

    for index in range(60):
        submit_lecturer_review_feedback(
            session,
            secret,
            _revision_comment(200 + index),
            clock=clock,
        )
        session.commit()
        clock.advance(seconds=59)

    with pytest.raises(LecturerReviewFailure) as limited:
        submit_lecturer_review_feedback(
            session,
            secret,
            _revision_comment(260),
            clock=clock,
        )
    session.rollback()

    assert limited.value.status_code == 429
    assert session.query(LecturerReviewFeedback).count() == 60


def test_access_closes_exactly_at_expiry_without_a_grace_period(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    assert _json(
        get_public_lecturer_review(
            session,
            secret,
            clock=DeterministicUtcClock(
                FIXED_UTC + timedelta(days=3, microseconds=-1)
            ),
        )
    )["courses"]
    session.commit()

    _assert_unavailable(
        session,
        secret,
        DeterministicUtcClock(FIXED_UTC + timedelta(days=3)),
    )
    link = session.scalar(select(LecturerReviewLink))
    assert link is not None
    assert link.status == "expired"
    assert _utc(link.ended_at) == FIXED_UTC + timedelta(days=3)
    _assert_unavailable(
        session,
        secret,
        DeterministicUtcClock(
            FIXED_UTC + timedelta(days=3, microseconds=1)
        ),
    )


def test_revoke_is_immediate_and_replace_ends_all_earlier_links_with_default(db):
    session, fixture = db
    first_secret = _issue_secret(session, fixture)
    first = session.scalar(select(LecturerReviewLink))
    assert first is not None
    revoke_lecturer_review_link(
        session,
        first.id,
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=1)),
    )
    session.commit()
    _assert_unavailable(session, first_secret, DeterministicUtcClock())

    replacement = replace_lecturer_review_link(
        session,
        first.id,
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=2)),
    )
    session.commit()
    replacement_secret = _value(replacement, "secret")
    replacement_id = _json(replacement)["issuedLink"]["id"]
    final = replace_lecturer_review_link(
        session,
        replacement_id,
        duration_days=2,
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=3)),
    )
    session.commit()

    links = session.scalars(
        select(LecturerReviewLink).order_by(LecturerReviewLink.id)
    ).all()
    assert [link.status for link in links] == ["replaced", "replaced", "active"]
    assert links[1].duration_days == 3
    assert links[2].duration_days == 2
    assert links[0].replaced_by_id == links[1].id
    assert links[1].replaced_by_id == links[2].id
    _assert_unavailable(session, first_secret, DeterministicUtcClock())
    _assert_unavailable(session, replacement_secret, DeterministicUtcClock())
    assert _json(
        get_public_lecturer_review(
            session,
            _value(final, "secret"),
            clock=DeterministicUtcClock(),
        )
    )["courses"]


def test_first_publication_keeps_the_bound_link_active(db):
    session, fixture = db
    working = session.get(ScheduleRevision, fixture.working_revision_id)
    published = session.get(ScheduleRevision, fixture.published_revision_id)
    assert working is not None and published is not None
    working.origin_revision_id = None
    session.flush()
    session.delete(published)
    session.commit()
    secret = _issue_secret(session, fixture)

    _publish(session, fixture.working_revision_id)
    link = session.scalar(select(LecturerReviewLink))
    review = _json(
        get_public_lecturer_review(
            session, secret, clock=DeterministicUtcClock()
        )
    )
    assert link is not None
    assert link.status == "active"
    assert review["revision"]["state"] == "published"


def test_published_planner_scope_comes_from_snapshot_after_new_working_changes(db):
    session, fixture = db
    working = session.get(ScheduleRevision, fixture.working_revision_id)
    published = session.get(ScheduleRevision, fixture.published_revision_id)
    assert working is not None and published is not None
    working.origin_revision_id = None
    session.flush()
    session.delete(published)
    session.commit()
    _publish(session, fixture.working_revision_id)
    before = _json(
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=DeterministicUtcClock(),
        )
    )
    expected = next(
        item
        for item in before["lecturers"]
        if item["lecturerId"] == fixture.primary_lecturer_id
    )

    lifecycle = get_lifecycle_overview(session, fixture.semester_id)
    create_working_revision(
        session,
        fixture.semester_id,
        lifecycle["stateToken"],
    )
    remove_all_assignments(session, fixture.primary_lecturer_id)
    session.commit()

    after = _json(
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=DeterministicUtcClock(),
        )
    )
    actual = next(
        item
        for item in after["lecturers"]
        if item["lecturerId"] == fixture.primary_lecturer_id
    )
    assert actual["sessionCount"] == expected["sessionCount"]
    assert actual["courses"] == expected["courses"]


def test_abandon_ends_access_permanently_across_restore(db):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    overview = get_lifecycle_overview(session, fixture.semester_id)
    current = overview["activeWorkingRevision"]
    abandoned = transition_revision(
        session,
        fixture.working_revision_id,
        action="abandon",
        expected_revision_version=current["revisionVersion"],
        expected_state_token=overview["stateToken"],
        confirmed=True,
    )
    session.commit()
    link = session.scalar(select(LecturerReviewLink))
    assert link is not None
    assert (link.status, link.end_reason) == ("revision_ended", "abandoned")
    _assert_unavailable(session, secret, DeterministicUtcClock())

    abandoned_revision = next(
        item
        for item in abandoned["revisions"]
        if item["revisionId"] == fixture.working_revision_id
    )
    transition_revision(
        session,
        fixture.working_revision_id,
        action="restore",
        expected_revision_version=abandoned_revision["revisionVersion"],
        expected_state_token=abandoned["stateToken"],
        confirmed=True,
    )
    session.commit()
    session.refresh(link)
    assert (link.status, link.end_reason) == ("revision_ended", "abandoned")
    _assert_unavailable(session, secret, DeterministicUtcClock())


def test_replacement_publication_terminalizes_superseded_revision_link(db):
    session, fixture = db
    secret = "S" * 43
    old = LecturerReviewLink(
        schedule_revision_id=fixture.published_revision_id,
        lecturer_id=fixture.primary_lecturer_id,
        intended_lecturer_name="Ada Lovelace",
        secret_digest=hashlib.sha256(secret.encode("ascii")).hexdigest(),
        duration_days=3,
        issued_at=FIXED_UTC,
        expires_at=FIXED_UTC + timedelta(days=3),
        status="active",
    )
    session.add(old)
    session.commit()

    _publish(session, fixture.working_revision_id)
    session.refresh(old)
    assert (old.status, old.end_reason) == ("revision_ended", "superseded")
    _assert_unavailable(session, secret, DeterministicUtcClock())


@pytest.mark.parametrize("secret", ["bad", "U" * 43])
def test_malformed_and_unknown_secrets_match_all_ended_link_failures(db, secret):
    session, _fixture = db
    _assert_unavailable(session, secret, DeterministicUtcClock())


@pytest.mark.parametrize(
    ("ending", "expected_status"),
    [
        ("expiry", "expired"),
        ("revoke", "revoked"),
        ("replace", "replaced"),
    ],
)
def test_feedback_remains_immutable_and_advisory_after_link_ending_and_publication(
    db,
    ending,
    expected_status,
):
    session, fixture = db
    secret = _issue_secret(session, fixture)
    link = session.scalar(select(LecturerReviewLink))
    assert link is not None
    link_id = link.id
    submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=900),
            kind="revision_comment",
            comment="Please consider a later start.",
        ),
        clock=DeterministicUtcClock(),
    )
    submit_lecturer_review_feedback(
        session,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=901),
            kind="impossible_session",
            session_ref="teaching:101",
            comment="This occurrence is not possible.",
        ),
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(seconds=1)),
    )
    session.commit()
    before = _feedback_signatures(session)

    if ending == "expiry":
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=DeterministicUtcClock(FIXED_UTC + timedelta(days=3)),
        )
    elif ending == "revoke":
        revoke_lecturer_review_link(
            session,
            link_id,
            clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=1)),
        )
    else:
        replace_lecturer_review_link(
            session,
            link_id,
            clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=1)),
        )
    session.commit()

    ended = session.get(LecturerReviewLink, link_id)
    assert ended is not None
    assert ended.status == expected_status
    assert _feedback_signatures(session) == before

    published = _publish(session, fixture.working_revision_id)

    assert published["currentPublication"]["revisionId"] == fixture.working_revision_id
    assert _feedback_signatures(session) == before
    overview = _json(
        get_lecturer_review_overview(
            session,
            fixture.working_revision_id,
            clock=DeterministicUtcClock(FIXED_UTC + timedelta(days=3)),
        )
    )
    assert overview["totalFeedbackCount"] == 2
    assert overview["impossibleFlagCount"] == 1


def _value(value: Any, field: str) -> Any:
    if isinstance(value, dict):
        return value[field]
    return getattr(value, field)


def _json(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return value.model_dump(mode="json", by_alias=True)


def _session_refs(public_review: dict) -> set[str]:
    return {
        session["sessionRef"]
        for course in public_review["courses"]
        for session in course["sessions"]
    }


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _issue_secret(session, fixture) -> str:
    result = issue_lecturer_review_link(
        session,
        fixture.working_revision_id,
        fixture.primary_lecturer_id,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    session.commit()
    return _value(result, "secret")


def _revision_comment(submission_number: int) -> FeedbackInput:
    return FeedbackInput(
        client_submission_id=UUID(int=submission_number),
        kind="revision_comment",
        comment=f"Comment {submission_number}",
    )


def _feedback_signatures(session: Session) -> list[tuple]:
    return [
        (
            item.id,
            item.review_link_id,
            item.kind,
            item.session_kind,
            item.source_session_id,
            item.comment_text,
            item.session_context,
            item.client_submission_id,
            item.request_fingerprint,
            _utc(item.submitted_at),
        )
        for item in session.scalars(
            select(LecturerReviewFeedback).order_by(LecturerReviewFeedback.id)
        )
    ]


def _assert_unavailable(
    session: Session, secret: str, clock: DeterministicUtcClock
) -> None:
    with pytest.raises(LecturerReviewFailure) as failure:
        get_public_lecturer_review(session, secret, clock=clock)
    session.commit()
    assert (
        failure.value.status_code,
        failure.value.code,
        failure.value.message,
    ) == (
        404,
        "REVIEW_UNAVAILABLE",
        "This review is unavailable. Contact the planner for a new link.",
    )


def _publish(session: Session, revision_id: int) -> dict:
    revision = session.get(ScheduleRevision, revision_id)
    assert revision is not None
    overview = get_lifecycle_overview(session, revision.semester_id)
    preparation = prepare_publication(
        session,
        revision_id,
        revision.row_version,
        overview["stateToken"],
    )
    result = transition_revision(
        session,
        revision_id,
        action="publish",
        expected_revision_version=revision.row_version,
        expected_state_token=overview["stateToken"],
        confirmed=True,
        publication_token=preparation["preparationToken"],
    )
    session.commit()
    return result
