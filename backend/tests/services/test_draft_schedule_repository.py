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
    DraftSessionEditValidationError,
    clear_generation_constraints,
    get_draft_schedule,
    load_generation_constraints,
    load_course_plan,
    load_semester_plan,
    replace_draft_schedule,
    save_generation_constraints,
    update_draft_session,
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
    room_2 = Room(id=2, name="R2", capacity=50)
    small_room = Room(id=3, name="Tiny", capacity=20)
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
    db.add_all([lecturer, cohort, room, room_2, small_room, study_type, semester, window, course])
    db.commit()


def seed_draft(db):
    course_plan = load_course_plan(db, 1)
    return replace_draft_schedule(
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
            ),
            GeneratedSession(
                date=date(2026, 9, 14),
                start_time=time(8, 0),
                end_time=time(11, 30),
                units=4,
                time_window_id=1,
                constraint_window_index=0,
            ),
        ],
    )


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

    draft = get_draft_schedule(db, 1, 1)
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


def test_update_draft_session_persists_date_time_and_room():
    db = make_session()
    seed_course(db)
    draft = seed_draft(db)

    updated = update_draft_session(
        db,
        draft.sessions[0].id,
        date=date(2026, 9, 21),
        start_time=time(9, 0),
        end_time=time(12, 0),
        room_id=2,
    )

    session = updated.sessions[-1]
    assert session.date == date(2026, 9, 21)
    assert session.start_time == time(9, 0)
    assert session.end_time == time(12, 0)
    assert session.room_id == 2


def test_update_draft_session_rejects_invalid_date_time_and_duplicate_date_without_changes():
    db = make_session()
    seed_course(db)
    draft = seed_draft(db)
    original = draft.sessions[0]

    invalid_cases = [
        {
            "date": date(2026, 9, 1),
            "start_time": time(9, 0),
            "end_time": time(10, 0),
            "room_id": 1,
            "code": "INVALID_SESSION_DATE",
        },
        {
            "date": date(2026, 9, 21),
            "start_time": time(10, 0),
            "end_time": time(10, 0),
            "room_id": 1,
            "code": "INVALID_SESSION_TIME_RANGE",
        },
        {
            "date": date(2026, 9, 14),
            "start_time": time(9, 0),
            "end_time": time(10, 0),
            "room_id": 1,
            "code": "DUPLICATE_SESSION_DATE",
        },
    ]

    for invalid in invalid_cases:
        try:
            update_draft_session(db, original.id, **{key: value for key, value in invalid.items() if key != "code"})
        except DraftSessionEditValidationError as exc:
            assert exc.code == invalid["code"]
        else:
            raise AssertionError("Expected validation error")

    unchanged = db.get(type(original), original.id)
    assert unchanged is not None
    assert unchanged.date == date(2026, 9, 7)
    assert unchanged.start_time == time(8, 0)
    assert unchanged.end_time == time(11, 30)
    assert unchanged.room_id == 1


def test_update_draft_session_enforces_room_capacity_but_not_occupancy():
    db = make_session()
    seed_course(db)
    draft = seed_draft(db)
    target_session_id = draft.sessions[0].id

    try:
        update_draft_session(
            db,
            target_session_id,
            date=date(2026, 9, 21),
            start_time=time(9, 0),
            end_time=time(10, 0),
            room_id=3,
        )
    except DraftSessionEditValidationError as exc:
        assert exc.code == "INSUFFICIENT_ROOM_CAPACITY"
    else:
        raise AssertionError("Expected capacity validation error")

    updated = update_draft_session(
        db,
        target_session_id,
        date=date(2026, 9, 21),
        start_time=time(8, 0),
        end_time=time(9, 0),
        room_id=2,
    )

    edited = next(session for session in updated.sessions if session.id == target_session_id)
    assert edited.room_id == 2


def test_course_semester_identity_revisions_and_cross_semester_retention():
    db = make_session()
    seed_course(db)
    db.add(Semester(id=2, name="Spring", start_date=date(2027, 2, 1), end_date=date(2027, 6, 20)))
    db.commit()
    plan = load_course_plan(db, 1)
    sessions = [GeneratedSession(date(2026, 9, 7), start_time=time(8), end_time=time(11, 30), units=4, time_window_id=1, constraint_window_index=0)]
    fall = replace_draft_schedule(db, plan, 1, sessions)
    db.commit()
    spring_sessions = [GeneratedSession(date(2027, 2, 1), start_time=time(8), end_time=time(11, 30), units=4, time_window_id=1, constraint_window_index=0)]
    spring = replace_draft_schedule(db, plan, 2, spring_sessions)
    db.commit()

    assert fall.id != spring.id
    assert get_draft_schedule(db, 1, 1).revision == 1
    assert get_draft_schedule(db, 1, 2).revision == 1

    regenerated = replace_draft_schedule(db, plan, 1, sessions)
    assert regenerated.id == fall.id
    assert regenerated.revision == 2
    assert get_draft_schedule(db, 1, 2).id == spring.id


def test_constraint_revision_changes_only_when_saved_values_change():
    db = make_session()
    seed_course(db)
    plan = load_course_plan(db, 1)
    semester = load_semester_plan(db, 1)
    period = PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20))
    windows = [TimeWindowPlan(id=1, weekday=0, start_time=time(8), end_time=time(12), sort_order=0)]

    first = save_generation_constraints(db, plan, semester, period, windows)
    unchanged = save_generation_constraints(db, plan, semester, period, windows)
    changed = save_generation_constraints(
        db, plan, semester, period,
        [TimeWindowPlan(id=None, weekday=2, start_time=time(9), end_time=time(13), sort_order=0)],
    )

    assert first.revision == 1
    assert unchanged.constraint_set_id == first.constraint_set_id
    assert unchanged.revision == 1
    assert changed.constraint_set_id == first.constraint_set_id
    assert changed.revision == 2


def test_repository_mutations_flush_without_commit_and_rollback_as_one_unit():
    db = make_session()
    seed_course(db)
    plan = load_course_plan(db, 1)
    semester = load_semester_plan(db, 1)
    replace_draft_schedule(
        db, plan, 1,
        [GeneratedSession(date(2026, 9, 7), start_time=time(8), end_time=time(11, 30), units=4, time_window_id=1, constraint_window_index=0)],
    )
    save_generation_constraints(
        db, plan, semester,
        PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20)),
        [TimeWindowPlan(id=1, weekday=0, start_time=time(8), end_time=time(12))],
    )
    assert get_draft_schedule(db, 1, 1) is not None
    assert load_generation_constraints(db, plan, semester).is_custom is True

    db.rollback()

    assert get_draft_schedule(db, 1, 1) is None
    assert load_generation_constraints(db, plan, semester).is_custom is False
