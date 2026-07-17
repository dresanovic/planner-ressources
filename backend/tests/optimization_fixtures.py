from datetime import date, time

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    Lecturer,
    Room,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)
from app.services.schedule_generation import PlanningPeriodPlan, ResourceCandidatePlan, TimeWindowPlan
from app.services.semester_optimization import FixedSession, OptimizationCourse


SEMESTER_START = date(2026, 9, 7)
SEMESTER_END = date(2026, 12, 20)


def resource(resource_id: int, code: str, *, capacity: int | None = None):
    return ResourceCandidatePlan(resource_id, code, capacity=capacity)


def window(window_id: int = 1, weekday: int = 0, start: time = time(8), end: time = time(12)):
    return TimeWindowPlan(window_id, weekday, start, end)


def optimization_course(
    course_id: int,
    *,
    total_units: int = 8,
    min_units: int = 2,
    max_units: int = 4,
    cohort_id: int | None = None,
    lecturer_ids: tuple[int, ...] | None = None,
    room_ids: tuple[int, ...] | None = None,
    windows: tuple[TimeWindowPlan, ...] | None = None,
):
    lecturers = lecturer_ids or (course_id,)
    rooms = room_ids or (course_id,)
    return OptimizationCourse(
        course_id=course_id,
        course_name=f"Course {course_id}",
        total_units=total_units,
        min_session_units=min_units,
        max_session_units=max_units,
        cohort_id=cohort_id or course_id,
        cohort_size=30,
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_END),
        windows=windows or (window(),),
        lecturers=tuple(resource(item, f"LEC-{item:03}") for item in lecturers),
        rooms=tuple(resource(item, f"ROOM-{item:03}", capacity=40) for item in rooms),
    )


def fixed_session(
    course_id: int = 99,
    *,
    cohort_id: int = 99,
    lecturer_id: int = 99,
    room_id: int = 99,
    session_date: date = SEMESTER_START,
    start: time = time(8),
    end: time = time(12),
):
    return FixedSession(course_id, cohort_id, lecturer_id, room_id, session_date, start, end)


def seed_optimization_planner(db, *, course_count: int = 3, total_units: int = 8):
    db.add_all([
        Semester(id=1, name="Fall 2026", start_date=SEMESTER_START, end_date=SEMESTER_END),
        Semester(id=2, name="Spring 2027", start_date=date(2027, 2, 15), end_date=date(2027, 6, 20)),
        StudyType(id=1, name="Full-time"),
        StudyTypeTimeWindow(id=1, study_type_id=1, weekday=0, start_time=time(8), end_time=time(12), sort_order=1),
        StudyTypeTimeWindow(id=2, study_type_id=1, weekday=2, start_time=time(8), end_time=time(12), sort_order=2),
    ])
    for course_id in range(1, course_count + 1):
        db.add_all([
            Lecturer(id=course_id, name=f"Lecturer {course_id}", reference_code=f"LEC-{course_id:03}"),
            Cohort(id=course_id, name=f"Cohort {course_id}", student_count=30),
            Room(id=course_id, name=f"Room {course_id}", reference_code=f"ROOM-{course_id:03}", capacity=40),
            Course(
                id=course_id,
                name=f"Course {course_id}",
                total_units=total_units,
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


def reference_performance_courses():
    windows = (
        window(1, 0, time(8), time(12)),
        window(2, 2, time(8), time(12)),
        window(3, 4, time(8), time(12)),
    )
    return [optimization_course(index, total_units=30, windows=windows) for index in range(1, 21)]


def reference_fixed_sessions():
    return [
        fixed_session(
            course_id=1000 + index,
            cohort_id=1000 + index,
            lecturer_id=1000 + index,
            room_id=1000 + index,
            session_date=SEMESTER_START,
        )
        for index in range(500)
    ]
