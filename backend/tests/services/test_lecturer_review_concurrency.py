from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier, Event
from typing import Any
from uuid import UUID

from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import (
    DraftSession,
    LecturerReviewFeedback,
    LecturerReviewLink,
    Semester,
)
from app.schemas.lecturer_review import FeedbackInput
from app.services.lecturer_review import (
    LecturerReviewFailure,
    get_public_lecturer_review,
    issue_lecturer_review_link,
    replace_lecturer_review_link,
    revoke_lecturer_review_link,
    submit_lecturer_review_feedback,
)
from app.services.schedule_lifecycle import (
    get_lifecycle_overview,
    prepare_publication,
    transition_revision,
)
from tests.lecturer_review_fixtures import (
    DeterministicUtcClock,
    FIXED_UTC,
    reassign_session,
    seed_lecturer_review_fixture,
)


def test_simultaneous_initial_issue_leaves_exactly_one_active_link(tmp_path: Path):
    database = tmp_path / "lecturer-review-issue-race.db"
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    initialize_database(engine)
    with Session(engine) as db:
        fixture = seed_lecturer_review_fixture(db)

    barrier = Barrier(2)

    def attempt_issue():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = issue_lecturer_review_link(
                    db,
                    fixture.working_revision_id,
                    fixture.primary_lecturer_id,
                    duration_days=3,
                    clock=DeterministicUtcClock(),
                )
                db.commit()
                return ("issued", _value(result, "secret"))
            except LecturerReviewFailure as exc:
                db.rollback()
                return ("rejected", exc.status_code)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _item: attempt_issue(), range(2)))

    assert [kind for kind, _value in outcomes].count("issued") == 1
    assert [kind for kind, _value in outcomes].count("rejected") == 1
    assert next(value for kind, value in outcomes if kind == "rejected") == 409
    with Session(engine) as db:
        links = db.scalars(select(LecturerReviewLink)).all()
        assert len(links) == 1
        assert links[0].status == "active"
        assert links[0].schedule_revision_id == fixture.working_revision_id
        assert links[0].lecturer_id == fixture.primary_lecturer_id


def test_protected_view_waiting_on_assignment_change_reloads_current_scope(
    tmp_path: Path,
):
    database = tmp_path / "lecturer-review-assignment-view-race.db"
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    initialize_database(engine)
    with Session(engine) as db:
        fixture = seed_lecturer_review_fixture(db)
        issued = issue_lecturer_review_link(
            db,
            fixture.working_revision_id,
            fixture.primary_lecturer_id,
            duration_days=3,
            clock=DeterministicUtcClock(),
        )
        db.commit()
        secret = _value(issued, "secret")

    assignment_claimed = Event()
    view_attempting = Event()

    def change_assignment():
        with Session(engine) as db:
            db.execute(
                update(Semester)
                .where(Semester.id == fixture.semester_id)
                .values(id=Semester.id)
            )
            reassign_session(
                db,
                "teaching",
                fixture.primary_teaching_session_ids[0],
                fixture.second_lecturer_id,
            )
            assignment_claimed.set()
            assert view_attempting.wait(timeout=5)
            db.commit()

    def read_view():
        assert assignment_claimed.wait(timeout=5)
        with Session(engine) as db:
            view_attempting.set()
            result = get_public_lecturer_review(
                db,
                secret,
                clock=DeterministicUtcClock(),
            )
            db.commit()
            return _session_refs(_json(result))

    with ThreadPoolExecutor(max_workers=2) as pool:
        change_future = pool.submit(change_assignment)
        view_future = pool.submit(read_view)
        change_future.result(timeout=10)
        visible_refs = view_future.result(timeout=10)

    assert (
        f"teaching:{fixture.primary_teaching_session_ids[0]}"
        not in visible_refs
    )
    assert visible_refs == {
        "teaching:102",
        "teaching:201",
        "exam:401",
    }
    with Session(engine) as db:
        changed = db.get(DraftSession, fixture.primary_teaching_session_ids[0])
        assert changed is not None
        assert changed.lecturer_id == fixture.second_lecturer_id


def test_duplicate_submission_race_creates_one_feedback_item(tmp_path: Path):
    database = tmp_path / "lecturer-review-duplicate-feedback-race.db"
    engine, fixture, secret = _seed_issued_database(database)
    barrier = Barrier(2)
    payload = FeedbackInput(
        client_submission_id=UUID(int=400),
        kind="session_comment",
        session_ref="teaching:101",
        comment="One logical submission.",
    )

    def submit():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = submit_lecturer_review_feedback(
                    db,
                    secret,
                    payload,
                    clock=DeterministicUtcClock(),
                )
                db.commit()
                return _json(result)["outcome"]
            except LecturerReviewFailure as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _item: submit(), range(2)))

    assert sorted(outcomes) == ["already_accepted", "created"]
    with Session(engine) as db:
        rows = db.scalars(select(LecturerReviewFeedback)).all()
        assert len(rows) == 1
        assert rows[0].client_submission_id == str(payload.client_submission_id)
        assert rows[0].review_link.lecturer_id == fixture.primary_lecturer_id


def test_feedback_waiting_on_revoke_rejects_without_an_item(tmp_path: Path):
    database = tmp_path / "lecturer-review-revoke-feedback-race.db"
    engine, fixture, secret = _seed_issued_database(database)
    revoke_claimed = Event()
    feedback_attempting = Event()

    def revoke():
        with Session(engine) as db:
            link = db.scalar(select(LecturerReviewLink))
            assert link is not None
            revoke_lecturer_review_link(
                db,
                link.id,
                clock=DeterministicUtcClock(),
            )
            revoke_claimed.set()
            assert feedback_attempting.wait(timeout=5)
            db.commit()

    def submit():
        assert revoke_claimed.wait(timeout=5)
        with Session(engine) as db:
            feedback_attempting.set()
            try:
                submit_lecturer_review_feedback(
                    db,
                    secret,
                    FeedbackInput(
                        client_submission_id=UUID(int=410),
                        kind="revision_comment",
                        comment="Must lose to revocation.",
                    ),
                    clock=DeterministicUtcClock(),
                )
                db.commit()
                return "accepted"
            except LecturerReviewFailure as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        revoke_future = pool.submit(revoke)
        feedback_future = pool.submit(submit)
        revoke_future.result(timeout=10)
        outcome = feedback_future.result(timeout=10)

    assert outcome == 404
    with Session(engine) as db:
        assert db.query(LecturerReviewFeedback).count() == 0
        assert db.scalar(select(LecturerReviewLink)).status == "revoked"


def test_feedback_waiting_on_reassignment_rejects_stale_scope(tmp_path: Path):
    database = tmp_path / "lecturer-review-reassignment-feedback-race.db"
    engine, fixture, secret = _seed_issued_database(database)
    assignment_claimed = Event()
    feedback_attempting = Event()

    def reassign():
        with Session(engine) as db:
            db.execute(
                update(Semester)
                .where(Semester.id == fixture.semester_id)
                .values(id=Semester.id)
            )
            reassign_session(
                db,
                "teaching",
                101,
                fixture.second_lecturer_id,
            )
            assignment_claimed.set()
            assert feedback_attempting.wait(timeout=5)
            db.commit()

    def submit():
        assert assignment_claimed.wait(timeout=5)
        with Session(engine) as db:
            feedback_attempting.set()
            try:
                submit_lecturer_review_feedback(
                    db,
                    secret,
                    FeedbackInput(
                        client_submission_id=UUID(int=420),
                        kind="session_comment",
                        session_ref="teaching:101",
                        comment="This session is no longer in scope.",
                    ),
                    clock=DeterministicUtcClock(),
                )
                db.commit()
                return "accepted"
            except LecturerReviewFailure as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assignment_future = pool.submit(reassign)
        feedback_future = pool.submit(submit)
        assignment_future.result(timeout=10)
        outcome = feedback_future.result(timeout=10)

    assert outcome == 409
    with Session(engine) as db:
        assert db.query(LecturerReviewFeedback).count() == 0
        assert db.get(DraftSession, 101).lecturer_id == fixture.second_lecturer_id


def test_concurrent_feedback_crossing_minute_limit_accepts_only_request_ten(
    tmp_path: Path,
):
    database = tmp_path / "lecturer-review-feedback-limit-race.db"
    engine, _fixture, secret = _seed_issued_database(database)
    clock = DeterministicUtcClock()
    with Session(engine) as db:
        for index in range(9):
            submit_lecturer_review_feedback(
                db,
                secret,
                FeedbackInput(
                    client_submission_id=UUID(int=430 + index),
                    kind="revision_comment",
                    comment=f"Existing {index}",
                ),
                clock=clock,
            )
        db.commit()

    barrier = Barrier(2)

    def submit(index: int):
        with Session(engine) as db:
            barrier.wait()
            try:
                result = submit_lecturer_review_feedback(
                    db,
                    secret,
                    FeedbackInput(
                        client_submission_id=UUID(int=450 + index),
                        kind="revision_comment",
                        comment=f"Competing {index}",
                    ),
                    clock=clock,
                )
                db.commit()
                return _json(result)["outcome"]
            except LecturerReviewFailure as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(submit, range(2)))

    assert outcomes.count("created") == 1
    assert outcomes.count(429) == 1
    with Session(engine) as db:
        assert db.query(LecturerReviewFeedback).count() == 10


def test_simultaneous_replacements_leave_one_active_final_secret(tmp_path: Path):
    database = tmp_path / "lecturer-review-replacement-race.db"
    engine, _fixture, _secret = _seed_issued_database(database)
    with Session(engine) as db:
        original_id = db.scalar(select(LecturerReviewLink.id))
    barrier = Barrier(2)

    def replace():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = replace_lecturer_review_link(
                    db,
                    original_id,
                    clock=DeterministicUtcClock(),
                )
                db.commit()
                return _value(result, "secret")
            except LecturerReviewFailure as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _item: replace(), range(2)))

    assert any(isinstance(item, str) for item in outcomes)
    assert all(isinstance(item, str) or item == 409 for item in outcomes)
    with Session(engine) as db:
        links = db.scalars(
            select(LecturerReviewLink).order_by(LecturerReviewLink.id)
        ).all()
        assert sum(link.status == "active" for link in links) == 1
        active = next(link for link in links if link.status == "active")
        for outcome in outcomes:
            if isinstance(outcome, str) and hashlib.sha256(
                outcome.encode("ascii")
            ).hexdigest() != active.secret_digest:
                _assert_public_unavailable(db, outcome)


def test_expiry_claim_wins_against_waiting_replacement(tmp_path: Path):
    database = tmp_path / "lecturer-review-expiry-replacement-race.db"
    engine, _fixture, secret = _seed_issued_database(database)
    with Session(engine) as db:
        link_id = db.scalar(select(LecturerReviewLink.id))
    expiry_claimed = Event()
    replacement_attempting = Event()
    expiry_clock = DeterministicUtcClock(FIXED_UTC + timedelta(days=3))

    def expire():
        with Session(engine) as db:
            try:
                get_public_lecturer_review(db, secret, clock=expiry_clock)
            except LecturerReviewFailure:
                expiry_claimed.set()
                assert replacement_attempting.wait(timeout=5)
                db.commit()

    def replace():
        assert expiry_claimed.wait(timeout=5)
        with Session(engine) as db:
            replacement_attempting.set()
            try:
                replace_lecturer_review_link(db, link_id, clock=expiry_clock)
                db.commit()
                return "replaced"
            except LecturerReviewFailure as exc:
                db.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        expiry_future = pool.submit(expire)
        replace_future = pool.submit(replace)
        expiry_future.result(timeout=10)
        outcome = replace_future.result(timeout=10)

    assert outcome == 409
    with Session(engine) as db:
        links = db.scalars(select(LecturerReviewLink)).all()
        assert len(links) == 1
        assert links[0].status == "expired"


def test_abandonment_waiting_feedback_fails_closed_and_terminalizes_link(
    tmp_path: Path,
):
    database = tmp_path / "lecturer-review-abandon-feedback-race.db"
    engine, fixture, secret = _seed_issued_database(database)
    with Session(engine) as db:
        overview = get_lifecycle_overview(db, fixture.semester_id)
        revision = overview["activeWorkingRevision"]
    ended = Event()
    feedback_attempting = Event()

    def abandon():
        with Session(engine) as db:
            transition_revision(
                db,
                fixture.working_revision_id,
                action="abandon",
                expected_revision_version=revision["revisionVersion"],
                expected_state_token=overview["stateToken"],
                confirmed=True,
            )
            ended.set()
            assert feedback_attempting.wait(timeout=5)
            db.commit()

    def feedback():
        assert ended.wait(timeout=5)
        return _submit_waiting_feedback(
            engine, secret, feedback_attempting, UUID(int=500)
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        end_future = pool.submit(abandon)
        feedback_future = pool.submit(feedback)
        end_future.result(timeout=10)
        assert feedback_future.result(timeout=10) == 404
    with Session(engine) as db:
        link = db.scalar(select(LecturerReviewLink))
        assert (link.status, link.end_reason) == ("revision_ended", "abandoned")
        assert db.query(LecturerReviewFeedback).count() == 0


def test_supersession_waiting_feedback_fails_closed_and_terminalizes_old_link(
    tmp_path: Path,
):
    database = tmp_path / "lecturer-review-supersede-feedback-race.db"
    engine, fixture, _secret = _seed_issued_database(database)
    old_secret = "Q" * 43
    with Session(engine) as db:
        old = LecturerReviewLink(
            schedule_revision_id=fixture.published_revision_id,
            lecturer_id=fixture.primary_lecturer_id,
            intended_lecturer_name="Ada Lovelace",
            secret_digest=__import__("hashlib").sha256(
                old_secret.encode("ascii")
            ).hexdigest(),
            duration_days=3,
            issued_at=FIXED_UTC,
            expires_at=FIXED_UTC + timedelta(days=3),
            status="active",
        )
        db.add(old)
        db.commit()
        overview = get_lifecycle_overview(db, fixture.semester_id)
        revision = overview["activeWorkingRevision"]
        preparation = prepare_publication(
            db,
            fixture.working_revision_id,
            revision["revisionVersion"],
            overview["stateToken"],
        )
    ended = Event()
    feedback_attempting = Event()

    def publish():
        with Session(engine) as db:
            transition_revision(
                db,
                fixture.working_revision_id,
                action="publish",
                expected_revision_version=revision["revisionVersion"],
                expected_state_token=overview["stateToken"],
                confirmed=True,
                publication_token=preparation["preparationToken"],
            )
            ended.set()
            assert feedback_attempting.wait(timeout=5)
            db.commit()

    def feedback():
        assert ended.wait(timeout=5)
        return _submit_waiting_feedback(
            engine, old_secret, feedback_attempting, UUID(int=510)
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        publish_future = pool.submit(publish)
        feedback_future = pool.submit(feedback)
        publish_future.result(timeout=10)
        assert feedback_future.result(timeout=10) == 404
    with Session(engine) as db:
        old = db.scalar(
            select(LecturerReviewLink).where(
                LecturerReviewLink.schedule_revision_id
                == fixture.published_revision_id
            )
        )
        assert (old.status, old.end_reason) == ("revision_ended", "superseded")
        assert db.query(LecturerReviewFeedback).count() == 0


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


def _seed_issued_database(database: Path):
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    initialize_database(engine)
    with Session(engine) as db:
        fixture = seed_lecturer_review_fixture(db)
        result = issue_lecturer_review_link(
            db,
            fixture.working_revision_id,
            fixture.primary_lecturer_id,
            duration_days=3,
            clock=DeterministicUtcClock(),
        )
        db.commit()
        secret = _value(result, "secret")
    return engine, fixture, secret


def _submit_waiting_feedback(
    engine,
    secret: str,
    attempting: Event,
    submission_id: UUID,
):
    with Session(engine) as db:
        attempting.set()
        try:
            submit_lecturer_review_feedback(
                db,
                secret,
                FeedbackInput(
                    client_submission_id=submission_id,
                    kind="revision_comment",
                    comment="Must lose to the lifecycle transition.",
                ),
                clock=DeterministicUtcClock(),
            )
            db.commit()
            return "accepted"
        except LecturerReviewFailure as exc:
            db.rollback()
            return exc.status_code


def _assert_public_unavailable(db: Session, secret: str) -> None:
    try:
        get_public_lecturer_review(
            db,
            secret,
            clock=DeterministicUtcClock(),
        )
    except LecturerReviewFailure as exc:
        assert exc.status_code == 404
        db.commit()
        return
    raise AssertionError("An earlier replacement secret remained usable.")
