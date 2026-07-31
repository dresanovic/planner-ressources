from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.models.planning import (
    Cohort,
    Course,
    DraftSchedule,
    DraftSession,
    ExamSession,
    Lecturer,
    LecturerReviewActivityEvent,
    LecturerReviewFeedback,
    LecturerReviewInvalidSourceState,
    LecturerReviewLink,
    Room,
    ScheduleRevision,
    Semester,
)
from app.schemas.lecturer_review import (
    FeedbackInput,
    FeedbackResult,
    IssuedLinkResult,
    PlannerReviewOverview,
    PublicReview,
)
from app.services.calendar_workspace import (
    CalendarWorkspaceError,
    get_calendar_workspace,
)


UTCClock = Callable[[], datetime]
TOKEN_SHAPE = re.compile(r"^[A-Za-z0-9_-]{43}$")
TIME_ZONE = "Europe/Vienna"
SOURCE_KEY_ENV = "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY"
WORKING_STATES = {"draft", "ready_for_review"}
PUBLIC_STATES = {"draft", "ready_for_review", "published"}


class LecturerReviewFailure(RuntimeError):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retry_after: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retry_after = retry_after


def source_fingerprint_key_from_environment(*, production: bool) -> bytes:
    configured = os.getenv(SOURCE_KEY_ENV)
    if configured is None or len(configured.encode("utf-8")) < 32:
        if production:
            raise RuntimeError(
                f"{SOURCE_KEY_ENV} must contain at least 256 bits of random key material."
            )
        configured = "local-development-only-source-key-" + ("0" * 32)
    return hashlib.sha256(configured.encode("utf-8")).digest()


def issue_lecturer_review_link(
    db: Session,
    revision_id: int,
    lecturer_id: int,
    *,
    duration_days: int = 3,
    clock: UTCClock | Any | None = None,
) -> IssuedLinkResult:
    if duration_days not in {1, 2, 3}:
        raise LecturerReviewFailure(
            422,
            "invalid_duration",
            "Review access must last one, two, or three days.",
        )
    revision = db.get(ScheduleRevision, revision_id)
    if revision is None:
        raise LecturerReviewFailure(404, "revision_not_found", "Revision not found.")

    _claim_semester(db, revision.semester_id)
    db.expire_all()
    revision = db.get(ScheduleRevision, revision_id)
    lecturer = db.get(Lecturer, lecturer_id)
    if revision is None or lecturer is None:
        raise LecturerReviewFailure(
            404, "review_scope_not_found", "Revision or lecturer not found."
        )
    if revision.state not in WORKING_STATES:
        raise LecturerReviewFailure(
            409,
            "revision_not_working",
            "Initial review access can be issued only for the Working revision.",
        )
    now = _now(clock)
    _materialize_due_expiry(db, revision_id, lecturer_id, now)
    if db.scalar(
        select(LecturerReviewLink.id).where(
            LecturerReviewLink.schedule_revision_id == revision_id,
            LecturerReviewLink.lecturer_id == lecturer_id,
            LecturerReviewLink.status == "active",
        )
    ):
        raise LecturerReviewFailure(
            409,
            "active_link_exists",
            "An active review link already exists for this lecturer and revision.",
        )
    if not _lecturer_has_live_assignments(db, revision.semester_id, lecturer_id):
        raise LecturerReviewFailure(
            422,
            "lecturer_has_no_assignments",
            "The lecturer has no current sessions in this revision.",
        )

    secret = secrets.token_urlsafe(32)
    digest = hashlib.sha256(secret.encode("ascii")).hexdigest()
    link = LecturerReviewLink(
        schedule_revision_id=revision.id,
        lecturer_id=lecturer.id,
        intended_lecturer_name=lecturer.name,
        secret_digest=digest,
        duration_days=duration_days,
        issued_at=now,
        expires_at=now + timedelta(days=duration_days),
        status="active",
    )
    db.add(link)
    try:
        db.flush()
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        raise LecturerReviewFailure(
            409,
            "active_link_exists",
            "An active review link already exists for this lecturer and revision.",
        ) from exc
    _event(
        db,
        "link_issued",
        now,
        link=link,
    )
    db.flush()
    overview = get_lecturer_review_overview(
        db, revision_id, clock=lambda: now, claim=False
    )
    return IssuedLinkResult(
        secret=secret,
        issued_link=_link_summary(link, now),
        overview=overview,
    )


def revoke_lecturer_review_link(
    db: Session,
    link_id: int,
    *,
    clock: UTCClock | Any | None = None,
) -> PlannerReviewOverview:
    link = db.get(LecturerReviewLink, link_id)
    if link is None:
        raise LecturerReviewFailure(404, "link_not_found", "Review link not found.")

    _claim_semester(db, link.schedule_revision.semester_id)
    db.expire_all()
    link = db.get(LecturerReviewLink, link_id)
    if link is None:
        raise LecturerReviewFailure(404, "link_not_found", "Review link not found.")

    now = _now(clock)
    _materialize_due_expiry(
        db,
        link.schedule_revision_id,
        link.lecturer_id,
        now,
    )
    db.flush()
    db.refresh(link)
    if link.status != "active":
        raise LecturerReviewFailure(
            409,
            "link_not_active",
            "Only an active review link can be revoked.",
        )

    link.status = "revoked"
    link.ended_at = now
    link.end_reason = "revoked"
    _event(db, "link_revoked", now, link=link, reason_code="revoked")
    db.flush()
    return get_lecturer_review_overview(
        db,
        link.schedule_revision_id,
        clock=lambda: now,
        claim=False,
    )


def replace_lecturer_review_link(
    db: Session,
    link_id: int,
    *,
    duration_days: int = 3,
    clock: UTCClock | Any | None = None,
) -> IssuedLinkResult:
    if duration_days not in {1, 2, 3}:
        raise LecturerReviewFailure(
            422,
            "invalid_duration",
            "Review access must last one, two, or three days.",
        )
    selected = db.get(LecturerReviewLink, link_id)
    if selected is None:
        raise LecturerReviewFailure(404, "link_not_found", "Review link not found.")

    _claim_semester(db, selected.schedule_revision.semester_id)
    db.expire_all()
    selected = db.get(LecturerReviewLink, link_id)
    if selected is None:
        raise LecturerReviewFailure(404, "link_not_found", "Review link not found.")

    now = _now(clock)
    revision = selected.schedule_revision
    _materialize_due_expiry(
        db,
        selected.schedule_revision_id,
        selected.lecturer_id,
        now,
    )
    db.flush()
    db.refresh(selected)
    active_id = db.scalar(
        select(LecturerReviewLink.id).where(
            LecturerReviewLink.schedule_revision_id
            == selected.schedule_revision_id,
            LecturerReviewLink.lecturer_id == selected.lecturer_id,
            LecturerReviewLink.status == "active",
        )
    )
    if active_id is not None and active_id != selected.id:
        raise LecturerReviewFailure(
            409,
            "replacement_conflict",
            "A newer active review link already exists.",
        )
    if selected.status not in {"active", "revoked"}:
        raise LecturerReviewFailure(
            409,
            "link_not_replaceable",
            "The selected review link can no longer be replaced.",
        )
    if not _revision_allows_replacement(db, revision):
        raise LecturerReviewFailure(
            409,
            "revision_not_reviewable",
            "The bound revision no longer accepts lecturer review access.",
        )

    earlier_active = list(
        db.scalars(
            select(LecturerReviewLink).where(
                LecturerReviewLink.schedule_revision_id
                == selected.schedule_revision_id,
                LecturerReviewLink.lecturer_id == selected.lecturer_id,
                LecturerReviewLink.status == "active",
            )
        )
    )
    # Release the database-enforced one-active-link slot inside this transaction.
    # No caller can observe this temporary state because the replacement and all
    # terminal states are committed atomically.
    for link in earlier_active:
        link.status = "revoked"
        link.ended_at = now
        link.end_reason = "revoked"
    db.flush()

    secret = secrets.token_urlsafe(32)
    replacement = LecturerReviewLink(
        schedule_revision_id=selected.schedule_revision_id,
        lecturer_id=selected.lecturer_id,
        intended_lecturer_name=selected.intended_lecturer_name,
        secret_digest=hashlib.sha256(secret.encode("ascii")).hexdigest(),
        duration_days=duration_days,
        issued_at=now,
        expires_at=now + timedelta(days=duration_days),
        status="active",
    )
    db.add(replacement)
    try:
        db.flush()
    except (IntegrityError, OperationalError) as exc:
        db.rollback()
        raise LecturerReviewFailure(
            409,
            "replacement_conflict",
            "The review link changed before replacement completed.",
        ) from exc

    links_to_replace = {
        link.id: link for link in [selected, *earlier_active]
    }.values()
    for link in links_to_replace:
        link.status = "replaced"
        link.ended_at = now
        link.end_reason = "replaced"
        link.replaced_by_id = replacement.id
        _event(
            db,
            "link_replaced",
            now,
            link=link,
            reason_code="replaced",
        )
    _event(db, "link_issued", now, link=replacement)
    db.flush()
    overview = get_lecturer_review_overview(
        db,
        replacement.schedule_revision_id,
        clock=lambda: now,
        claim=False,
    )
    return IssuedLinkResult(
        secret=secret,
        issued_link=_link_summary(replacement, now),
        overview=overview,
    )


def get_lecturer_review_overview(
    db: Session,
    revision_id: int,
    *,
    clock: UTCClock | Any | None = None,
    claim: bool = True,
) -> PlannerReviewOverview:
    revision = db.get(ScheduleRevision, revision_id)
    if revision is None:
        raise LecturerReviewFailure(404, "revision_not_found", "Revision not found.")
    now = _now(clock)
    if claim:
        _claim_semester(db, revision.semester_id)
        db.expire_all()
        revision = db.get(ScheduleRevision, revision_id)
        assert revision is not None
    _materialize_due_expiry(db, revision_id, None, now)

    lecturer_courses: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    lecturer_session_counts: dict[int, int] = defaultdict(int)
    assignments = (
        _published_assignment_rows(revision)
        if revision.state == "published"
        else [
            (course_id, _course_identity(db.get(Course, course_id)), lecturer_id)
            for course_id, lecturer_id in _live_assignment_pairs(
                db, revision.semester_id
            )
        ]
    )
    for course_id, course, lecturer_id in assignments:
        lecturer_courses[lecturer_id][course_id] = course
        lecturer_session_counts[lecturer_id] += 1
    lecturers = []
    for lecturer_id in sorted(lecturer_courses):
        lecturer = db.get(Lecturer, lecturer_id)
        if lecturer is None:
            continue
        courses = [
            lecturer_courses[lecturer_id][course_id]
            for course_id in sorted(lecturer_courses[lecturer_id])
        ]
        active = db.scalar(
            select(LecturerReviewLink.id).where(
                LecturerReviewLink.schedule_revision_id == revision_id,
                LecturerReviewLink.lecturer_id == lecturer_id,
                LecturerReviewLink.status == "active",
            )
        )
        lecturers.append(
            {
                "lecturerId": lecturer.id,
                "lecturerName": lecturer.name,
                "sessionCount": lecturer_session_counts[lecturer_id],
                "courses": courses,
                "initialIssueAllowed": (
                    revision.state in WORKING_STATES and active is None
                ),
            }
        )
    links = list(
        db.scalars(
            select(LecturerReviewLink)
            .where(LecturerReviewLink.schedule_revision_id == revision_id)
            .order_by(LecturerReviewLink.issued_at.desc(), LecturerReviewLink.id.desc())
        )
    )
    feedback = list(
        db.scalars(
            select(LecturerReviewFeedback)
            .join(LecturerReviewLink)
            .where(LecturerReviewLink.schedule_revision_id == revision_id)
            .order_by(LecturerReviewFeedback.submitted_at, LecturerReviewFeedback.id)
        )
    )
    groups = _planner_feedback_groups(db, feedback)
    impossible_count = sum(
        1 for item in feedback if item.kind == "impossible_session"
    )
    return PlannerReviewOverview.model_validate(
        {
            "revision": _revision_summary(revision),
            "lecturers": lecturers,
            "links": [_link_summary(link, now) for link in links],
            "feedbackAvailability": "complete",
            "totalFeedbackCount": len(feedback),
            "impossibleFlagCount": impossible_count,
            "feedbackGroups": groups,
        }
    )


def get_public_lecturer_review(
    db: Session,
    secret: str,
    *,
    clock: UTCClock | Any | None = None,
    source_host: str | None = None,
    source_key: bytes | None = None,
) -> PublicReview:
    now = _now(clock)
    source_key_value = source_key or source_fingerprint_key_from_environment(
        production=False
    )
    if source_host is not None and _invalid_source_is_blocked(
        db,
        source_host,
        source_key_value,
        now,
    ):
        _event(db, "access_rejected", now, reason_code="source_limited")
        db.flush()
        raise _public_unavailable()
    link = _resolve_link(db, secret)
    if link is None:
        if source_host is not None:
            _record_invalid_source(
                db,
                source_host,
                source_key_value,
                now,
            )
        _event(db, "access_rejected", now, reason_code=_secret_reason(secret))
        db.flush()
        raise _public_unavailable()

    _claim_semester(db, link.schedule_revision.semester_id)
    db.expire_all()
    link = db.scalar(
        select(LecturerReviewLink).where(
            LecturerReviewLink.secret_digest
            == hashlib.sha256(secret.encode("ascii")).hexdigest()
        )
    )
    if link is None or not _link_is_usable(db, link, now):
        db.flush()
        raise _public_unavailable()
    if _known_view_limited(db, link, now):
        _event(db, "access_rejected", now, link=link, reason_code="view_limited")
        db.flush()
        raise LecturerReviewFailure(
            429,
            "REVIEW_TEMPORARILY_UNAVAILABLE",
            "This review is temporarily unavailable. Try again later.",
            retry_after=300,
        )
    payload = _public_projection(db, link)
    _event(db, "access_accepted", now, link=link)
    db.flush()
    return PublicReview.model_validate(payload)


def submit_lecturer_review_feedback(
    db: Session,
    secret: str,
    payload: FeedbackInput,
    *,
    clock: UTCClock | Any | None = None,
    source_host: str | None = None,
    source_key: bytes | None = None,
) -> FeedbackResult:
    now = _now(clock)
    source_key_value = source_key or source_fingerprint_key_from_environment(
        production=False
    )
    if source_host is not None and _invalid_source_is_blocked(
        db,
        source_host,
        source_key_value,
        now,
    ):
        _event(db, "feedback_rejected", now, reason_code="source_limited")
        db.flush()
        raise _public_unavailable()
    link = _resolve_link(db, secret)
    if link is None:
        if source_host is not None:
            _record_invalid_source(
                db,
                source_host,
                source_key_value,
                now,
            )
        _event(db, "feedback_rejected", now, reason_code=_secret_reason(secret))
        db.flush()
        raise _public_unavailable()

    _claim_semester(db, link.schedule_revision.semester_id)
    db.expire_all()
    link = _resolve_link(db, secret)
    if link is None or not _link_is_usable(db, link, now):
        db.flush()
        raise _public_unavailable()

    if _feedback_limited(db, link, now):
        _event(
            db,
            "feedback_rejected",
            now,
            link=link,
            reason_code="feedback_limited",
        )
        db.flush()
        raise LecturerReviewFailure(
            429,
            "REVIEW_TEMPORARILY_UNAVAILABLE",
            "This review is temporarily unavailable. Try again later.",
            retry_after=60,
        )

    request_fingerprint = _feedback_fingerprint(payload)
    submission_id = str(payload.client_submission_id)
    existing = db.scalar(
        select(LecturerReviewFeedback).where(
            LecturerReviewFeedback.review_link_id == link.id,
            LecturerReviewFeedback.client_submission_id == submission_id,
        )
    )
    if existing is not None:
        if existing.request_fingerprint != request_fingerprint:
            _event(
                db,
                "feedback_rejected",
                now,
                link=link,
                reason_code="stale_session",
            )
            db.flush()
            raise LecturerReviewFailure(
                409,
                "REVIEW_REFRESH_REQUIRED",
                "The schedule changed. Reload the browser page or reopen the link before submitting feedback.",
            )
        _event(
            db,
            "feedback_accepted",
            now,
            link=link,
            feedback=existing,
            reason_code="idempotent_replay",
        )
        db.flush()
        return FeedbackResult(
            outcome="already_accepted",
            item=_public_feedback(existing),
        )

    session_kind: str | None = None
    source_session_id: int | None = None
    session_context: dict[str, Any] | None = None
    if payload.session_ref is not None:
        session_kind, raw_id = payload.session_ref.split(":", 1)
        source_session_id = int(raw_id)
        session_context = _current_session_context(
            db,
            link,
            session_kind,
            source_session_id,
        )
        if session_context is None:
            _event(
                db,
                "feedback_rejected",
                now,
                link=link,
                reason_code="out_of_scope",
            )
            db.flush()
            raise LecturerReviewFailure(
                409,
                "REVIEW_REFRESH_REQUIRED",
                "The schedule changed. Reload the browser page or reopen the link before submitting feedback.",
            )

    feedback = LecturerReviewFeedback(
        review_link=link,
        kind=str(payload.kind),
        session_kind=session_kind,
        source_session_id=source_session_id,
        comment_text=payload.comment,
        session_context=session_context,
        client_submission_id=submission_id,
        request_fingerprint=request_fingerprint,
        submitted_at=now,
    )
    db.add(feedback)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise LecturerReviewFailure(
            409,
            "REVIEW_REFRESH_REQUIRED",
            "The schedule changed. Reload the browser page or reopen the link before submitting feedback.",
        )
    _event(db, "feedback_accepted", now, link=link, feedback=feedback)
    db.flush()
    return FeedbackResult(outcome="created", item=_public_feedback(feedback))


def reject_invalid_feedback_attempt(
    db: Session,
    secret: str,
    *,
    clock: UTCClock | Any | None = None,
    source_host: str | None = None,
    source_key: bytes | None = None,
) -> None:
    now = _now(clock)
    source_key_value = source_key or source_fingerprint_key_from_environment(
        production=False
    )
    if source_host is not None and _invalid_source_is_blocked(
        db, source_host, source_key_value, now
    ):
        _event(db, "feedback_rejected", now, reason_code="source_limited")
        db.flush()
        raise _public_unavailable()
    link = _resolve_link(db, secret)
    if link is None:
        if source_host is not None:
            _record_invalid_source(db, source_host, source_key_value, now)
        _event(db, "feedback_rejected", now, reason_code=_secret_reason(secret))
        db.flush()
        raise _public_unavailable()
    _claim_semester(db, link.schedule_revision.semester_id)
    db.expire_all()
    link = _resolve_link(db, secret)
    if link is None or not _link_is_usable(db, link, now):
        db.flush()
        raise _public_unavailable()
    if _feedback_limited(db, link, now):
        _event(
            db,
            "feedback_rejected",
            now,
            link=link,
            reason_code="feedback_limited",
        )
        db.flush()
        raise LecturerReviewFailure(
            429,
            "REVIEW_TEMPORARILY_UNAVAILABLE",
            "This review is temporarily unavailable. Try again later.",
            retry_after=60,
        )
    _event(db, "feedback_rejected", now, link=link, reason_code="invalid_feedback")
    db.flush()
    raise LecturerReviewFailure(
        422,
        "INVALID_FEEDBACK",
        "Feedback must match the current review session.",
    )


def cleanup_invalid_source_states(
    db: Session,
    *,
    clock: UTCClock | Any | None = None,
) -> int:
    now = _now(clock)
    cutoff = now - timedelta(minutes=14)
    result = db.execute(
        delete(LecturerReviewInvalidSourceState).where(
            LecturerReviewInvalidSourceState.last_relevant_at <= cutoff,
            (
                LecturerReviewInvalidSourceState.blocked_until.is_(None)
                | (LecturerReviewInvalidSourceState.blocked_until <= now)
            ),
        ).execution_options(synchronize_session=False)
    )
    return int(result.rowcount or 0)


def terminalize_revision_links(
    db: Session,
    revision_id: int,
    *,
    reason: str,
    clock: UTCClock | Any | None = None,
) -> None:
    if reason not in {"abandoned", "superseded"}:
        raise ValueError("Unsupported terminal revision reason.")
    now = _now(clock)
    links = list(
        db.scalars(
            select(LecturerReviewLink).where(
                LecturerReviewLink.schedule_revision_id == revision_id,
                LecturerReviewLink.status == "active",
            )
        )
    )
    for link in links:
        link.status = "revision_ended"
        link.ended_at = now
        link.end_reason = reason
        _event(db, "revision_ended", now, link=link, reason_code=reason)


def _revision_allows_replacement(
    db: Session,
    revision: ScheduleRevision,
) -> bool:
    if revision.state in WORKING_STATES:
        active_id = db.scalar(
            select(ScheduleRevision.id).where(
                ScheduleRevision.semester_id == revision.semester_id,
                ScheduleRevision.state.in_(WORKING_STATES),
            )
        )
        return active_id == revision.id
    if revision.state == "published":
        current_id = db.scalar(
            select(ScheduleRevision.id).where(
                ScheduleRevision.semester_id == revision.semester_id,
                ScheduleRevision.state == "published",
            )
        )
        return current_id == revision.id
    return False


def _public_projection(db: Session, link: LecturerReviewLink) -> dict[str, Any]:
    revision = link.schedule_revision
    if revision.state in WORKING_STATES:
        courses = _live_public_courses(db, revision.semester_id, link.lecturer_id)
    elif revision.state == "published":
        courses = _published_public_courses(db, revision, link.lecturer_id)
    else:
        raise _public_unavailable()
    try:
        workspace = get_calendar_workspace(
            db, revision.semester_id, revision.id
        )
    except CalendarWorkspaceError as exc:
        raise _public_unavailable() from exc
    validation_findings = _safe_validation_projection(workspace, courses)
    validation_availability = _validation_availability(workspace)
    semester = revision.semester
    return {
        "intendedLecturer": link.intended_lecturer_name,
        "identityDisclaimer": (
            f"This link is intended for {link.intended_lecturer_name}; "
            "it does not authenticate the person using it."
        ),
        "revision": _revision_summary(revision),
        "accessExpiresAt": _iso(link.expires_at),
        "timeZone": TIME_ZONE,
        "semesterStartDate": semester.start_date.isoformat(),
        "semesterEndDate": semester.end_date.isoformat(),
        "validationAvailability": validation_availability,
        "validationFindings": validation_findings,
        "filterFacets": _public_filter_facets(
            revision,
            courses,
            validation_findings,
            validation_availability,
        ),
        "courses": courses,
        "submittedFeedback": [
            _public_feedback(item)
            for item in sorted(
                link.feedback_items, key=lambda row: (row.submitted_at, row.id)
            )
        ],
    }


def _live_public_courses(
    db: Session, semester_id: int, lecturer_id: int
) -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    teaching = list(
        db.scalars(
            select(DraftSession)
            .join(DraftSchedule)
            .where(
                DraftSchedule.semester_id == semester_id,
                DraftSession.lecturer_id == lecturer_id,
            )
            .order_by(DraftSession.date, DraftSession.start_time, DraftSession.id)
        )
    )
    exams = list(
        db.scalars(
            select(ExamSession)
            .where(
                ExamSession.semester_id == semester_id,
                ExamSession.lecturer_id == lecturer_id,
            )
            .order_by(ExamSession.exam_date, ExamSession.start_time, ExamSession.id)
        )
    )
    for session in teaching:
        course = db.get(Course, session.course_id)
        room = db.get(Room, session.room_id)
        cohort = db.get(Cohort, session.cohort_id)
        if course is None or room is None or cohort is None:
            raise _public_unavailable()
        entry = grouped.setdefault(course.id, _public_course(course))
        entry["sessions"].append(
            {
                "sessionRef": f"teaching:{session.id}",
                "sessionKind": "teaching",
                "sourceSessionId": session.id,
                "courseRef": f"course:{course.id}",
                "sessionType": "Lecture",
                "date": session.date.isoformat(),
                "startTime": _clock_text(session.start_time),
                "endTime": _clock_text(session.end_time),
                "timeZone": TIME_ZONE,
                "roomName": room.name,
                "roomRef": f"room:{room.id}",
                "cohortName": cohort.name,
                "teachingUnits": session.units,
                "examDurationMinutes": None,
                "validationFindingRefs": [],
            }
        )
    for session in exams:
        course = db.get(Course, session.course_id)
        room = db.get(Room, session.room_id)
        cohort = db.get(Cohort, session.cohort_id)
        if course is None or room is None or cohort is None:
            raise _public_unavailable()
        entry = grouped.setdefault(course.id, _public_course(course))
        entry["sessions"].append(
            {
                "sessionRef": f"exam:{session.id}",
                "sessionKind": "exam",
                "sourceSessionId": session.id,
                "courseRef": f"course:{course.id}",
                "sessionType": session.exam_type,
                "date": session.exam_date.isoformat(),
                "startTime": _clock_text(session.start_time),
                "endTime": _clock_text(session.end_time),
                "timeZone": TIME_ZONE,
                "roomName": room.name,
                "roomRef": f"room:{room.id}",
                "cohortName": cohort.name,
                "teachingUnits": None,
                "examDurationMinutes": session.duration_minutes,
                "validationFindingRefs": [],
            }
        )
    for course in grouped.values():
        course["sessions"].sort(
            key=lambda item: (
                item["date"],
                item["startTime"],
                item["sessionKind"],
                item["sourceSessionId"],
            )
        )
    return [grouped[key] for key in sorted(grouped)]


def _published_public_courses(
    db: Session, revision: ScheduleRevision, lecturer_id: int
) -> list[dict[str, Any]]:
    snapshot = revision.snapshot_document
    if not isinstance(snapshot, dict):
        raise _public_unavailable()
    grouped: dict[int, dict[str, Any]] = {}
    for source in snapshot.get("courses", []):
        course_id = source.get("sourceCourseId")
        if not isinstance(course_id, int):
            raise _public_unavailable()
        for session in source.get("teachingSessions", []):
            lecturer = session.get("lecturer", {})
            if lecturer.get("sourceId") != lecturer_id:
                continue
            room = session.get("room", {})
            cohort = source.get("cohort", {})
            entry = grouped.setdefault(
                course_id,
                {
                    "sourceCourseId": course_id,
                    "courseRef": f"course:{course_id}",
                    "code": f"COURSE-{course_id}",
                    "title": source.get("name"),
                    "cohortName": cohort.get("name"),
                    "studyType": source.get("studyType", {}).get("name"),
                    "sessions": [],
                },
            )
            entry["sessions"].append(
                {
                    "sessionRef": f"teaching:{session['sourceSessionId']}",
                    "sessionKind": "teaching",
                    "sourceSessionId": session["sourceSessionId"],
                    "courseRef": f"course:{course_id}",
                    "sessionType": "Lecture",
                    "date": session["date"],
                    "startTime": _clock_text(session["startTime"]),
                    "endTime": _clock_text(session["endTime"]),
                    "timeZone": TIME_ZONE,
                    "roomName": room.get("name"),
                    "roomRef": f"room:{room.get('sourceId')}",
                    "cohortName": cohort.get("name"),
                    "teachingUnits": session.get("units"),
                    "examDurationMinutes": None,
                    "validationFindingRefs": [],
                }
            )
    for exam in snapshot.get("examSessions", []):
        lecturer = exam.get("lecturer", {})
        if lecturer.get("sourceId") != lecturer_id:
            continue
        course = exam.get("course", {})
        course_id = course.get("sourceId")
        if not isinstance(course_id, int):
            raise _public_unavailable()
        entry = grouped.setdefault(
            course_id,
            {
                "sourceCourseId": course_id,
                "courseRef": f"course:{course_id}",
                "code": f"COURSE-{course_id}",
                "title": course.get("name"),
                "cohortName": exam.get("cohort", {}).get("name"),
                "studyType": _published_study_type(
                    db, snapshot, course_id
                ),
                "sessions": [],
            },
        )
        entry["sessions"].append(
            {
                "sessionRef": f"exam:{exam['sourceExamId']}",
                "sessionKind": "exam",
                "sourceSessionId": exam["sourceExamId"],
                "courseRef": f"course:{course_id}",
                "sessionType": exam.get("examType") or "Exam",
                "date": exam["examDate"],
                "startTime": _clock_text(exam["startTime"]),
                "endTime": _clock_text(exam["endTime"]),
                "timeZone": TIME_ZONE,
                "roomName": exam.get("room", {}).get("name"),
                "roomRef": f"room:{exam.get('room', {}).get('sourceId')}",
                "cohortName": exam.get("cohort", {}).get("name"),
                "teachingUnits": None,
                "examDurationMinutes": exam.get("durationMinutes"),
                "validationFindingRefs": [],
            }
        )
    for course in grouped.values():
        if (
            not all(
                isinstance(course.get(field), str)
                for field in (
                    "courseRef",
                    "title",
                    "cohortName",
                    "studyType",
                )
            )
            or any(
                not all(
                    isinstance(session.get(field), str)
                    for field in (
                        "sessionRef",
                        "sessionType",
                        "date",
                        "startTime",
                        "endTime",
                        "roomName",
                        "roomRef",
                        "cohortName",
                    )
                )
                for session in course["sessions"]
            )
        ):
            raise _public_unavailable()
        course["sessions"].sort(key=lambda item: (item["date"], item["startTime"]))
    return [grouped[key] for key in sorted(grouped)]


def _published_study_type(
    db: Session, snapshot: dict[str, Any], course_id: int
) -> str | None:
    for source in snapshot.get("courses", []):
        if source.get("sourceCourseId") == course_id:
            value = source.get("studyType", {}).get("name")
            if isinstance(value, str) and value:
                return value
    course = db.get(Course, course_id)
    if course is not None and course.study_type is not None:
        return course.study_type.name
    return None


_PUBLIC_FINDING_CATEGORIES = {
    "lecturer_conflict",
    "room_conflict",
    "cohort_conflict",
    "room_capacity",
    "holiday",
    "exam_validity",
}

_PUBLIC_FINDING_MESSAGES = {
    "lecturer_conflict": "This session overlaps another lecturer assignment.",
    "room_conflict": "This session overlaps another use of the assigned room.",
    "cohort_conflict": "This session overlaps another assignment for the cohort.",
    "room_capacity": "The assigned room may not have enough capacity.",
    "holiday": "This session falls on an institution holiday.",
    "exam_validity": "This exam needs review against the current exam rules.",
    "other": "This session has a current validation item to review.",
}


def _safe_validation_projection(
    workspace: dict[str, Any],
    courses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sessions = [
        session for course in courses for session in course["sessions"]
    ]
    scoped_refs = {session["sessionRef"] for session in sessions}
    finding_refs_by_session: dict[str, list[str]] = {
        ref: [] for ref in scoped_refs
    }
    safe_findings: list[dict[str, Any]] = []
    for finding in workspace.get("validationFindings", []):
        affected = sorted(
            scoped_refs.intersection(
                finding.get("affectedOccurrenceRefs", [])
            )
        )
        if not affected:
            continue
        category = finding.get("category")
        if category not in _PUBLIC_FINDING_CATEGORIES:
            category = "other"
        source_ref = str(finding.get("findingRef", "finding"))
        digest = hashlib.sha256(
            f"{source_ref}|{'|'.join(affected)}".encode("utf-8")
        ).hexdigest()[:20]
        safe_ref = f"public-finding:{digest}"
        safe_findings.append(
            {
                "findingRef": safe_ref,
                "category": category,
                "message": _PUBLIC_FINDING_MESSAGES[category],
                "affectedSessionRefs": affected,
            }
        )
        for session_ref in affected:
            finding_refs_by_session[session_ref].append(safe_ref)
    safe_findings.sort(key=lambda row: row["findingRef"])
    for session in sessions:
        session["validationFindingRefs"] = sorted(
            finding_refs_by_session[session["sessionRef"]]
        )
    return safe_findings


def _validation_availability(workspace: dict[str, Any]) -> str:
    status = (
        workspace.get("sectionStatus", {})
        .get("validationFindings", {})
        .get("availability")
    )
    if status == "available":
        return "complete"
    if status == "partial":
        return "partial"
    return "unavailable"


def _public_filter_facets(
    revision: ScheduleRevision,
    courses: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    validation_availability: str,
) -> dict[str, list[dict[str, str]]]:
    sessions = [
        session for course in courses for session in course["sessions"]
    ]

    def facets(values: list[tuple[str, str]]) -> list[dict[str, str]]:
        return [
            {"value": value, "label": label}
            for value, label in sorted(set(values), key=lambda item: item[1])
        ]

    validation_values = [
        (
            finding["category"],
            finding["category"].replace("_", " ").title(),
        )
        for finding in findings
    ]
    if (
        validation_availability == "complete"
        and any(not session["validationFindingRefs"] for session in sessions)
    ):
        validation_values.append(("none", "No current issue"))
    return {
        "courses": facets(
            [
                (
                    course["courseRef"],
                    f"{course['code']} — {course['title']}",
                )
                for course in courses
            ]
        ),
        "cohorts": facets(
            [
                (course["cohortName"], course["cohortName"])
                for course in courses
            ]
        ),
        "rooms": facets(
            [
                (session["roomRef"], session["roomName"])
                for session in sessions
            ]
        ),
        "studyTypes": facets(
            [
                (course["studyType"], course["studyType"])
                for course in courses
            ]
        ),
        "sessionTypes": facets(
            [
                (
                    session["sessionKind"],
                    session["sessionKind"].title(),
                )
                for session in sessions
            ]
        ),
        "lifecycleContexts": [
            {
                "value": revision.state,
                "label": revision.state.replace("_", " ").title(),
            }
        ],
        "validationCategories": facets(validation_values),
    }


def _link_is_usable(db: Session, link: LecturerReviewLink, now: datetime) -> bool:
    if link.status != "active":
        _event(
            db,
            "access_rejected",
            now,
            link=link,
            reason_code=link.end_reason or link.status,
        )
        return False
    if now >= _as_utc(link.expires_at):
        link.status = "expired"
        link.ended_at = _as_utc(link.expires_at)
        link.end_reason = "expired"
        if not db.scalar(
            select(LecturerReviewActivityEvent.id).where(
                LecturerReviewActivityEvent.review_link_id == link.id,
                LecturerReviewActivityEvent.event_type == "link_expired",
            )
        ):
            _event(db, "link_expired", _as_utc(link.expires_at), link=link, reason_code="expired")
        _event(db, "access_rejected", now, link=link, reason_code="expired")
        return False
    revision = link.schedule_revision
    if revision.state not in PUBLIC_STATES:
        _event(
            db,
            "access_rejected",
            now,
            link=link,
            reason_code=(
                "abandoned" if revision.state == "abandoned" else "superseded"
            ),
        )
        return False
    if revision.state in WORKING_STATES:
        active_id = db.scalar(
            select(ScheduleRevision.id).where(
                ScheduleRevision.semester_id == revision.semester_id,
                ScheduleRevision.state.in_(WORKING_STATES),
            )
        )
        if active_id != revision.id:
            return False
    if revision.state == "published":
        published_id = db.scalar(
            select(ScheduleRevision.id).where(
                ScheduleRevision.semester_id == revision.semester_id,
                ScheduleRevision.state == "published",
            )
        )
        if published_id != revision.id:
            return False
    return True


def _known_view_limited(
    db: Session, link: LecturerReviewLink, now: datetime
) -> bool:
    if link.access_blocked_until is not None and now < _as_utc(
        link.access_blocked_until
    ):
        return True
    window_start = now - timedelta(minutes=5)
    count = db.scalar(
        select(func.count(LecturerReviewActivityEvent.id)).where(
            LecturerReviewActivityEvent.review_link_id == link.id,
            LecturerReviewActivityEvent.event_type == "access_accepted",
            LecturerReviewActivityEvent.occurred_at >= window_start,
        )
    ) or 0
    if count >= 120:
        link.access_blocked_until = now + timedelta(minutes=5)
        _event(
            db,
            "misuse_limit_activated",
            now,
            link=link,
            reason_code="view_limited",
        )
        db.flush()
        return True
    return False


def _feedback_limited(
    db: Session, link: LecturerReviewLink, now: datetime
) -> bool:
    feedback_events = ("feedback_accepted", "feedback_rejected")
    minute_count = db.scalar(
        select(func.count(LecturerReviewActivityEvent.id)).where(
            LecturerReviewActivityEvent.review_link_id == link.id,
            LecturerReviewActivityEvent.event_type.in_(feedback_events),
            LecturerReviewActivityEvent.occurred_at > now - timedelta(minutes=1),
        )
    ) or 0
    hour_count = db.scalar(
        select(func.count(LecturerReviewActivityEvent.id)).where(
            LecturerReviewActivityEvent.review_link_id == link.id,
            LecturerReviewActivityEvent.event_type.in_(feedback_events),
            LecturerReviewActivityEvent.occurred_at > now - timedelta(hours=1),
        )
    ) or 0
    return minute_count >= 10 or hour_count >= 60


def _feedback_fingerprint(payload: FeedbackInput) -> str:
    canonical = json.dumps(
        {
            "kind": str(payload.kind),
            "sessionRef": payload.session_ref,
            "comment": payload.comment,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _current_session_context(
    db: Session,
    link: LecturerReviewLink,
    session_kind: str,
    source_session_id: int,
) -> dict[str, Any] | None:
    revision = link.schedule_revision
    if revision.state in WORKING_STATES:
        model = DraftSession if session_kind == "teaching" else ExamSession
        session = db.get(model, source_session_id)
        if session is None or session.lecturer_id != link.lecturer_id:
            return None
        if session_kind == "teaching":
            draft = db.get(DraftSchedule, session.draft_schedule_id)
            if draft is None or draft.semester_id != revision.semester_id:
                return None
            date_value = session.date
            session_type = "Lecture"
        else:
            if session.semester_id != revision.semester_id:
                return None
            date_value = session.exam_date
            session_type = session.exam_type
        course = db.get(Course, session.course_id)
        room = db.get(Room, session.room_id)
        cohort = db.get(Cohort, session.cohort_id)
        if course is None or room is None or cohort is None:
            return None
        return {
            "sessionRef": f"{session_kind}:{source_session_id}",
            "sessionKind": session_kind,
            "sourceSessionId": source_session_id,
            "sessionType": session_type,
            "courseSourceId": course.id,
            "courseCode": f"COURSE-{course.id}",
            "courseTitle": course.name,
            "date": date_value.isoformat(),
            "startTime": _clock_text(session.start_time),
            "endTime": _clock_text(session.end_time),
            "timeZone": TIME_ZONE,
            "roomName": room.name,
            "cohortName": cohort.name,
            "studyType": course.study_type.name,
            "teachingUnits": (
                session.units if session_kind == "teaching" else None
            ),
            "examDurationMinutes": (
                session.duration_minutes if session_kind == "exam" else None
            ),
        }
    if revision.state != "published":
        return None
    for course in _published_public_courses(db, revision, link.lecturer_id):
        for session in course["sessions"]:
            if session["sessionRef"] == f"{session_kind}:{source_session_id}":
                return {
                    "sessionRef": session["sessionRef"],
                    "sessionKind": session["sessionKind"],
                    "sourceSessionId": session["sourceSessionId"],
                    "sessionType": session["sessionType"],
                    "courseSourceId": course["sourceCourseId"],
                    "courseCode": course["code"],
                    "courseTitle": course["title"],
                    "date": session["date"],
                    "startTime": session["startTime"],
                    "endTime": session["endTime"],
                    "timeZone": session["timeZone"],
                    "roomName": session["roomName"],
                    "cohortName": session["cohortName"],
                    "studyType": course["studyType"],
                    "teachingUnits": session["teachingUnits"],
                    "examDurationMinutes": session["examDurationMinutes"],
                }
    return None


def _record_invalid_source(
    db: Session, host: str, key: bytes, now: datetime
) -> None:
    fingerprint = _source_fingerprint(host, key)
    # The no-op upsert acquires SQLite's writer slot before the state is read.
    # Requests for the same source therefore serialize across sessions and
    # workers instead of racing through an ORM read/modify/write sequence.
    db.execute(
        sqlite_insert(LecturerReviewInvalidSourceState)
        .values(
            source_fingerprint=fingerprint,
            attempt_timestamps=[],
            last_relevant_at=now,
        )
        .on_conflict_do_nothing(
            index_elements=[LecturerReviewInvalidSourceState.source_fingerprint]
        )
    )
    db.expire_all()
    row = db.get(LecturerReviewInvalidSourceState, fingerprint)
    assert row is not None
    cutoff = now - timedelta(minutes=5)
    attempts = [
        item
        for item in row.attempt_timestamps
        if _parse_timestamp(item) > cutoff
    ]
    if row.blocked_until is not None and now < _as_utc(row.blocked_until):
        row.last_relevant_at = now
    else:
        attempts.append(_iso(now))
        attempts = attempts[-20:]
        row.attempt_timestamps = attempts
        row.last_relevant_at = now
        if len(attempts) >= 20:
            row.blocked_until = now + timedelta(minutes=10)
            _event(
                db,
                "misuse_limit_activated",
                now,
                reason_code="source_limited",
            )
    db.flush()


def _invalid_source_is_blocked(
    db: Session,
    host: str,
    key: bytes,
    now: datetime,
) -> bool:
    row = db.get(
        LecturerReviewInvalidSourceState,
        _source_fingerprint(host, key),
    )
    if (
        row is None
        or row.blocked_until is None
        or now >= _as_utc(row.blocked_until)
    ):
        return False
    row.last_relevant_at = now
    db.flush()
    return True


def _source_fingerprint(host: str, key: bytes) -> str:
    normalized = _normalize_source_host(host)
    return hmac.new(
        key,
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _normalize_source_host(host: str) -> str:
    candidate = host.strip()
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return candidate.casefold()
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        return address.ipv4_mapped.compressed
    return address.compressed.casefold()


def _resolve_link(db: Session, secret: str) -> LecturerReviewLink | None:
    if not TOKEN_SHAPE.fullmatch(secret):
        return None
    digest = _secret_digest(secret)
    return db.scalar(
        select(LecturerReviewLink).where(
            LecturerReviewLink.secret_digest == digest
        )
    )


def is_stored_lecturer_review_secret(db: Session, secret: str) -> bool:
    """Classify a bearer without changing link state or recording activity."""

    if not TOKEN_SHAPE.fullmatch(secret):
        return False
    return (
        db.scalar(
            select(LecturerReviewLink.id).where(
                LecturerReviewLink.secret_digest == _secret_digest(secret)
            )
        )
        is not None
    )


def _secret_digest(secret: str) -> str:
    return hashlib.sha256(secret.encode("ascii")).hexdigest()


def _materialize_due_expiry(
    db: Session,
    revision_id: int,
    lecturer_id: int | None,
    now: datetime,
) -> None:
    statement = select(LecturerReviewLink).where(
        LecturerReviewLink.schedule_revision_id == revision_id,
        LecturerReviewLink.status == "active",
        LecturerReviewLink.expires_at <= now,
    )
    if lecturer_id is not None:
        statement = statement.where(LecturerReviewLink.lecturer_id == lecturer_id)
    for link in db.scalars(statement):
        link.status = "expired"
        link.ended_at = _as_utc(link.expires_at)
        link.end_reason = "expired"
        _event(
            db,
            "link_expired",
            _as_utc(link.expires_at),
            link=link,
            reason_code="expired",
        )


def _live_assignment_pairs(
    db: Session, semester_id: int
) -> list[tuple[int, int]]:
    teaching = list(
        db.execute(
            select(DraftSession.course_id, DraftSession.lecturer_id)
            .join(DraftSchedule)
            .where(DraftSchedule.semester_id == semester_id)
        )
    )
    exams = list(
        db.execute(
            select(ExamSession.course_id, ExamSession.lecturer_id).where(
                ExamSession.semester_id == semester_id
            )
        )
    )
    return [(int(course), int(lecturer)) for course, lecturer in teaching + exams]


def _published_assignment_rows(
    revision: ScheduleRevision,
) -> list[tuple[int, dict[str, Any], int]]:
    snapshot = revision.snapshot_document
    if not isinstance(snapshot, dict):
        raise LecturerReviewFailure(
            409, "scope_incomplete", "Review scope could not be confirmed."
        )
    rows: list[tuple[int, dict[str, Any], int]] = []
    for source in snapshot.get("courses", []):
        course_id = source.get("sourceCourseId")
        title = source.get("name")
        if not isinstance(course_id, int) or not isinstance(title, str):
            raise LecturerReviewFailure(
                409, "scope_incomplete", "Review scope could not be confirmed."
            )
        identity = {
            "sourceCourseId": course_id,
            "code": f"COURSE-{course_id}",
            "title": title,
        }
        for session in source.get("teachingSessions", []):
            lecturer_id = session.get("lecturer", {}).get("sourceId")
            if isinstance(lecturer_id, int):
                rows.append((course_id, identity, lecturer_id))
    for exam in snapshot.get("examSessions", []):
        course = exam.get("course", {})
        course_id = course.get("sourceId")
        title = course.get("name")
        lecturer_id = exam.get("lecturer", {}).get("sourceId")
        if (
            not isinstance(course_id, int)
            or not isinstance(title, str)
            or not isinstance(lecturer_id, int)
        ):
            raise LecturerReviewFailure(
                409, "scope_incomplete", "Review scope could not be confirmed."
            )
        rows.append(
            (
                course_id,
                {
                    "sourceCourseId": course_id,
                    "code": f"COURSE-{course_id}",
                    "title": title,
                },
                lecturer_id,
            )
        )
    return rows


def _lecturer_has_live_assignments(
    db: Session, semester_id: int, lecturer_id: int
) -> bool:
    return any(
        assigned == lecturer_id
        for _course, assigned in _live_assignment_pairs(db, semester_id)
    )


def _revision_summary(revision: ScheduleRevision) -> dict[str, Any]:
    return {
        "id": revision.id,
        "semesterId": revision.semester_id,
        "semesterName": revision.semester.name,
        "label": f"Revision {revision.revision_number}",
        "state": revision.state,
    }


def _course_identity(course: Course | None) -> dict[str, Any]:
    if course is None:
        raise LecturerReviewFailure(
            409, "scope_incomplete", "Review scope could not be confirmed."
        )
    return {
        "sourceCourseId": course.id,
        "code": f"COURSE-{course.id}",
        "title": course.name,
    }


def _public_course(course: Course) -> dict[str, Any]:
    return {
        **_course_identity(course),
        "courseRef": f"course:{course.id}",
        "cohortName": course.cohort.name,
        "studyType": course.study_type.name,
        "sessions": [],
    }


def _link_summary(link: LecturerReviewLink, now: datetime) -> dict[str, Any]:
    effective_status = link.status
    if effective_status == "active" and now >= _as_utc(link.expires_at):
        effective_status = "expired"
    return {
        "id": link.id,
        "revisionId": link.schedule_revision_id,
        "lecturerId": link.lecturer_id,
        "intendedLecturerName": link.intended_lecturer_name,
        "durationDays": link.duration_days,
        "issuedAt": _iso(link.issued_at),
        "expiresAt": _iso(link.expires_at),
        "timeZone": TIME_ZONE,
        "status": effective_status,
        "endedAt": _iso(link.ended_at) if link.ended_at is not None else None,
        "replaceAllowed": (
            link.status == "active"
            and link.schedule_revision.state in PUBLIC_STATES
        ),
    }


def _planner_feedback_groups(
    db: Session, feedback: list[LecturerReviewFeedback]
) -> list[dict[str, Any]]:
    groups: dict[str, list[LecturerReviewFeedback]] = defaultdict(list)
    for item in feedback:
        ref = (
            "revision"
            if item.session_kind is None
            else f"{item.session_kind}:{item.source_session_id}"
        )
        groups[ref].append(item)
    result = []
    for ref, items in groups.items():
        first = items[0]
        context = first.session_context
        result.append(
            {
                "groupRef": ref,
                "level": "revision" if ref == "revision" else "session",
                "sessionContext": context,
                "currentNavigation": (
                    {
                        "revisionId": first.review_link.schedule_revision_id,
                        "occurrenceRef": ref,
                    }
                    if context is not None
                    and _current_session_exists(db, first.review_link, ref)
                    else None
                ),
                "impossibleFlagCount": sum(
                    1 for item in items if item.kind == "impossible_session"
                ),
                "items": [
                    {
                        "id": item.id,
                        "intendedLecturerId": item.review_link.lecturer_id,
                        "intendedLecturerName": item.review_link.intended_lecturer_name,
                        "attribution": (
                            "Submitted through the review link intended for "
                            f"{item.review_link.intended_lecturer_name}; "
                            "identity was not authenticated."
                        ),
                        "kind": item.kind,
                        "comment": item.comment_text,
                        "sessionContext": item.session_context,
                        "submittedAt": _iso(item.submitted_at),
                        "timeZone": TIME_ZONE,
                    }
                    for item in items
                ],
            }
        )
    return sorted(result, key=lambda item: (item["groupRef"] != "revision", item["groupRef"]))


def _current_session_exists(
    db: Session, link: LecturerReviewLink, session_ref: str
) -> bool:
    revision = link.schedule_revision
    if not _revision_allows_replacement(db, revision):
        return False
    if revision.state == "published":
        return any(
            session["sessionRef"] == session_ref
            for course in _published_public_courses(
                db, revision, link.lecturer_id
            )
            for session in course["sessions"]
        )
    kind, raw_id = session_ref.split(":", 1)
    model = DraftSession if kind == "teaching" else ExamSession
    item = db.get(model, int(raw_id))
    if item is None or item.lecturer_id != link.lecturer_id:
        return False
    if kind == "teaching":
        draft = db.get(DraftSchedule, item.draft_schedule_id)
        return draft is not None and draft.semester_id == revision.semester_id
    return item.semester_id == revision.semester_id


def _public_feedback(item: LecturerReviewFeedback) -> dict[str, Any]:
    return {
        "id": item.id,
        "kind": item.kind,
        "sessionRef": (
            f"{item.session_kind}:{item.source_session_id}"
            if item.session_kind is not None
            else None
        ),
        "comment": item.comment_text,
        "submittedAt": _iso(item.submitted_at),
        "timeZone": TIME_ZONE,
    }


def _event(
    db: Session,
    event_type: str,
    occurred_at: datetime,
    *,
    link: LecturerReviewLink | None = None,
    feedback: LecturerReviewFeedback | None = None,
    reason_code: str | None = None,
) -> None:
    db.add(
        LecturerReviewActivityEvent(
            event_type=event_type,
            review_link=link,
            schedule_revision_id=(
                link.schedule_revision_id if link is not None else None
            ),
            lecturer_id=link.lecturer_id if link is not None else None,
            feedback=feedback,
            reason_code=reason_code,
            occurred_at=occurred_at,
        )
    )


def _claim_semester(db: Session, semester_id: int) -> None:
    db.execute(
        update(Semester)
        .where(Semester.id == semester_id)
        .values(id=Semester.id)
    )


def _secret_reason(secret: str) -> str:
    return "unknown_secret" if TOKEN_SHAPE.fullmatch(secret) else "malformed_secret"


def _public_unavailable() -> LecturerReviewFailure:
    return LecturerReviewFailure(
        404,
        "REVIEW_UNAVAILABLE",
        "This review is unavailable. Contact the planner for a new link.",
    )


def _now(clock: UTCClock | Any | None) -> datetime:
    if clock is None:
        return datetime.now(timezone.utc)
    value = clock() if callable(clock) else clock.now()
    return _as_utc(value)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _clock_text(value: Any) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value)[:5]
