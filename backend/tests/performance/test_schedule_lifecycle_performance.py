from datetime import date, time, timedelta
from time import perf_counter

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
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
)
from app.services.schedule_lifecycle import create_working_revision, get_lifecycle_overview, get_revision_content, prepare_publication, transition_revision
from tests.schedule_lifecycle_fixtures import FIXED_UTC, seed_lifecycle_semester


LIMIT_SECONDS = 2.0


def _seed_reference_schedule(db: Session) -> None:
    semester, first_course = seed_lifecycle_semester(db, with_schedule=False)
    first_course.total_units = 10
    first_course.min_session_units = 2
    first_course.max_session_units = 2
    for course_id in range(2, 101):
        lecturer = Lecturer(id=course_id, name=f"Lecturer {course_id}", reference_code=f"L-{course_id}", normalized_reference_code=f"l-{course_id}")
        room = Room(id=course_id, name=f"Room {course_id}", reference_code=f"R-{course_id}", normalized_reference_code=f"r-{course_id}", capacity=40)
        cohort = Cohort(id=course_id, name=f"Cohort {course_id}", student_count=30)
        course = Course(
            id=course_id,
            name=f"Course {course_id}",
            total_units=10,
            min_session_units=2,
            max_session_units=2,
            cohort_id=course_id,
            study_type_id=first_course.study_type_id,
            current_semester_id=semester.id,
            eligible_lecturers=[CourseEligibleLecturer(lecturer_id=course_id)],
            eligible_rooms=[CourseEligibleRoom(room_id=course_id)],
        )
        db.add_all([lecturer, room, cohort, course])
    db.flush()
    for course_id in range(1, 101):
        sessions = [
            DraftSession(
                course_id=course_id,
                lecturer_id=course_id,
                cohort_id=course_id,
                room_id=course_id,
                date=date(2026, 10, 5) + timedelta(days=index),
                start_time=time(9),
                end_time=time(11),
                units=2,
                constraint_window_index=0,
            )
            for index in range(5)
        ]
        draft = DraftSchedule(
            course_id=course_id,
            semester_id=semester.id,
            revision=1,
            status="generated",
            course_name_snapshot=f"Course {course_id}",
            course_total_units_snapshot=10,
            course_min_session_units_snapshot=2,
            course_max_session_units_snapshot=2,
            cohort_id_snapshot=course_id,
            cohort_name_snapshot=f"Cohort {course_id}",
            cohort_size_snapshot=30,
            study_type_id_snapshot=first_course.study_type_id,
            study_type_name_snapshot=first_course.study_type.name,
            semester_name_snapshot=semester.name,
            semester_start_date_snapshot=semester.start_date,
            semester_end_date_snapshot=semester.end_date,
            sessions=sessions,
        )
        db.add(draft)
        db.flush()
        db.add(ExamSession(
            course_id=course_id,
            semester_id=semester.id,
            cohort_id=course_id,
            lecturer_id=course_id,
            room_id=course_id,
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
            final_teaching_date=sessions[-1].date,
            final_teaching_end_time=sessions[-1].end_time,
            final_teaching_session_id_snapshot=sessions[-1].id,
            course_name_snapshot=f"Course {course_id}",
            semester_name_snapshot=semester.name,
            cohort_name_snapshot=f"Cohort {course_id}",
            lecturer_name_snapshot=f"Lecturer {course_id}",
            lecturer_reference_snapshot=f"L-{course_id}",
            room_name_snapshot=f"Room {course_id}",
            room_reference_snapshot=f"R-{course_id}",
        ))
    db.commit()


def test_lifecycle_reference_operations_remain_bounded(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'lifecycle-performance.db'}")
    initialize_database(engine)
    with Session(engine) as db:
        _seed_reference_schedule(db)
        initial = get_lifecycle_overview(db, 1)
        working = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        revision = working["activeWorkingRevision"]

        statements = 0

        def count_statement(*_args):
            nonlocal statements
            statements += 1

        event.listen(engine, "before_cursor_execute", count_statement)
        started = perf_counter()
        prepared = prepare_publication(db, revision["revisionId"], revision["revisionVersion"], working["stateToken"])
        event.remove(engine, "before_cursor_execute", count_statement)
        assert prepared["courseCount"] == 100
        assert statements < 50
        assert perf_counter() - started < LIMIT_SECONDS
        started = perf_counter()
        published = transition_revision(db, revision["revisionId"], action="publish", expected_revision_version=revision["revisionVersion"], expected_state_token=working["stateToken"], confirmed=True, publication_token=prepared["preparationToken"])
        db.commit()
        assert perf_counter() - started < LIMIT_SECONDS
        started = perf_counter()
        successor = create_working_revision(db, 1, published["stateToken"])
        db.commit()
        assert perf_counter() - started < LIMIT_SECONDS
        started = perf_counter()
        content = get_revision_content(db, published["currentPublication"]["revisionId"])
        assert content["contentSource"] == "captured_snapshot"
        assert len(content["snapshot"]["courses"]) == 100
        assert sum(len(course["teachingSessions"]) for course in content["snapshot"]["courses"]) == 500
        assert len(content["snapshot"]["examSessions"]) == 100
        assert perf_counter() - started < LIMIT_SECONDS

        active = db.get(ScheduleRevision, successor["activeWorkingRevision"]["revisionId"])
        active.state = "abandoned"
        active.snapshot_schema_version = 1
        active.snapshot_document = {"schemaVersion": 1}
        for number in range(3, 102):
            row = ScheduleRevision(semester_id=1, revision_number=number, state="abandoned", row_version=1, snapshot_schema_version=1, snapshot_document={"schemaVersion": 1}, created_at=FIXED_UTC, state_changed_at=FIXED_UTC, updated_at=FIXED_UTC)
            row.events.append(ScheduleRevisionEvent(semester_id=1, event_sequence=number + 1, event_type="abandoned", from_state="draft", to_state="abandoned", occurred_at=FIXED_UTC))
            db.add(row)
        db.commit()
        started = perf_counter()
        history = get_lifecycle_overview(db, 1)
        assert len(history["revisions"]) == 101
        assert perf_counter() - started < LIMIT_SECONDS
