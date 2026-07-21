from datetime import date, datetime, time, timezone

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


FIXED_UTC = datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc)


def seed_lifecycle_semester(db, *, semester_id: int = 1, with_schedule: bool = True):
    lecturer = Lecturer(
        id=semester_id,
        name=f"Lecturer {semester_id}",
        reference_code=f"L-{semester_id}",
        normalized_reference_code=f"l-{semester_id}",
    )
    room = Room(
        id=semester_id,
        name=f"Room {semester_id}",
        reference_code=f"R-{semester_id}",
        normalized_reference_code=f"r-{semester_id}",
        capacity=40,
    )
    cohort = Cohort(id=semester_id, name=f"Cohort {semester_id}", student_count=30)
    semester = Semester(
        id=semester_id,
        name=f"Semester {semester_id}",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 20),
    )
    study_type = StudyType(id=semester_id, name=f"Study type {semester_id}")
    course = Course(
        id=semester_id,
        name=f"Course {semester_id}",
        total_units=4,
        min_session_units=2,
        max_session_units=2,
        cohort_id=cohort.id,
        study_type_id=study_type.id,
        current_semester_id=semester.id,
        eligible_lecturers=[CourseEligibleLecturer(lecturer_id=lecturer.id)],
        eligible_rooms=[CourseEligibleRoom(room_id=room.id)],
    )
    db.add_all([lecturer, room, cohort, semester, study_type, course])
    if with_schedule:
        db.add(teaching_schedule(semester_id=semester_id))
        db.add(exam_session(semester_id=semester_id))
    db.commit()
    return semester, course


def teaching_schedule(*, semester_id: int = 1) -> DraftSchedule:
    return DraftSchedule(
        course_id=semester_id,
        semester_id=semester_id,
        revision=1,
        status="generated",
        course_name_snapshot=f"Course {semester_id}",
        course_total_units_snapshot=4,
        course_min_session_units_snapshot=2,
        course_max_session_units_snapshot=2,
        cohort_id_snapshot=semester_id,
        cohort_name_snapshot=f"Cohort {semester_id}",
        cohort_size_snapshot=30,
        study_type_id_snapshot=semester_id,
        study_type_name_snapshot=f"Study type {semester_id}",
        semester_name_snapshot=f"Semester {semester_id}",
        semester_start_date_snapshot=date(2026, 9, 1),
        semester_end_date_snapshot=date(2026, 12, 20),
        sessions=[
            DraftSession(
                course_id=semester_id,
                lecturer_id=semester_id,
                cohort_id=semester_id,
                room_id=semester_id,
                date=date(2026, 10, 5),
                start_time=time(9),
                end_time=time(11),
                units=2,
                constraint_window_index=0,
            )
        ],
    )


def exam_session(*, semester_id: int = 1) -> ExamSession:
    return ExamSession(
        course_id=semester_id,
        semester_id=semester_id,
        cohort_id=semester_id,
        lecturer_id=semester_id,
        room_id=semester_id,
        exam_date=date(2026, 12, 10),
        start_time=time(9),
        end_time=time(11),
        source="manual",
        revision=1,
        configuration_identifier="FINAL",
        configuration_revision=1,
        duration_minutes=120,
        exam_type="Written",
        required_capacity=30,
        recommended_start_date=date(2026, 12, 7),
        recommended_end_date=date(2026, 12, 18),
        recommendation_was_overridden=False,
        final_teaching_date=date(2026, 10, 5),
        final_teaching_end_time=time(11),
        final_teaching_session_id_snapshot=1,
        course_name_snapshot=f"Course {semester_id}",
        semester_name_snapshot=f"Semester {semester_id}",
        cohort_name_snapshot=f"Cohort {semester_id}",
        lecturer_name_snapshot=f"Lecturer {semester_id}",
        lecturer_reference_snapshot=f"L-{semester_id}",
        room_name_snapshot=f"Room {semester_id}",
        room_reference_snapshot=f"R-{semester_id}",
    )


def working_revision(*, semester_id: int = 1, revision_number: int = 1):
    revision = ScheduleRevision(
        semester_id=semester_id,
        revision_number=revision_number,
        state="draft",
        row_version=1,
        created_at=FIXED_UTC,
        state_changed_at=FIXED_UTC,
        updated_at=FIXED_UTC,
    )
    revision.events.append(
        ScheduleRevisionEvent(
            semester_id=semester_id,
            event_sequence=1,
            event_type="created",
            from_state=None,
            to_state="draft",
            occurred_at=FIXED_UTC,
        )
    )
    return revision


def publication_condition(**overrides):
    value = {
        "code": "course_units_remaining",
        "message": "Course 1 has 2 teaching units remaining.",
        "courseId": 1,
        "sessionKind": "teaching",
        "sourceSessionId": None,
        "details": {"remainingUnits": 2},
    }
    value.update(overrides)
    return value


def canonical_snapshot(**overrides):
    value = {
        "schemaVersion": 1,
        "capturedAt": FIXED_UTC.isoformat().replace("+00:00", "Z"),
        "semester": {
            "sourceId": 1,
            "name": "Semester 1",
            "startDate": "2026-09-01",
            "endDate": "2026-12-20",
        },
        "courses": [],
        "examSessions": [],
        "capturedConditions": [publication_condition()],
    }
    value.update(overrides)
    return value
