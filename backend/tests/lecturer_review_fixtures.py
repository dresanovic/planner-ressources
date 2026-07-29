from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    DraftSession,
    ExamSession,
    Lecturer,
    Room,
    ScheduleRevision,
    ScheduleRevisionEvent,
    Semester,
    StudyType,
)


FIXED_UTC = datetime(2026, 7, 28, 8, 0, tzinfo=timezone.utc)


@dataclass
class DeterministicUtcClock:
    """Mutable callable clock for exact expiry and rolling-window boundaries."""

    current: datetime = FIXED_UTC

    def __post_init__(self) -> None:
        self.current = _as_utc(self.current)

    def __call__(self) -> datetime:
        return self.current

    def now(self) -> datetime:
        return self.current

    def set(self, value: datetime) -> datetime:
        self.current = _as_utc(value)
        return self.current

    def advance(
        self, delta: timedelta | None = None, **duration: float
    ) -> datetime:
        if delta is not None and duration:
            raise ValueError("Pass either a timedelta or duration fields, not both.")
        self.current += delta if delta is not None else timedelta(**duration)
        return self.current


@dataclass(frozen=True)
class LecturerReviewFixture:
    semester_id: int = 1
    published_revision_id: int = 1
    working_revision_id: int = 2
    primary_lecturer_id: int = 1
    second_lecturer_id: int = 2
    third_lecturer_id: int = 3
    primary_course_ids: tuple[int, ...] = (1, 2)
    all_course_ids: tuple[int, ...] = (1, 2, 3)
    primary_teaching_session_ids: tuple[int, ...] = (101, 102, 201)
    primary_exam_session_ids: tuple[int, ...] = (401,)


@dataclass(frozen=True)
class AssignmentChange:
    session_kind: Literal["teaching", "exam"]
    source_session_id: int
    previous_lecturer_id: int
    assigned_lecturer_id: int


def seed_lecturer_review_fixture(db: Session) -> LecturerReviewFixture:
    """Seed the complete minimum FS-015 lecturer/revision acceptance matrix.

    Courses may have multiple eligible lecturers, while every scheduled
    teaching or exam occurrence deliberately keeps the product's current
    single ``lecturer_id`` assignment.
    """

    fixture = LecturerReviewFixture()
    semester = Semester(
        id=fixture.semester_id,
        name="Autumn 2026",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 20),
    )
    lecturers = [
        Lecturer(
            id=1,
            name="Ada Lovelace",
            reference_code="LECT-ADA",
            normalized_reference_code="lect-ada",
        ),
        Lecturer(
            id=2,
            name="Grace Hopper",
            reference_code="LECT-GRACE",
            normalized_reference_code="lect-grace",
        ),
        Lecturer(
            id=3,
            name="Katherine Johnson",
            reference_code="LECT-KATHERINE",
            normalized_reference_code="lect-katherine",
        ),
    ]
    rooms = [
        Room(
            id=value,
            name=f"Room {value}01",
            reference_code=f"ROOM-{value}01",
            normalized_reference_code=f"room-{value}01",
            capacity=40 + value * 10,
        )
        for value in range(1, 4)
    ]
    cohorts = [
        Cohort(id=value, name=f"Cohort {value}", student_count=20 + value * 5)
        for value in range(1, 4)
    ]
    study_type = StudyType(id=1, name="Full-time")
    courses = [
        _course(
            course_id=1,
            name="Analytical Methods",
            eligible_lecturer_ids=(1, 2),
            room_id=1,
        ),
        _course(
            course_id=2,
            name="Algorithms",
            eligible_lecturer_ids=(1, 3),
            room_id=2,
        ),
        _course(
            course_id=3,
            name="Applied Physics",
            eligible_lecturer_ids=(2, 3),
            room_id=3,
        ),
    ]
    published = ScheduleRevision(
        id=fixture.published_revision_id,
        semester_id=fixture.semester_id,
        revision_number=1,
        state="published",
        row_version=2,
        snapshot_schema_version=1,
        snapshot_document=published_revision_snapshot(),
        created_at=FIXED_UTC - timedelta(days=7),
        state_changed_at=FIXED_UTC - timedelta(days=6),
        published_at=FIXED_UTC - timedelta(days=6),
        updated_at=FIXED_UTC - timedelta(days=6),
        events=[
            ScheduleRevisionEvent(
                semester_id=fixture.semester_id,
                event_sequence=1,
                event_type="created",
                from_state=None,
                to_state="draft",
                occurred_at=FIXED_UTC - timedelta(days=7),
            ),
            ScheduleRevisionEvent(
                semester_id=fixture.semester_id,
                event_sequence=2,
                event_type="published",
                from_state="draft",
                to_state="published",
                occurred_at=FIXED_UTC - timedelta(days=6),
            ),
        ],
    )
    working = ScheduleRevision(
        id=fixture.working_revision_id,
        semester_id=fixture.semester_id,
        revision_number=2,
        state="draft",
        origin_revision_id=fixture.published_revision_id,
        row_version=1,
        created_at=FIXED_UTC - timedelta(hours=1),
        state_changed_at=FIXED_UTC - timedelta(hours=1),
        updated_at=FIXED_UTC - timedelta(hours=1),
        events=[
            ScheduleRevisionEvent(
                semester_id=fixture.semester_id,
                event_sequence=3,
                event_type="created",
                from_state=None,
                to_state="draft",
                occurred_at=FIXED_UTC - timedelta(hours=1),
            )
        ],
    )

    db.add_all(
        [
            semester,
            *lecturers,
            *rooms,
            *cohorts,
            study_type,
            *courses,
            published,
            working,
            *_working_teaching_schedules(),
            *_working_exam_sessions(),
        ]
    )
    db.commit()
    return fixture


def reassign_session(
    db: Session,
    session_kind: Literal["teaching", "exam"],
    source_session_id: int,
    lecturer_id: int,
) -> AssignmentChange:
    model = DraftSession if session_kind == "teaching" else ExamSession
    session = db.get(model, source_session_id)
    if session is None:
        raise LookupError(f"{session_kind} session {source_session_id} does not exist.")
    if db.get(Lecturer, lecturer_id) is None:
        raise LookupError(f"Lecturer {lecturer_id} does not exist.")
    if not _lecturer_is_eligible(db, session.course_id, lecturer_id):
        raise ValueError(
            f"Lecturer {lecturer_id} is not eligible for course {session.course_id}."
        )
    change = AssignmentChange(
        session_kind=session_kind,
        source_session_id=source_session_id,
        previous_lecturer_id=session.lecturer_id,
        assigned_lecturer_id=lecturer_id,
    )
    session.lecturer_id = lecturer_id
    db.flush()
    return change


def remove_all_assignments(
    db: Session, lecturer_id: int
) -> tuple[AssignmentChange, ...]:
    """Reassign all live occurrences away from one lecturer.

    The seeded courses always provide at least one other eligible lecturer, so
    this helper models an empty public projection without deleting sessions.
    """

    changes: list[AssignmentChange] = []
    for session_kind, model in (("teaching", DraftSession), ("exam", ExamSession)):
        sessions = db.scalars(
            select(model)
            .where(model.lecturer_id == lecturer_id)
            .order_by(model.id)
        ).all()
        for session in sessions:
            replacement_id = db.scalar(
                select(CourseEligibleLecturer.lecturer_id)
                .where(
                    CourseEligibleLecturer.course_id == session.course_id,
                    CourseEligibleLecturer.lecturer_id != lecturer_id,
                )
                .order_by(CourseEligibleLecturer.lecturer_id)
                .limit(1)
            )
            if replacement_id is None:
                raise ValueError(
                    f"Course {session.course_id} has no replacement lecturer."
                )
            changes.append(
                reassign_session(
                    db,
                    session_kind,
                    session.id,
                    replacement_id,
                )
            )
    db.flush()
    return tuple(changes)


def restore_assignments(
    db: Session, changes: tuple[AssignmentChange, ...] | list[AssignmentChange]
) -> None:
    for change in changes:
        reassign_session(
            db,
            change.session_kind,
            change.source_session_id,
            change.previous_lecturer_id,
        )
    db.flush()


def published_revision_snapshot() -> dict:
    """Return revision-one content that differs from the live Working revision."""

    captured_at = _rfc3339(FIXED_UTC - timedelta(days=6))
    return {
        "schemaVersion": 1,
        "capturedAt": captured_at,
        "semester": {
            "sourceId": 1,
            "name": "Autumn 2026",
            "startDate": "2026-09-01",
            "endDate": "2026-12-20",
        },
        "courses": [
            _snapshot_course(
                course_id=1,
                title="Analytical Methods",
                cohort_id=1,
                lecturer_id=1,
                lecturer_name="Ada Lovelace",
                room_id=1,
                session_id=1001,
                session_date="2026-09-14",
            ),
            _snapshot_course(
                course_id=2,
                title="Algorithms",
                cohort_id=2,
                lecturer_id=3,
                lecturer_name="Katherine Johnson",
                room_id=2,
                session_id=2001,
                session_date="2026-09-15",
            ),
        ],
        "examSessions": [
            _snapshot_exam(
                exam_id=4001,
                course_id=1,
                course_title="Analytical Methods",
                cohort_id=1,
                lecturer_id=1,
                lecturer_name="Ada Lovelace",
                room_id=1,
            ),
            _snapshot_exam(
                exam_id=4002,
                course_id=2,
                course_title="Algorithms",
                cohort_id=2,
                lecturer_id=3,
                lecturer_name="Katherine Johnson",
                room_id=2,
            ),
        ],
        "capturedConditions": [],
    }


def _course(
    *,
    course_id: int,
    name: str,
    eligible_lecturer_ids: tuple[int, ...],
    room_id: int,
) -> Course:
    return Course(
        id=course_id,
        name=name,
        total_units=8,
        min_session_units=2,
        max_session_units=4,
        cohort_id=course_id,
        study_type_id=1,
        current_semester_id=1,
        eligible_lecturers=[
            CourseEligibleLecturer(lecturer_id=lecturer_id)
            for lecturer_id in eligible_lecturer_ids
        ],
        eligible_rooms=[CourseEligibleRoom(room_id=room_id)],
    )


def _working_teaching_schedules() -> list[DraftSchedule]:
    assignments = {
        1: [(101, 1, date(2026, 9, 21)), (102, 1, date(2026, 9, 28))],
        2: [(201, 1, date(2026, 9, 22)), (202, 3, date(2026, 9, 29))],
        3: [(301, 2, date(2026, 9, 23))],
    }
    names = {
        1: "Analytical Methods",
        2: "Algorithms",
        3: "Applied Physics",
    }
    schedules: list[DraftSchedule] = []
    for course_id, sessions in assignments.items():
        schedules.append(
            DraftSchedule(
                id=course_id,
                course_id=course_id,
                semester_id=1,
                revision=1,
                status="generated",
                course_name_snapshot=names[course_id],
                course_total_units_snapshot=8,
                course_min_session_units_snapshot=2,
                course_max_session_units_snapshot=4,
                cohort_id_snapshot=course_id,
                cohort_name_snapshot=f"Cohort {course_id}",
                cohort_size_snapshot=20 + course_id * 5,
                study_type_id_snapshot=1,
                study_type_name_snapshot="Full-time",
                semester_name_snapshot="Autumn 2026",
                semester_start_date_snapshot=date(2026, 9, 1),
                semester_end_date_snapshot=date(2026, 12, 20),
                sessions=[
                    DraftSession(
                        id=session_id,
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
                    for session_id, lecturer_id, session_date in sessions
                ],
            )
        )
    return schedules


def _working_exam_sessions() -> list[ExamSession]:
    return [
        _exam_session(
            exam_id=401,
            course_id=1,
            lecturer_id=1,
            lecturer_name="Ada Lovelace",
            exam_date=date(2026, 12, 7),
            final_teaching_session_id=102,
            final_teaching_date=date(2026, 9, 28),
        ),
        _exam_session(
            exam_id=402,
            course_id=2,
            lecturer_id=3,
            lecturer_name="Katherine Johnson",
            exam_date=date(2026, 12, 8),
            final_teaching_session_id=202,
            final_teaching_date=date(2026, 9, 29),
        ),
        _exam_session(
            exam_id=403,
            course_id=3,
            lecturer_id=2,
            lecturer_name="Grace Hopper",
            exam_date=date(2026, 12, 9),
            final_teaching_session_id=301,
            final_teaching_date=date(2026, 9, 23),
        ),
    ]


def _exam_session(
    *,
    exam_id: int,
    course_id: int,
    lecturer_id: int,
    lecturer_name: str,
    exam_date: date,
    final_teaching_session_id: int,
    final_teaching_date: date,
) -> ExamSession:
    course_names = {
        1: "Analytical Methods",
        2: "Algorithms",
        3: "Applied Physics",
    }
    lecturer_references = {
        1: "LECT-ADA",
        2: "LECT-GRACE",
        3: "LECT-KATHERINE",
    }
    return ExamSession(
        id=exam_id,
        course_id=course_id,
        semester_id=1,
        cohort_id=course_id,
        lecturer_id=lecturer_id,
        room_id=course_id,
        exam_date=exam_date,
        start_time=time(9),
        end_time=time(11),
        source="manual",
        revision=1,
        configuration_identifier=f"FINAL-{course_id}",
        configuration_revision=1,
        duration_minutes=120,
        exam_type="Written",
        required_capacity=20 + course_id * 5,
        recommended_start_date=exam_date - timedelta(days=2),
        recommended_end_date=exam_date + timedelta(days=2),
        recommendation_was_overridden=False,
        final_teaching_date=final_teaching_date,
        final_teaching_end_time=time(11),
        final_teaching_session_id_snapshot=final_teaching_session_id,
        course_name_snapshot=course_names[course_id],
        semester_name_snapshot="Autumn 2026",
        cohort_name_snapshot=f"Cohort {course_id}",
        lecturer_name_snapshot=lecturer_name,
        lecturer_reference_snapshot=lecturer_references[lecturer_id],
        room_name_snapshot=f"Room {course_id}01",
        room_reference_snapshot=f"ROOM-{course_id}01",
    )


def _snapshot_course(
    *,
    course_id: int,
    title: str,
    cohort_id: int,
    lecturer_id: int,
    lecturer_name: str,
    room_id: int,
    session_id: int,
    session_date: str,
) -> dict:
    return {
        "sourceCourseId": course_id,
        "name": title,
        "cohort": {
            "sourceId": cohort_id,
            "name": f"Cohort {cohort_id}",
            "size": 20 + cohort_id * 5,
        },
        "studyType": {"sourceId": 1, "name": "Full-time"},
        "totalUnits": 8,
        "scheduledUnits": 2,
        "remainingUnits": 6,
        "draftStatus": "generated",
        "teachingSessions": [
            {
                "sourceSessionId": session_id,
                "date": session_date,
                "startTime": "09:00:00",
                "endTime": "11:00:00",
                "units": 2,
                "timeWindowId": None,
                "constraintWindowIndex": 0,
                "lecturer": _snapshot_lecturer(lecturer_id, lecturer_name),
                "room": _snapshot_room(room_id),
                "validationAlerts": [],
            }
        ],
    }


def _snapshot_exam(
    *,
    exam_id: int,
    course_id: int,
    course_title: str,
    cohort_id: int,
    lecturer_id: int,
    lecturer_name: str,
    room_id: int,
) -> dict:
    return {
        "sourceExamId": exam_id,
        "course": {"sourceId": course_id, "name": course_title},
        "cohort": {"sourceId": cohort_id, "name": f"Cohort {cohort_id}"},
        "lecturer": _snapshot_lecturer(lecturer_id, lecturer_name),
        "room": _snapshot_room(room_id),
        "examDate": f"2026-12-{9 + course_id:02d}",
        "startTime": "09:00:00",
        "endTime": "11:00:00",
        "source": "manual",
        "configurationIdentifier": f"FINAL-{course_id}",
        "configurationRevision": 1,
        "durationMinutes": 120,
        "examType": "Written",
        "requiredCapacity": 20 + cohort_id * 5,
        "recommendedStartDate": f"2026-12-{7 + course_id:02d}",
        "recommendedEndDate": f"2026-12-{11 + course_id:02d}",
        "recommendationWasOverridden": False,
        "finalTeachingDate": "2026-09-30",
        "finalTeachingEndTime": "11:00:00",
        "finalTeachingSessionId": course_id * 1000 + 1,
        "validityIssues": [],
        "outsideRecommendedWindow": False,
    }


def _snapshot_lecturer(lecturer_id: int, name: str) -> dict:
    references = {
        1: "LECT-ADA",
        2: "LECT-GRACE",
        3: "LECT-KATHERINE",
    }
    return {
        "sourceId": lecturer_id,
        "name": name,
        "referenceCode": references[lecturer_id],
        "capacity": None,
    }


def _snapshot_room(room_id: int) -> dict:
    return {
        "sourceId": room_id,
        "name": f"Room {room_id}01",
        "referenceCode": f"ROOM-{room_id}01",
        "capacity": 40 + room_id * 10,
    }


def _lecturer_is_eligible(
    db: Session, course_id: int, lecturer_id: int
) -> bool:
    return (
        db.scalar(
            select(CourseEligibleLecturer.lecturer_id).where(
                CourseEligibleLecturer.course_id == course_id,
                CourseEligibleLecturer.lecturer_id == lecturer_id,
            )
        )
        is not None
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("DeterministicUtcClock requires an offset-aware datetime.")
    return value.astimezone(timezone.utc)


def _rfc3339(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")
