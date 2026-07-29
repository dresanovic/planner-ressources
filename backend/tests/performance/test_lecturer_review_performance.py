from __future__ import annotations

import hashlib
import platform
import sqlite3
import sys
from datetime import date, time, timedelta
from time import perf_counter
from uuid import UUID

import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.db.session import get_db
from app.main import app
from app.models.planning import (
    Cohort,
    Course,
    DraftSchedule,
    DraftSession,
    ExamSession,
    LecturerReviewFeedback,
)
from app.schemas.lecturer_review import FeedbackInput
from app.services.lecturer_review import (
    issue_lecturer_review_link,
    submit_lecturer_review_feedback,
)
from app.services.schedule_lifecycle import (
    create_working_revision,
    get_lifecycle_overview,
)
from tests.lecturer_review_fixtures import DeterministicUtcClock, FIXED_UTC
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester


SOURCE_FINGERPRINT_KEY = "fs015-performance-source-key-" + ("p" * 40)
OPENING_TARGET_SECONDS = 3.0
OPENING_MAX_SECONDS = 10.0
SUBMISSION_TARGET_SECONDS = 2.0
SUBMISSION_MAX_SECONDS = 5.0
MEASURED_OPERATIONS = 20
WARM_UP_OPERATIONS = 3


def test_reference_scale_service_and_api_performance_guards(tmp_path, monkeypatch):
    """Repeatable backend guard, not browser or deployed-network acceptance."""

    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY",
        SOURCE_FINGERPRINT_KEY,
    )
    database = tmp_path / "lecturer-review-performance.db"
    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    with Session(engine) as db:
        secret = _seed_reference_scope(db)
        assert _session_count(db) == 100
        assert db.query(LecturerReviewFeedback).count() == 200

        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app, client=("198.51.100.40", 44000)) as client:
                authorization = {"Authorization": f"Bearer {secret}"}
                for _ in range(WARM_UP_OPERATIONS):
                    response = client.get(
                        "/api/public/lecturer-review",
                        headers=authorization,
                    )
                    assert response.status_code == 200

                opening_measurements = []
                for trial in range(MEASURED_OPERATIONS):
                    started = perf_counter()
                    response = client.get(
                        "/api/public/lecturer-review",
                        headers=authorization,
                    )
                    elapsed = perf_counter() - started
                    assert response.status_code == 200
                    payload = response.json()
                    assert sum(
                        len(course["sessions"]) for course in payload["courses"]
                    ) == 100
                    assert len(payload["submittedFeedback"]) == 200
                    opening_measurements.append(elapsed)
                    print(
                        f"OPEN-{trial + 1:02}: {elapsed:.6f}s "
                        "outcome=complete_usable_schedule"
                    )
        finally:
            app.dependency_overrides.clear()

        clock = DeterministicUtcClock(FIXED_UTC + timedelta(minutes=10))
        for index in range(WARM_UP_OPERATIONS):
            _timed_submission(
                db,
                secret,
                submission_number=10_000 + index,
                clock=clock,
            )

        submission_measurements = []
        created_ids = set()
        for trial in range(MEASURED_OPERATIONS):
            started = perf_counter()
            result = submit_lecturer_review_feedback(
                db,
                secret,
                FeedbackInput(
                    client_submission_id=UUID(int=20_000 + trial),
                    kind="revision_comment",
                    comment=f"Measured recommendation {trial + 1}.",
                ),
                clock=clock,
            )
            db.commit()
            elapsed = perf_counter() - started
            assert result.outcome == "created"
            assert result.item.id not in created_ids
            created_ids.add(result.item.id)
            submission_measurements.append(elapsed)
            print(
                f"SUBMIT-{trial + 1:02}: {elapsed:.6f}s "
                f"outcome={result.outcome}"
            )
            clock.advance(seconds=7)

        print(
            "PERF-ENV: "
            f"os={platform.platform()}; "
            f"python={sys.version.split()[0]}; "
            f"sqlalchemy={sqlalchemy.__version__}; "
            f"sqlite={sqlite3.sqlite_version}; "
            "runner=pytest+FastAPI-TestClient; "
            "database=file-backed-SQLite; "
            "network=none; browser=none"
        )

        assert len(opening_measurements) == MEASURED_OPERATIONS
        assert (
            sum(
                duration <= OPENING_TARGET_SECONDS
                for duration in opening_measurements
            )
            >= 19
        )
        assert all(
            duration <= OPENING_MAX_SECONDS
            for duration in opening_measurements
        )
        assert len(submission_measurements) == MEASURED_OPERATIONS
        assert (
            sum(
                duration <= SUBMISSION_TARGET_SECONDS
                for duration in submission_measurements
            )
            >= 19
        )
        assert all(
            duration <= SUBMISSION_MAX_SECONDS
            for duration in submission_measurements
        )
        assert len(created_ids) == MEASURED_OPERATIONS
        assert db.query(LecturerReviewFeedback).count() == (
            200 + WARM_UP_OPERATIONS + MEASURED_OPERATIONS
        )


def _seed_reference_scope(db: Session) -> str:
    seed_lifecycle_semester(db, with_schedule=True)
    draft = db.scalar(select(DraftSchedule))
    assert draft is not None
    reference_dates = [
        date(2026, 9, 1) + timedelta(days=index)
        for index in range(99)
        if date(2026, 9, 1) + timedelta(days=index) != date(2026, 10, 5)
    ]
    assert len(reference_dates) == 98
    for session_date in reference_dates:
        draft.sessions.append(
            DraftSession(
                course_id=1,
                lecturer_id=1,
                cohort_id=1,
                room_id=1,
                date=session_date,
                start_time=time(9),
                end_time=time(11),
                units=2,
                constraint_window_index=0,
            )
        )
    db.flush()

    revision = db.scalar(select(DraftSchedule.semester_id))
    assert revision == 1
    lifecycle = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, lifecycle["stateToken"])
    db.commit()
    issued = issue_lecturer_review_link(
        db,
        created["activeWorkingRevision"]["revisionId"],
        1,
        duration_days=3,
        clock=DeterministicUtcClock(),
    )
    db.commit()

    sessions = [
        ("teaching", item.id, item.date, "Lecture")
        for item in db.scalars(select(DraftSession).order_by(DraftSession.id))
    ]
    sessions.extend(
        (
            "exam",
            item.id,
            item.exam_date,
            item.exam_type,
        )
        for item in db.scalars(select(ExamSession).order_by(ExamSession.id))
    )
    course = db.get(Course, 1)
    cohort = db.get(Cohort, 1)
    assert course is not None and cohort is not None
    for index in range(200):
        kind, source_id, session_date, session_type = sessions[index % 100]
        context = {
            "sessionRef": f"{kind}:{source_id}",
            "sessionKind": kind,
            "sourceSessionId": source_id,
            "sessionType": session_type,
            "courseSourceId": course.id,
            "courseCode": "COURSE-1",
            "courseTitle": course.name,
            "date": session_date.isoformat(),
            "startTime": "09:00",
            "endTime": "11:00",
            "timeZone": "Europe/Vienna",
            "roomName": "Room 1",
            "cohortName": cohort.name,
        }
        impossible = index % 2 == 0
        db.add(
            LecturerReviewFeedback(
                review_link_id=issued.issued_link.id,
                kind=(
                    "impossible_session"
                    if impossible
                    else "session_comment"
                ),
                session_kind=kind,
                source_session_id=source_id,
                comment_text=(
                    None
                    if impossible
                    else f"Reference recommendation {index + 1}."
                ),
                session_context=context,
                client_submission_id=str(UUID(int=index + 1)),
                request_fingerprint=hashlib.sha256(
                    f"reference-feedback-{index + 1}".encode()
                ).hexdigest(),
                submitted_at=FIXED_UTC + timedelta(microseconds=index),
            )
        )
    db.commit()
    return issued.secret


def _session_count(db: Session) -> int:
    return (
        db.query(DraftSession).count()
        + db.query(ExamSession).count()
    )


def _timed_submission(
    db: Session,
    secret: str,
    *,
    submission_number: int,
    clock: DeterministicUtcClock,
) -> None:
    result = submit_lecturer_review_feedback(
        db,
        secret,
        FeedbackInput(
            client_submission_id=UUID(int=submission_number),
            kind="revision_comment",
            comment=f"Warm-up recommendation {submission_number}.",
        ),
        clock=clock,
    )
    db.commit()
    assert result.outcome == "created"
    clock.advance(seconds=7)
