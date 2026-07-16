from datetime import date, time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
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
from app.services.draft_schedule_repository import (
    DraftSessionEditValidationError,
    ManualSessionValidationError,
    StaleDraftError,
    clear_generation_constraints,
    clear_course_draft,
    course_semester_progress,
    create_manual_draft_session,
    delete_draft_session,
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
        cohort_id=1,
        study_type_id=1,
        eligible_lecturers=[CourseEligibleLecturer(lecturer_id=1)],
        eligible_rooms=[CourseEligibleRoom(room_id=1)],
    )
    db.add_all([lecturer, cohort, room, room_2, small_room, study_type, semester, window, course])
    db.flush()
    db.add_all([
        CourseEligibleRoom(course_id=1, room_id=2),
        CourseEligibleRoom(course_id=1, room_id=3),
    ])
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


def seed_over_scheduled_draft(db):
    draft = seed_draft(db)
    db.get(Course, 1).total_units = 6
    db.flush()
    return draft


def seed_saved_constraints(db):
    return save_generation_constraints(
        db,
        load_course_plan(db, 1),
        load_semester_plan(db, 1),
        PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20)),
        [TimeWindowPlan(id=1, weekday=0, start_time=time(8), end_time=time(12))],
    )


def seed_cross_semester_draft(db):
    db.add(Semester(id=2, name="Spring", start_date=date(2027, 2, 1), end_date=date(2027, 6, 20)))
    db.flush()
    return replace_draft_schedule(
        db,
        load_course_plan(db, 1),
        2,
        [GeneratedSession(date(2027, 2, 1), start_time=time(8), end_time=time(9, 45), units=2, time_window_id=None, constraint_window_index=0)],
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


def test_draft_academic_snapshots_survive_source_edits():
    db = make_session()
    seed_course(db)
    draft = seed_draft(db)
    assert draft.course_name_snapshot == "Planning 101"
    assert draft.cohort_name_snapshot == "AI 1"
    assert draft.cohort_size_snapshot == 30
    assert draft.study_type_name_snapshot == "Full-time"
    assert draft.semester_name_snapshot == "Fall"

    db.get(Course, 1).name = "Renamed course"
    db.get(Cohort, 1).name = "Renamed cohort"
    db.get(Cohort, 1).student_count = 99
    db.get(StudyType, 1).name = "Renamed type"
    db.get(Semester, 1).name = "Renamed semester"
    db.commit()
    preserved = get_draft_schedule(db, 1, 1)
    assert preserved.course_name_snapshot == "Planning 101"
    assert preserved.cohort_name_snapshot == "AI 1"
    assert preserved.cohort_size_snapshot == 30
    assert preserved.study_type_name_snapshot == "Full-time"
    assert preserved.semester_name_snapshot == "Fall"


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


def test_update_draft_session_uses_current_cohort_size_after_cohort_shrink():
    db = make_session()
    seed_course(db)
    draft = seed_draft(db)
    target = draft.sessions[0]

    db.get(Cohort, 1).student_count = 15
    db.flush()

    updated = update_draft_session(
        db,
        target.id,
        date=target.date,
        start_time=target.start_time,
        end_time=target.end_time,
        room_id=3,
    )

    edited = next(session for session in updated.sessions if session.id == target.id)
    assert edited.room_id == 3


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


def test_manual_creation_builds_first_draft_appends_and_derives_progress():
    db = make_session()
    seed_course(db)

    assert course_semester_progress(db, 1, 1) == (20, 0, 20)
    first = create_manual_draft_session(
        db, 1, 1,
        session_date=date(2026, 9, 7), start_time=time(8), end_time=time(9, 45), units=2, room_id=2,
    )
    assert first.revision == 1
    assert first.course_name_snapshot == "Planning 101"
    assert first.sessions[0].lecturer_id == 1
    assert first.sessions[0].cohort_id == 1
    assert first.sessions[0].room_id == 2
    assert first.sessions[0].time_window_id is None
    assert course_semester_progress(db, 1, 1) == (20, 2, 18)

    second = create_manual_draft_session(
        db, 1, 1,
        session_date=date(2026, 9, 14), start_time=time(9), end_time=time(10), units=4, room_id=1,
    )
    assert second.id == first.id
    assert second.revision == 2
    assert [session.units for session in second.sessions] == [2, 4]
    assert course_semester_progress(db, 1, 1) == (20, 6, 14)


def test_manual_creation_enforces_every_hard_rule_without_changing_saved_state():
    db = make_session()
    seed_course(db)
    seed_saved_constraints(db)
    saved = create_manual_draft_session(
        db, 1, 1,
        session_date=date(2026, 9, 7), start_time=time(8), end_time=time(9, 45), units=2, room_id=1,
    )
    db.commit()
    original_revision = saved.revision

    invalid = [
        ({"session_date": date(2026, 9, 1), "start_time": time(8), "end_time": time(9), "units": 1, "room_id": 1}, "INVALID_SESSION_DATE"),
        ({"session_date": date(2026, 9, 14), "start_time": time(9), "end_time": time(9), "units": 1, "room_id": 1}, "INVALID_SESSION_TIME_RANGE"),
        ({"session_date": date(2026, 9, 14), "start_time": time(8), "end_time": time(9), "units": 1.5, "room_id": 1}, "INVALID_SESSION_UNITS"),
        ({"session_date": date(2026, 9, 14), "start_time": time(8), "end_time": time(9), "units": 19, "room_id": 1}, "UNITS_EXCEED_REMAINING"),
        ({"session_date": date(2026, 9, 7), "start_time": time(10), "end_time": time(11), "units": 1, "room_id": 1}, "DUPLICATE_SESSION_DATE"),
        ({"session_date": date(2026, 9, 14), "start_time": time(8), "end_time": time(9), "units": 1, "room_id": 3}, "INSUFFICIENT_ROOM_CAPACITY"),
    ]
    for values, code in invalid:
        with pytest.raises(ManualSessionValidationError) as caught:
            create_manual_draft_session(db, 1, 1, **values)
        assert caught.value.code == code
        db.rollback()

    unchanged = get_draft_schedule(db, 1, 1)
    assert unchanged is not None
    assert unchanged.revision == original_revision
    assert len(unchanged.sessions) == 1
    assert load_generation_constraints(db, load_course_plan(db, 1), load_semester_plan(db, 1)).is_custom is True


def test_over_scheduled_progress_is_clamped_and_manual_creation_is_rejected():
    db = make_session()
    seed_course(db)
    seed_over_scheduled_draft(db)
    assert course_semester_progress(db, 1, 1) == (6, 8, 0)
    with pytest.raises(ManualSessionValidationError) as caught:
        create_manual_draft_session(
            db, 1, 1,
            session_date=date(2026, 9, 21), start_time=time(8), end_time=time(9), units=1, room_id=1,
        )
    assert caught.value.code == "UNITS_EXCEED_REMAINING"


def test_concurrent_append_revalidates_remaining_units_against_the_winning_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'concurrent.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    seed = SessionLocal()
    seed_course(seed)
    seed.get(Course, 1).total_units = 4
    first = create_manual_draft_session(
        seed, 1, 1,
        session_date=date(2026, 9, 7), start_time=time(8), end_time=time(9, 45), units=2, room_id=1,
    )
    seed.commit()

    winner = SessionLocal()
    stale_reader = SessionLocal()
    assert get_draft_schedule(winner, 1, 1).revision == first.revision
    assert get_draft_schedule(stale_reader, 1, 1).revision == first.revision

    create_manual_draft_session(
        winner, 1, 1,
        session_date=date(2026, 9, 14), start_time=time(8), end_time=time(9, 45), units=2, room_id=1,
    )
    winner.commit()

    with pytest.raises(ManualSessionValidationError) as caught:
        create_manual_draft_session(
            stale_reader, 1, 1,
            session_date=date(2026, 9, 21), start_time=time(8), end_time=time(9), units=1, room_id=1,
        )
    assert caught.value.code == "UNITS_EXCEED_REMAINING"
    stale_reader.rollback()
    current = get_draft_schedule(stale_reader, 1, 1)
    assert current is not None
    assert current.revision == 2
    assert sum(session.units for session in current.sessions) == 4
    winner.close()
    stale_reader.close()
    seed.close()


def test_simultaneous_first_draft_creation_never_exceeds_remaining_units(tmp_path):
    for attempt in range(10):
        engine = create_engine(
            f"sqlite:///{tmp_path / f'first-draft-{attempt}.db'}",
            connect_args={"check_same_thread": False, "timeout": 2},
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        seed = SessionLocal()
        seed_course(seed)
        seed.get(Course, 1).total_units = 2
        seed.commit()
        seed.close()
        barrier = Barrier(2)

        def create_on(day: int) -> str:
            db = SessionLocal()
            try:
                barrier.wait()
                create_manual_draft_session(
                    db,
                    1,
                    1,
                    session_date=date(2026, 9, day),
                    start_time=time(8),
                    end_time=time(9, 45),
                    units=2,
                    room_id=1,
                )
                db.commit()
                return "CREATED"
            except ManualSessionValidationError as exc:
                db.rollback()
                return exc.code
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(create_on, (7, 14)))

        check = SessionLocal()
        saved = get_draft_schedule(check, 1, 1)
        assert saved is not None
        assert outcomes.count("CREATED") == 1
        assert outcomes.count("UNITS_EXCEED_REMAINING") == 1
        assert sum(session.units for session in saved.sessions) == 2
        check.close()
        engine.dispose()


def test_single_session_deletion_removes_only_target_and_last_deletion_removes_parent():
    db = make_session()
    seed_course(db)
    seed_saved_constraints(db)
    draft = seed_draft(db)
    db.commit()
    first_id, second_id = [session.id for session in draft.sessions]

    surviving, course_id, semester_id = delete_draft_session(
        db, first_id, expected_draft_schedule_id=draft.id, expected_revision=draft.revision,
    )
    assert (course_id, semester_id) == (1, 1)
    assert surviving is not None
    assert surviving.revision == 2
    assert [session.id for session in surviving.sessions] == [second_id]
    assert course_semester_progress(db, 1, 1) == (20, 4, 16)

    removed, _, _ = delete_draft_session(
        db, second_id, expected_draft_schedule_id=surviving.id, expected_revision=surviving.revision,
    )
    assert removed is None
    assert get_draft_schedule(db, 1, 1) is None
    assert course_semester_progress(db, 1, 1) == (20, 0, 20)
    assert load_generation_constraints(db, load_course_plan(db, 1), load_semester_plan(db, 1)).is_custom is True


def test_single_session_deletion_rejects_stale_or_missing_confirmed_target_without_changes():
    db = make_session()
    seed_course(db)
    draft = seed_draft(db)
    db.commit()
    target_id = draft.sessions[0].id
    original_ids = [session.id for session in draft.sessions]

    with pytest.raises(StaleDraftError) as stale:
        delete_draft_session(db, target_id, expected_draft_schedule_id=draft.id, expected_revision=draft.revision + 1)
    assert stale.value.current_revision == draft.revision

    with pytest.raises(StaleDraftError):
        delete_draft_session(db, 9999, expected_draft_schedule_id=draft.id, expected_revision=draft.revision)

    current = get_draft_schedule(db, 1, 1)
    assert current is not None
    assert [session.id for session in current.sessions] == original_ids


def test_single_deletion_recomputes_progress_from_over_scheduled_state():
    db = make_session()
    seed_course(db)
    draft = seed_over_scheduled_draft(db)
    db.commit()
    surviving, _, _ = delete_draft_session(
        db, draft.sessions[0].id, expected_draft_schedule_id=draft.id, expected_revision=draft.revision,
    )
    assert surviving is not None
    assert course_semester_progress(db, 1, 1) == (6, 4, 2)


def test_clear_course_draft_removes_parent_and_sessions_but_preserves_other_semester_and_constraints():
    db = make_session()
    seed_course(db)
    seed_saved_constraints(db)
    target = seed_draft(db)
    other_semester = seed_cross_semester_draft(db)
    db.commit()

    course_id, semester_id = clear_course_draft(
        db,
        1,
        1,
        expected_draft_schedule_id=target.id,
        expected_revision=target.revision,
    )
    assert (course_id, semester_id) == (1, 1)
    assert get_draft_schedule(db, 1, 1) is None
    assert get_draft_schedule(db, 1, 2).id == other_semester.id
    assert course_semester_progress(db, 1, 1) == (20, 0, 20)
    assert load_generation_constraints(db, load_course_plan(db, 1), load_semester_plan(db, 1)).is_custom is True


def test_clear_course_draft_rejects_stale_or_missing_confirmation_without_deleting_current_state():
    db = make_session()
    seed_course(db)
    target = seed_draft(db)
    db.commit()
    original_ids = [session.id for session in target.sessions]

    with pytest.raises(StaleDraftError) as stale:
        clear_course_draft(db, 1, 1, expected_draft_schedule_id=target.id, expected_revision=target.revision + 1)
    assert stale.value.current_revision == target.revision
    with pytest.raises(StaleDraftError):
        clear_course_draft(db, 1, 1, expected_draft_schedule_id=9999, expected_revision=1)

    current = get_draft_schedule(db, 1, 1)
    assert current is not None
    assert [session.id for session in current.sessions] == original_ids
