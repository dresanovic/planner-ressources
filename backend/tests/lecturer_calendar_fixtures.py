from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta

from sqlalchemy.orm import Session

from app.models.planning import DraftSchedule, DraftSession, ExamSession
from tests.lecturer_review_fixtures import (
    FIXED_UTC,
    DeterministicUtcClock,
    LecturerReviewFixture,
    _exam_session,
    remove_all_assignments,
    reassign_session,
    restore_assignments,
    seed_lecturer_review_fixture,
)


CALENDAR_SOURCE_FINGERPRINT_KEY = (
    "fs020-calendar-source-fingerprint-key-" + ("c" * 32)
)


@dataclass(frozen=True)
class LecturerCalendarFixture:
    review: LecturerReviewFixture
    clock: DeterministicUtcClock
    source_fingerprint_key: str
    teaching_session_ids: tuple[int, ...]
    exam_session_ids: tuple[int, ...]

    @property
    def total_session_count(self) -> int:
        return len(self.teaching_session_ids) + len(self.exam_session_ids)


def seed_lecturer_calendar_fixture(db: Session) -> LecturerCalendarFixture:
    """Seed the reusable FS-020 acceptance matrix.

    The matrix spans three lecturers, two revisions, three courses, 20 mixed
    teaching/exam sessions, reassignment helpers, and deterministic clock/key
    inputs. ``remove_all_assignments`` supplies the explicit empty projection.
    """

    review = seed_lecturer_review_fixture(db)
    extra_teaching: list[DraftSession] = []
    teaching_assignments = (
        (110, 1, 1, date(2026, 10, 5)),
        (111, 1, 2, date(2026, 10, 12)),
        (112, 1, 1, date(2026, 10, 19)),
        (210, 2, 1, date(2026, 10, 6)),
        (211, 2, 3, date(2026, 10, 13)),
        (212, 2, 1, date(2026, 10, 20)),
        (310, 3, 2, date(2026, 10, 7)),
        (311, 3, 3, date(2026, 10, 14)),
        (312, 3, 2, date(2026, 10, 21)),
    )
    for session_id, course_id, lecturer_id, session_date in teaching_assignments:
        schedule = db.get(DraftSchedule, course_id)
        if schedule is None:
            raise AssertionError(f"Missing seeded schedule for course {course_id}.")
        extra_teaching.append(
            DraftSession(
                id=session_id,
                draft_schedule_id=schedule.id,
                course_id=course_id,
                lecturer_id=lecturer_id,
                cohort_id=course_id,
                room_id=course_id,
                date=session_date,
                start_time=time(9),
                end_time=time(11),
                units=2,
                constraint_window_index=0,
            )
        )

    extra_exams: list[ExamSession] = []
    for exam_id, course_id, lecturer_id, lecturer_name, exam_date, final_id in (
        (410, 1, 1, "Ada Lovelace", date(2026, 12, 14), 112),
        (411, 2, 3, "Katherine Johnson", date(2026, 12, 15), 212),
        (412, 3, 2, "Grace Hopper", date(2026, 12, 16), 312),
    ):
        extra_exams.append(
            _exam_session(
                exam_id=exam_id,
                course_id=course_id,
                lecturer_id=lecturer_id,
                lecturer_name=lecturer_name,
                exam_date=exam_date,
                final_teaching_session_id=final_id,
                final_teaching_date=exam_date - timedelta(days=55),
            )
        )

    db.add_all([*extra_teaching, *extra_exams])
    db.commit()
    teaching_ids = (101, 102, 201, 202, 301, *(item[0] for item in teaching_assignments))
    exam_ids = (401, 402, 403, *(item.id for item in extra_exams))
    fixture = LecturerCalendarFixture(
        review=review,
        clock=DeterministicUtcClock(FIXED_UTC),
        source_fingerprint_key=CALENDAR_SOURCE_FINGERPRINT_KEY,
        teaching_session_ids=teaching_ids,
        exam_session_ids=exam_ids,
    )
    if fixture.total_session_count < 20:
        raise AssertionError("FS-020 fixture must contain at least 20 sessions.")
    return fixture


__all__ = [
    "CALENDAR_SOURCE_FINGERPRINT_KEY",
    "LecturerCalendarFixture",
    "remove_all_assignments",
    "reassign_session",
    "restore_assignments",
    "seed_lecturer_calendar_fixture",
]
