from datetime import date, time
from time import perf_counter

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, selectinload

from app.db.schema import initialize_database
from app.api.planning_options import read_planning_options
from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    Lecturer,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
    Room,
    Semester,
    StudyType,
)


def test_reference_acceptance_dataset_is_queryable_within_two_seconds():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    with Session(engine) as db:
        semester = Semester(name="Fall", normalized_name="fall", normalized_name_key="fall", start_date=date(2026, 9, 1), end_date=date(2026, 12, 20))
        cohort = Cohort(name="Cohort", normalized_name="cohort", normalized_name_key="cohort", student_count=20)
        study_type = StudyType(name="Full-time", normalized_name="full-time", normalized_name_key="full-time")
        db.add_all([semester, cohort, study_type])
        lecturers = [Lecturer(name=f"Lecturer {i}", reference_code=f"L-{i}", normalized_reference_code=f"l-{i}") for i in range(100)]
        rooms = [Room(name=f"Room {i}", reference_code=f"R-{i}", normalized_reference_code=f"r-{i}", capacity=30) for i in range(100)]
        db.add_all(lecturers + rooms)
        db.flush()
        courses = [Course(name=f"Course {i}", normalized_name=f"course {i}", normalized_name_key=f"course {i}", total_units=4, min_session_units=2, max_session_units=4, cohort_id=cohort.id, study_type_id=study_type.id, current_semester_id=semester.id) for i in range(100)]
        db.add_all(courses)
        db.flush()
        for i, course in enumerate(courses):
            db.add(CourseEligibleLecturer(course_id=course.id, lecturer_id=lecturers[i].id))
            db.add(CourseEligibleRoom(course_id=course.id, room_id=rooms[i].id))
        for i in range(1000):
            period = ResourceUnavailabilityPeriod(lecturer_id=lecturers[i % 100].id, kind="recurring", start_time=time(8), end_time=time(10))
            period.weekdays.append(ResourceUnavailabilityWeekday(weekday=i % 7))
            db.add(period)
        db.commit()

        started = perf_counter()
        loaded_lecturers = db.execute(select(Lecturer).order_by(Lecturer.id)).scalars().all()
        loaded_rooms = db.execute(select(Room).order_by(Room.id)).scalars().all()
        loaded_courses = db.execute(
            select(Course).options(selectinload(Course.eligible_lecturers), selectinload(Course.eligible_rooms))
        ).scalars().all()
        loaded_periods = db.execute(
            select(ResourceUnavailabilityPeriod).options(selectinload(ResourceUnavailabilityPeriod.weekdays))
        ).scalars().all()
        elapsed = perf_counter() - started

        statement_count = 0

        def count_statement(*_args):
            nonlocal statement_count
            statement_count += 1

        event.listen(engine, "before_cursor_execute", count_statement)
        started = perf_counter()
        planning_options = read_planning_options(semester_id=semester.id, db=db)
        planning_elapsed = perf_counter() - started
        event.remove(engine, "before_cursor_execute", count_statement)

    assert (len(loaded_lecturers), len(loaded_rooms), len(loaded_courses), len(loaded_periods)) == (100, 100, 100, 1000)
    assert elapsed < 2.0
    assert len(planning_options.courses) == 100
    assert planning_elapsed < 2.0
    assert statement_count <= 20
