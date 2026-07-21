from datetime import date, time

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    Lecturer,
    Room,
    ScheduleRevision,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)
from app.services.draft_schedule_repository import (
    load_course_plan,
    load_semester_plan,
    replace_draft_schedule,
    save_generation_constraints,
    update_draft_session,
)
from app.services.schedule_generation import GeneratedSession, PlanningPeriodPlan, TimeWindowPlan


def seed_multi_course_planner(db, *, course_count: int = 3, invalid_course_id: int | None = None):
    db.add_all([
        Semester(id=1, name="Fall 2026", start_date=date(2026, 9, 7), end_date=date(2026, 12, 20)),
        Semester(id=2, name="Spring 2027", start_date=date(2027, 2, 15), end_date=date(2027, 6, 20)),
        ScheduleRevision(id=1, semester_id=1, revision_number=1, row_version=1, state="draft"),
        ScheduleRevision(id=2, semester_id=2, revision_number=1, row_version=1, state="draft"),
        StudyType(id=1, name="Full-time"),
        StudyTypeTimeWindow(
            id=1, study_type_id=1, weekday=0, start_time=time(8), end_time=time(12), sort_order=1
        ),
        StudyTypeTimeWindow(
            id=2, study_type_id=1, weekday=2, start_time=time(8), end_time=time(12), sort_order=2
        ),
    ])
    for course_id in range(1, course_count + 1):
        db.add_all([
            Lecturer(id=course_id, name=f"Lecturer {course_id}"),
            Cohort(id=course_id, name=f"Cohort {course_id}", student_count=30),
            Room(id=course_id, name=f"Room {course_id}", capacity=20 if course_id == invalid_course_id else 40),
            Course(
                id=course_id,
                name=f"Course {course_id}",
                total_units=8,
                min_session_units=2,
                max_session_units=4,
                cohort_id=course_id,
                study_type_id=1,
                current_semester_id=1,
                eligible_lecturers=[CourseEligibleLecturer(lecturer_id=course_id)],
                eligible_rooms=[CourseEligibleRoom(room_id=course_id)],
            ),
        ])
    db.commit()


def seed_saved_constraints(db, course_id: int, semester_id: int, *, weekday: int = 4):
    constraints = save_generation_constraints(
        db,
        load_course_plan(db, course_id),
        load_semester_plan(db, semester_id),
        PlanningPeriodPlan(
            date(2026, 9, 7) if semester_id == 1 else date(2027, 2, 15),
            date(2026, 12, 20) if semester_id == 1 else date(2027, 6, 20),
        ),
        [TimeWindowPlan(id=None, weekday=weekday, start_time=time(8), end_time=time(12))],
    )
    db.commit()
    return constraints


def seed_existing_draft(db, course_id: int, semester_id: int, *, manually_edit: bool = False):
    session_date = date(2026, 9, 7) if semester_id == 1 else date(2027, 2, 15)
    draft = replace_draft_schedule(
        db,
        load_course_plan(db, course_id),
        semester_id,
        [GeneratedSession(
            date=session_date,
            start_time=time(8),
            end_time=time(11, 30),
            units=4,
            time_window_id=1,
            constraint_window_index=0,
        )],
    )
    db.commit()
    if manually_edit:
        edited_date = date(2026, 12, 14) if semester_id == 1 else date(2027, 6, 14)
        draft = update_draft_session(
            db,
            draft.sessions[0].id,
            date=edited_date,
            start_time=time(9),
            end_time=time(10, 30),
            room_id=course_id,
        )
        db.commit()
    return draft
