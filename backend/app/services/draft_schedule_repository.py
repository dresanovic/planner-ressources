from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Cohort,
    Course,
    DraftSchedule,
    DraftSession,
    Room,
    Semester,
    StudyTypeTimeWindow,
)
from app.services.schedule_generation import (
    CoursePlan,
    GeneratedSession,
    SemesterPlan,
    TimeWindowPlan,
)


class PlanningInputNotFoundError(ValueError):
    pass


def load_course_plan(db: Session, course_id: int) -> CoursePlan:
    course = db.get(Course, course_id)
    if course is None:
        raise PlanningInputNotFoundError("Course not found.")
    cohort = db.get(Cohort, course.cohort_id)
    room = db.get(Room, course.room_id)
    if cohort is None or room is None:
        raise PlanningInputNotFoundError("Course planning input is incomplete.")
    return CoursePlan(
        id=course.id,
        total_units=course.total_units,
        min_session_units=course.min_session_units,
        max_session_units=course.max_session_units,
        lecturer_id=course.lecturer_id,
        cohort_id=course.cohort_id,
        room_id=course.room_id,
        study_type_id=course.study_type_id,
        cohort_size=cohort.student_count,
        room_capacity=room.capacity,
    )


def load_semester_plan(db: Session, semester_id: int) -> SemesterPlan:
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise PlanningInputNotFoundError("Semester not found.")
    return SemesterPlan(id=semester.id, start_date=semester.start_date, end_date=semester.end_date)


def load_time_windows(db: Session, study_type_id: int) -> list[TimeWindowPlan]:
    rows = (
        db.execute(
            select(StudyTypeTimeWindow)
            .where(StudyTypeTimeWindow.study_type_id == study_type_id)
            .order_by(StudyTypeTimeWindow.sort_order, StudyTypeTimeWindow.weekday)
        )
        .scalars()
        .all()
    )
    return [
        TimeWindowPlan(
            id=row.id,
            weekday=row.weekday,
            start_time=row.start_time,
            end_time=row.end_time,
            sort_order=row.sort_order,
        )
        for row in rows
    ]


def replace_draft_schedule(
    db: Session,
    course_plan: CoursePlan,
    semester_id: int,
    selected_time_window_id: int,
    generated_sessions: list[GeneratedSession],
) -> DraftSchedule:
    existing = get_draft_schedule(db, course_plan.id)
    if existing is not None:
        db.delete(existing)
        db.flush()

    draft = DraftSchedule(
        course_id=course_plan.id,
        semester_id=semester_id,
        selected_time_window_id=selected_time_window_id,
        status="generated",
    )
    draft.sessions = [
        DraftSession(
            course_id=course_plan.id,
            lecturer_id=course_plan.lecturer_id,
            cohort_id=course_plan.cohort_id,
            room_id=course_plan.room_id,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
            units=session.units,
            time_window_id=session.time_window_id,
        )
        for session in generated_sessions
    ]
    db.add(draft)
    db.commit()
    return get_draft_schedule(db, course_plan.id) or draft


def get_draft_schedule(db: Session, course_id: int) -> DraftSchedule | None:
    return (
        db.execute(
            select(DraftSchedule)
            .where(DraftSchedule.course_id == course_id)
            .options(
                selectinload(DraftSchedule.sessions),
                selectinload(DraftSchedule.course).selectinload(Course.lecturer),
                selectinload(DraftSchedule.course).selectinload(Course.cohort),
                selectinload(DraftSchedule.course).selectinload(Course.room),
                selectinload(DraftSchedule.course).selectinload(Course.study_type),
            )
        )
        .scalars()
        .one_or_none()
    )
