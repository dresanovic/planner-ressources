from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.planning import (
    Cohort,
    Course,
    Lecturer,
    Room,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)
from app.services.draft_schedule_repository import (
    clear_generation_constraints,
    get_draft_schedule,
    load_generation_constraints,
    load_course_plan,
    load_semester_plan,
    replace_draft_schedule,
    save_generation_constraints,
)
from app.services.schedule_generation import GeneratedSession, PlanningPeriodPlan, TimeWindowPlan


def make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def seed_course(db):
    lecturer = Lecturer(id=1, name="Ada Lovelace")
    cohort = Cohort(id=1, name="AI 1", student_count=30)
    room = Room(id=1, name="R1", capacity=40)
    study_type = StudyType(id=1, name="Full-time")
    semester = Semester(id=1, name="Fall", start_date=date(2026, 9, 7), end_date=date(2026, 12, 20))
    window = StudyTypeTimeWindow(
        id=1,
        study_type_id=1,
        weekday=0,
        start_time=time(8, 0),
        end_time=time(12, 0),
        sort_order=1,
    )
    course = Course(
        id=1,
        name="Planning 101",
        total_units=20,
        min_session_units=2,
        max_session_units=4,
        lecturer_id=1,
        cohort_id=1,
        room_id=1,
        study_type_id=1,
    )
    db.add_all([lecturer, cohort, room, study_type, semester, window, course])
    db.commit()


def test_successful_regeneration_replaces_prior_draft_sessions():
    db = make_session()
    seed_course(db)
    course_plan = load_course_plan(db, 1)

    replace_draft_schedule(
        db,
        course_plan=course_plan,
        semester_id=1,
        generated_sessions=[
            GeneratedSession(
                date=date(2026, 9, 7),
                start_time=time(8, 0),
                end_time=time(11, 30),
                units=4,
                time_window_id=1,
                constraint_window_index=0,
            )
        ],
    )
    replace_draft_schedule(
        db,
        course_plan=course_plan,
        semester_id=1,
        generated_sessions=[
            GeneratedSession(
                date=date(2026, 9, 14),
                start_time=time(8, 0),
                end_time=time(11, 30),
                units=4,
                time_window_id=1,
                constraint_window_index=0,
            ),
            GeneratedSession(
                date=date(2026, 9, 21),
                start_time=time(8, 0),
                end_time=time(11, 30),
                units=4,
                time_window_id=1,
                constraint_window_index=0,
            ),
        ],
    )

    draft = get_draft_schedule(db, 1)
    assert draft is not None
    assert [session.date for session in draft.sessions] == [date(2026, 9, 14), date(2026, 9, 21)]


def test_generation_constraints_default_save_replace_and_clear():
    db = make_session()
    seed_course(db)
    course_plan = load_course_plan(db, 1)
    semester_plan = load_semester_plan(db, 1)

    defaults = load_generation_constraints(db, course_plan, semester_plan)

    assert defaults.is_custom is False
    assert defaults.planning_period.start_date == date(2026, 9, 7)
    assert [window.weekday for window in defaults.allowed_windows] == [0]

    saved = save_generation_constraints(
        db,
        course_plan=course_plan,
        semester_plan=semester_plan,
        planning_period=PlanningPeriodPlan(date(2026, 9, 14), date(2026, 10, 5)),
        allowed_windows=[
            TimeWindowPlan(
                id=None,
                weekday=2,
                start_time=time(9, 0),
                end_time=time(13, 0),
                constraint_window_index=0,
            )
        ],
    )

    assert saved.is_custom is True
    assert saved.planning_period.start_date == date(2026, 9, 14)
    assert saved.allowed_windows[0].id is None
    assert saved.allowed_windows[0].weekday == 2

    clear_generation_constraints(db, course_id=1, semester_id=1)
    cleared = load_generation_constraints(db, course_plan, semester_plan)

    assert cleared.is_custom is False
    assert cleared.planning_period.start_date == date(2026, 9, 7)
    assert [window.weekday for window in cleared.allowed_windows] == [0]
