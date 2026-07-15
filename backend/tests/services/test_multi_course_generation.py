from datetime import date, time
from time import perf_counter

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.planning import (
    CourseEligibleLecturer,
    DraftSchedule,
    GenerationConstraintSet,
    Lecturer,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
)
from app.schemas.multi_course_generation import BatchOperationKind, PreparedCourseInput
from app.services.draft_schedule_repository import (
    get_draft_schedule,
    load_course_plan,
    load_semester_plan,
    save_generation_constraints,
)
from app.services.multi_course_generation import generate_batch, prepare_batch
from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan
from tests.multi_course_fixtures import seed_multi_course_planner


def make_session(database_url="sqlite://"):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        **({"poolclass": StaticPool} if database_url == "sqlite://" else {}),
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)(), engine


def prepared(*course_ids: int):
    return [
        PreparedCourseInput(courseId=course_id, expectedDraftScheduleId=None, expectedDraftRevision=None)
        for course_id in course_ids
    ]


def test_preparation_is_read_only_ordered_and_includes_unavailable_items():
    db, _ = make_session()
    seed_multi_course_planner(db)
    result = prepare_batch(db, 1, BatchOperationKind.INITIAL, [3, 999, 1])
    assert [item.course_id for item in result.courses] == [3, 999, 1]
    assert result.courses[1].available is False
    assert db.query(DraftSchedule).count() == 0


def test_generation_uses_each_courses_saved_constraints_or_defaults_without_rewriting_saved_set():
    db, _ = make_session()
    seed_multi_course_planner(db)
    plan = load_course_plan(db, 1)
    semester = load_semester_plan(db, 1)
    saved = save_generation_constraints(
        db,
        plan,
        semester,
        PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20)),
        [TimeWindowPlan(id=None, weekday=4, start_time=time(8), end_time=time(12))],
    )
    db.commit()

    result = generate_batch(db, 1, BatchOperationKind.INITIAL, prepared(1, 2))
    db.commit()

    assert result.summary.succeeded == 2
    assert all(session.date.weekday() == 4 for session in get_draft_schedule(db, 1, 1).sessions)
    assert all(session.date.weekday() == 0 for session in get_draft_schedule(db, 2, 1).sessions)
    current = db.query(GenerationConstraintSet).filter_by(course_id=1, semester_id=1).one()
    assert current.id == saved.constraint_set_id
    assert current.revision == 1


def test_unexpected_persistence_failure_can_roll_back_all_prior_course_savepoints(monkeypatch):
    db, _ = make_session()
    seed_multi_course_planner(db)
    import app.services.multi_course_generation as service

    original = service.replace_draft_schedule
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("injected unexpected failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_second)
    with pytest.raises(RuntimeError, match="injected unexpected failure"):
        generate_batch(db, 1, BatchOperationKind.INITIAL, prepared(1, 2))
    db.rollback()
    assert db.query(DraftSchedule).count() == 0
    assert db.query(GenerationConstraintSet).count() == 0


def test_fifty_course_generation_is_ordered_fast_and_uses_bounded_loading(tmp_path):
    db, engine = make_session(f"sqlite:///{tmp_path / 'fifty-courses.db'}")
    seed_multi_course_planner(db, course_count=50)
    statements = 0

    def count_statements(conn, cursor, statement, parameters, context, executemany):
        nonlocal statements
        if statement.lstrip().upper().startswith("SELECT"):
            statements += 1

    event.listen(engine, "before_cursor_execute", count_statements)
    started = perf_counter()
    result = generate_batch(db, 1, BatchOperationKind.INITIAL, prepared(*range(1, 51)))
    db.commit()
    elapsed = perf_counter() - started
    event.remove(engine, "before_cursor_execute", count_statements)

    assert elapsed < 10
    assert result.summary.succeeded == 50
    assert [item.course_id for item in result.outcomes] == list(range(1, 51))
    assert statements < 30


def test_changed_saved_constraints_are_reported_as_stale_without_replacing_draft(monkeypatch):
    db, _ = make_session()
    seed_multi_course_planner(db)
    plan = load_course_plan(db, 1)
    semester = load_semester_plan(db, 1)
    save_generation_constraints(
        db, plan, semester,
        PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20)),
        [TimeWindowPlan(id=None, weekday=4, start_time=time(8), end_time=time(12))],
    )
    db.commit()
    import app.services.multi_course_generation as service
    original = service._bulk_load
    calls = 0

    def change_between_snapshot_and_persistence(*args, **kwargs):
        nonlocal calls
        calls += 1
        loaded = original(*args, **kwargs)
        if calls == 2:
            saved = db.query(GenerationConstraintSet).filter_by(course_id=1, semester_id=1).one()
            saved.revision += 1
            db.flush()
        return loaded

    monkeypatch.setattr(service, "_bulk_load", change_between_snapshot_and_persistence)
    result = generate_batch(db, 1, BatchOperationKind.RETRY, prepared(1))
    assert result.outcomes[0].errors[0].code == "STALE_GENERATION_CONSTRAINTS"
    assert get_draft_schedule(db, 1, 1) is None


def test_batch_generation_assigns_resources_within_each_course_independently():
    db, _ = make_session()
    seed_multi_course_planner(db, course_count=2)
    alternate = Lecturer(
        id=20,
        name="Course 1 Alternate",
        reference_code="LEC-020",
        normalized_reference_code="lec-020",
    )
    blocked = ResourceUnavailabilityPeriod(
        lecturer_id=1,
        kind="recurring",
        start_time=time(8),
        end_time=time(12),
    )
    blocked.weekdays = [
        ResourceUnavailabilityWeekday(weekday=0),
        ResourceUnavailabilityWeekday(weekday=2),
    ]
    db.add_all([alternate, CourseEligibleLecturer(course_id=1, lecturer_id=20), blocked])
    db.commit()

    result = generate_batch(db, 1, BatchOperationKind.INITIAL, prepared(1, 2))
    db.commit()

    assert result.summary.succeeded == 2
    course_one = get_draft_schedule(db, 1, 1)
    course_two = get_draft_schedule(db, 2, 1)
    assert {session.lecturer_id for session in course_one.sessions} == {20}
    assert {session.lecturer_id for session in course_two.sessions} == {2}
