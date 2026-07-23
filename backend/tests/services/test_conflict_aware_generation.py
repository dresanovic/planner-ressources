import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace

from app.db.base import Base
from datetime import date, time

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    Lecturer,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
    Room,
    Semester,
    StudyTypeTimeWindow,
    InstitutionHoliday,
)
from app.schemas.conflict_aware_generation import PreparedOptimizationCourseInput
from app.services.conflict_aware_generation import generate_optimization, prepare_optimization
from app.services.draft_schedule_repository import load_course_plan, replace_draft_schedule
from app.services.schedule_generation import GeneratedSession
from tests.optimization_fixtures import seed_optimization_planner


def make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def execution_courses(preparation):
    return [PreparedOptimizationCourseInput(
        courseId=item.course_id,
        expectedDraftScheduleId=item.draft_schedule_id,
        expectedDraftRevision=item.draft_revision,
        inputSnapshotToken=item.input_snapshot_token,
    ) for item in preparation.courses]


def save_custom_constraints(db, course_id, weekday, source_window_id):
    constraint_set = GenerationConstraintSet(
        course_id=course_id,
        semester_id=1,
        planning_start_date=date(2026, 9, 7),
        planning_end_date=date(2026, 12, 20),
    )
    constraint_set.windows = [GenerationConstraintWindow(
        source_time_window_id=source_window_id,
        weekday=weekday,
        start_time=time(8),
        end_time=time(12),
        sort_order=1,
    )]
    db.add(constraint_set)


def test_preparation_is_canonical_read_only_and_generation_saves_complete_results_and_defaults():
    db = make_session()
    seed_optimization_planner(db, course_count=2)
    prepared = prepare_optimization(db, 1, [2, 1], ["2026-10-26", "2026-10-26"])
    assert prepared.unavailable_dates == [prepared.unavailable_dates[0]]
    assert [item.course_id for item in prepared.courses] == [1, 2]
    assert db.query(DraftSchedule).count() == 0

    result = generate_optimization(db, 1, execution_courses(prepared), prepared.unavailable_dates, prepared.shared_snapshot_token)
    db.commit()

    assert result.summary.complete == 2
    assert result.summary.optimal_for_prepared_snapshot is True
    assert db.query(DraftSchedule).count() == 2
    assert db.query(GenerationConstraintSet).count() == 2


def test_preparation_tokens_are_bound_to_the_schedule_revision():
    db = make_session()
    seed_optimization_planner(db, course_count=1)

    first = prepare_optimization(db, 1, [1], [], schedule_revision_id=11)
    second = prepare_optimization(db, 1, [1], [], schedule_revision_id=12)

    assert first.shared_snapshot_token != second.shared_snapshot_token
    assert first.courses[0].input_snapshot_token != second.courses[0].input_snapshot_token


def test_optimization_claims_lifecycle_only_after_solver_finishes(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2)
    import app.services.conflict_aware_generation as service

    events = []
    original_optimize = service.optimize_semester

    def tracked_optimize(*args, **kwargs):
        events.append("solve")
        return original_optimize(*args, **kwargs)

    monkeypatch.setattr(service, "optimize_semester", tracked_optimize)
    monkeypatch.setattr(
        service,
        "claim_active_working_revision",
        lambda *_args, **_kwargs: events.append("claim"),
    )
    prepared = prepare_optimization(
        db, 1, [1, 2], [], schedule_revision_id=99
    )

    generate_optimization(
        db,
        1,
        execution_courses(prepared),
        [],
        prepared.shared_snapshot_token,
        schedule_revision_id=99,
    )

    assert events == ["solve", "claim"]


def test_holidays_are_server_authoritative_named_blockers_without_changing_caller_unavailable_dates():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    save_custom_constraints(db, 1, 0, 1)
    constraints = db.query(GenerationConstraintSet).filter_by(course_id=1, semester_id=1).one()
    constraints.planning_end_date = date(2026, 9, 7)
    db.add(InstitutionHoliday(date=date(2026, 9, 7), name="Founders Day"))
    db.commit()

    prepared = prepare_optimization(db, 1, [1], ["2026-10-26"])
    result = generate_optimization(
        db,
        1,
        execution_courses(prepared),
        prepared.unavailable_dates,
        prepared.shared_snapshot_token,
    )

    assert prepared.unavailable_dates == [date(2026, 10, 26)]
    reason = next(item for item in result.outcomes[0].reasons if item.code == "INSTITUTION_HOLIDAY")
    assert reason.holiday_date == date(2026, 9, 7)
    assert reason.holiday_name == "Founders Day"
    assert result.outcomes[0].saved is False


def test_holiday_change_after_preparation_invalidates_snapshot_without_saving():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    prepared = prepare_optimization(db, 1, [1], [])
    db.add(InstitutionHoliday(date=date(2026, 9, 7), name="New Closure"))
    db.commit()

    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert result.summary.stale == 1
    assert result.outcomes[0].saved is False
    assert db.query(DraftSchedule).count() == 0


def test_changed_course_input_is_stale_and_preserved():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    prepared = prepare_optimization(db, 1, [1], [])
    db.get(Course, 1).total_units = 10
    db.commit()
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    assert result.summary.stale == 1
    assert result.outcomes[0].saved is False
    assert db.query(DraftSchedule).count() == 0


def test_partial_existing_draft_is_replaced_only_with_more_units_and_complete_draft_is_preserved():
    db = make_session()
    seed_optimization_planner(db, course_count=2)
    partial = replace_draft_schedule(db, load_course_plan(db, 1), 1, [GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1)])
    complete = replace_draft_schedule(db, load_course_plan(db, 2), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 2, 2),
        GeneratedSession(date(2026, 9, 14), time(8), time(11, 30), 4, 1, 0, 2, 2),
    ])
    db.commit()
    partial_revision = partial.revision
    complete_revision = complete.revision
    prepared = prepare_optimization(db, 1, [1, 2], [])
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    db.commit()

    one = next(item for item in result.outcomes if item.course_id == 1)
    two = next(item for item in result.outcomes if item.course_id == 2)
    assert one.status == "complete" and one.scheduled_units == 8 and one.draft_revision == partial_revision + 1
    assert two.status == "unchanged" and two.draft_revision == complete_revision


def test_zero_placement_creates_no_empty_draft_and_reports_substantiated_reason():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    db.get(Lecturer, 1).is_active = False
    db.commit()
    prepared = prepare_optimization(db, 1, [1], [])
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    assert result.outcomes[0].status == "unchanged"
    assert result.outcomes[0].draft_schedule_id is None
    assert {item.code for item in result.outcomes[0].reasons} >= {"NO_ELIGIBLE_LECTURER"}
    assert db.query(DraftSchedule).count() == 0


def test_unfillable_remaining_units_report_course_constraint_in_saved_partial_outcome():
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=5)
    course = db.get(Course, 1)
    course.max_session_units = 3
    course.revision += 1
    save_custom_constraints(db, 1, 0, 1)
    constraints = db.query(GenerationConstraintSet).filter_by(course_id=1, semester_id=1).one()
    constraints.planning_end_date = date(2026, 9, 7)
    db.commit()
    prepared = prepare_optimization(db, 1, [1], [])

    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    outcome = result.outcomes[0]

    assert outcome.status == "improved_partial"
    assert outcome.scheduled_units == 3
    assert outcome.remaining_units == 2
    assert {item.code for item in outcome.reasons} >= {"COURSE_CONSTRAINT"}


def test_post_solve_stale_course_is_preserved_while_exact_unaffected_result_saves_without_resolve(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2)
    prepared = prepare_optimization(db, 1, [1, 2], [])
    import app.services.conflict_aware_generation as service
    original = service.optimize_semester
    calls = 0

    def solve_then_change(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = original(*args, **kwargs)
        db.get(Course, 1).total_units = 10
        db.flush()
        return result

    monkeypatch.setattr(service, "optimize_semester", solve_then_change)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    db.commit()

    assert calls == 1
    assert result.summary.stale == 1 and result.summary.complete == 1
    assert next(item for item in result.outcomes if item.course_id == 1).saved is False
    assert next(item for item in result.outcomes if item.course_id == 2).saved is True
    assert db.query(DraftSchedule).count() == 1


def test_course_save_failure_rolls_back_only_that_course_and_keeps_exact_unaffected_save(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2)
    prepared = prepare_optimization(db, 1, [1, 2], [])
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    db.commit()

    assert result.summary.failed == 1 and result.summary.complete == 1
    assert next(item for item in result.outcomes if item.course_id == 1).errors[0].code == "COURSE_SAVE_FAILED"
    assert db.query(DraftSchedule).count() == 1


def test_unavailable_selected_draft_remains_fixed_occupancy_for_eligible_courses():
    db = make_session()
    seed_optimization_planner(db, course_count=2, total_units=4)
    replace_draft_schedule(db, load_course_plan(db, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    db.query(CourseEligibleLecturer).filter(CourseEligibleLecturer.course_id == 2).delete()
    db.query(CourseEligibleRoom).filter(CourseEligibleRoom.course_id == 2).delete()
    db.add_all([
        CourseEligibleLecturer(course_id=2, lecturer_id=1),
        CourseEligibleRoom(course_id=2, room_id=1),
    ])
    db.get(Course, 1).is_active = False
    db.commit()

    prepared = prepare_optimization(db, 1, [1, 2], [])
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    drafts = {item.course_id: item for item in db.query(DraftSchedule).all()}

    assert next(item for item in prepared.courses if item.course_id == 1).available is False
    assert next(item for item in result.outcomes if item.course_id == 1).status == "failed"
    assert drafts[1].sessions[0].date == date(2026, 9, 7)
    assert drafts[2].sessions[0].date != date(2026, 9, 7)


def test_inactive_cohort_is_not_available_and_cannot_be_saved():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    db.get(Cohort, 1).is_active = False
    db.commit()

    prepared = prepare_optimization(db, 1, [1], [])
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert prepared.courses[0].available is False
    assert result.outcomes[0].status == "failed"
    assert result.outcomes[0].saved is False
    assert db.query(DraftSchedule).count() == 0


def test_post_solve_semester_change_marks_custom_constraint_result_stale(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    save_custom_constraints(db, 1, 0, 1)
    db.commit()
    prepared = prepare_optimization(db, 1, [1], [])
    import app.services.conflict_aware_generation as service
    original = service.optimize_semester

    def solve_then_change(*args, **kwargs):
        result = original(*args, **kwargs)
        semester = db.get(Semester, 1)
        semester.start_date = date(2026, 10, 1)
        semester.revision += 1
        db.flush()
        return result

    monkeypatch.setattr(service, "optimize_semester", solve_then_change)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert result.outcomes[0].status == "stale"
    assert result.outcomes[0].saved is False
    assert db.query(DraftSchedule).count() == 0


def test_save_failure_revalidates_later_results_against_preserved_draft(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2, total_units=4)
    db.query(CourseEligibleLecturer).filter(CourseEligibleLecturer.course_id == 2).delete()
    db.query(CourseEligibleRoom).filter(CourseEligibleRoom.course_id == 2).delete()
    db.add_all([
        CourseEligibleLecturer(course_id=2, lecturer_id=1),
        CourseEligibleRoom(course_id=2, room_id=1),
    ])
    replace_draft_schedule(db, load_course_plan(db, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 30), 2, 1, 0, 1, 1),
    ])
    save_custom_constraints(db, 1, 2, 2)
    save_custom_constraints(db, 2, 0, 1)
    db.commit()
    prepared = prepare_optimization(db, 1, [1, 2], [])
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert next(item for item in result.outcomes if item.course_id == 1).status == "failed"
    assert next(item for item in result.outcomes if item.course_id == 2).status in {"stale", "failed"}
    assert db.query(DraftSchedule).count() == 1


def test_operation_rollback_removes_released_course_savepoint(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    prepared = prepare_optimization(db, 1, [1], [])
    import app.services.conflict_aware_generation as service

    monkeypatch.setattr(
        service,
        "OptimizationGenerationResult",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("after-save failure")),
    )
    try:
        generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    except RuntimeError:
        db.rollback()

    assert db.query(DraftSchedule).count() == 0


def test_no_solver_run_does_not_claim_prepared_snapshot_optimality():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    prepared = prepare_optimization(db, 1, [1], [])

    result = generate_optimization(db, 1, execution_courses(prepared), [], "changed-shared-token")

    assert result.summary.stale == 1
    assert result.summary.optimal_for_prepared_snapshot is False


def test_post_solve_reload_detects_change_committed_by_another_session(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    prepared = prepare_optimization(db, 1, [1], [])
    import app.services.conflict_aware_generation as service
    original = service.optimize_semester

    def solve_then_change_elsewhere(*args, **kwargs):
        result = original(*args, **kwargs)
        other_db = sessionmaker(bind=db.get_bind())()
        course = other_db.get(Course, 1)
        course.total_units = 10
        course.revision += 1
        other_db.commit()
        other_db.close()
        return result

    monkeypatch.setattr(service, "optimize_semester", solve_then_change_elsewhere)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert result.outcomes[0].status == "stale"
    assert result.outcomes[0].saved is False
    assert db.query(DraftSchedule).count() == 0


def test_asymmetric_save_failure_keeps_unaffected_dependency_result(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2, total_units=4)
    db.query(CourseEligibleLecturer).filter(CourseEligibleLecturer.course_id == 2).delete()
    db.query(CourseEligibleRoom).filter(CourseEligibleRoom.course_id == 2).delete()
    db.add_all([
        CourseEligibleLecturer(course_id=2, lecturer_id=1),
        CourseEligibleRoom(course_id=2, room_id=1),
    ])
    replace_draft_schedule(db, load_course_plan(db, 1), 1, [
        GeneratedSession(date(2026, 9, 11), time(8), time(9, 30), 2, 1, 0, 1, 1),
    ])
    replace_draft_schedule(db, load_course_plan(db, 2), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 30), 2, 1, 0, 1, 1),
    ])
    save_custom_constraints(db, 1, 0, 1)
    save_custom_constraints(db, 2, 2, 2)
    db.commit()
    prepared = prepare_optimization(db, 1, [1, 2], [])
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    first = next(item for item in result.outcomes if item.course_id == 1)
    second = next(item for item in result.outcomes if item.course_id == 2)

    assert first.status == "failed" and first.saved is False
    assert second.status == "complete" and second.saved is True
    assert second.draft_revision == 2


def test_mutual_save_dependency_rolls_back_the_atomic_cycle(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2, total_units=4)
    db.query(CourseEligibleLecturer).filter(CourseEligibleLecturer.course_id == 2).delete()
    db.query(CourseEligibleRoom).filter(CourseEligibleRoom.course_id == 2).delete()
    db.add_all([
        CourseEligibleLecturer(course_id=2, lecturer_id=1),
        CourseEligibleRoom(course_id=2, room_id=1),
    ])
    replace_draft_schedule(db, load_course_plan(db, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 30), 2, 1, 0, 1, 1),
    ])
    replace_draft_schedule(db, load_course_plan(db, 2), 1, [
        GeneratedSession(date(2026, 9, 9), time(8), time(9, 30), 2, 1, 0, 1, 1),
    ])
    save_custom_constraints(db, 1, 2, 2)
    save_custom_constraints(db, 2, 0, 1)
    db.commit()
    prepared = prepare_optimization(db, 1, [1, 2], [])
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert [item.status for item in result.outcomes] == ["failed", "failed"]
    assert all(item.saved is False and item.draft_revision == 1 for item in result.outcomes)


def test_solver_budget_reserves_time_for_revalidation_and_saving(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    prepared = prepare_optimization(db, 1, [1], [])
    import app.services.conflict_aware_generation as service
    original = service.optimize_semester
    solver_budgets = []

    def record_budget(*args, **kwargs):
        solver_budgets.append(kwargs["deadline_seconds"])
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "optimize_semester", record_budget)
    generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert solver_budgets and solver_budgets[0] <= 55.0


def test_equal_unit_replacement_uses_lexicographic_arrangement_priorities():
    import app.services.conflict_aware_generation as service

    draft = SimpleNamespace(sessions=[
        SimpleNamespace(
            date=date(2026, 9, 7), start_time=time(8), end_time=time(9, 30),
            units=2, cohort_id=1, lecturer_id=1, room_id=1,
        ),
        SimpleNamespace(
            date=date(2026, 9, 14), start_time=time(8), end_time=time(9, 30),
            units=2, cohort_id=1, lecturer_id=1, room_id=2,
        ),
    ])
    item = SimpleNamespace(course=SimpleNamespace(id=1), draft=draft)
    operation = SimpleNamespace(fixed_sessions=(), courses=(item,))
    candidate = service.CourseOptimization(
        course_id=1,
        sessions=(),
        retained_current=False,
        scheduled_units=4,
        lecturer_changes=1,
        room_changes=0,
        evidence=(),
    )

    assert service._candidate_improvement(item, candidate, operation) is None


def test_no_solver_stale_outcome_reloads_current_saved_state(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    prepared = prepare_optimization(db, 1, [1], [])
    import app.services.conflict_aware_generation as service
    original = service.load_operation
    load_calls = 0

    def load_after_external_change(*args, **kwargs):
        nonlocal load_calls
        load_calls += 1
        if load_calls == 2:
            other_db = sessionmaker(bind=db.get_bind())()
            course = other_db.get(Course, 1)
            course.total_units = 10
            course.revision += 1
            other_db.commit()
            other_db.close()
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "load_operation", load_after_external_change)
    result = generate_optimization(db, 1, execution_courses(prepared), [], "changed-shared-token")

    assert result.outcomes[0].status == "stale"
    assert result.outcomes[0].remaining_units == 10
    assert result.summary.optimal_for_prepared_snapshot is False


@pytest.mark.parametrize("changed_input", [
    "lecturer_eligibility",
    "room_eligibility",
    "room_capacity",
    "lecturer_active_state",
    "lecturer_availability",
    "active_time_window",
    "saved_constraints",
    "unavailable_dates",
    "relevant_fixed_occupancy",
])
def test_material_input_changes_after_preparation_are_stale_and_preserved(changed_input):
    db = make_session()
    seed_optimization_planner(
        db,
        course_count=2 if changed_input == "relevant_fixed_occupancy" else 1,
        total_units=4,
    )
    prepared = prepare_optimization(db, 1, [1], [])
    generation_dates = []

    if changed_input == "lecturer_eligibility":
        db.query(CourseEligibleLecturer).filter_by(course_id=1, lecturer_id=1).delete()
    elif changed_input == "room_eligibility":
        db.query(CourseEligibleRoom).filter_by(course_id=1, room_id=1).delete()
    elif changed_input == "room_capacity":
        room = db.get(Room, 1)
        room.capacity = 20
        room.revision += 1
    elif changed_input == "lecturer_active_state":
        lecturer = db.get(Lecturer, 1)
        lecturer.is_active = False
        lecturer.revision += 1
    elif changed_input == "lecturer_availability":
        db.add(ResourceUnavailabilityPeriod(
            lecturer_id=1,
            kind="recurring",
            start_time=time(8),
            end_time=time(12),
            weekdays=[ResourceUnavailabilityWeekday(weekday=0)],
        ))
    elif changed_input == "active_time_window":
        window = db.get(StudyTypeTimeWindow, 1)
        window.is_active = False
        window.revision += 1
    elif changed_input == "saved_constraints":
        save_custom_constraints(db, 1, 2, 2)
    elif changed_input == "unavailable_dates":
        generation_dates = [date(2026, 10, 26)]
    elif changed_input == "relevant_fixed_occupancy":
        replace_draft_schedule(db, load_course_plan(db, 2), 1, [
            GeneratedSession(date(2026, 9, 7), time(8), time(9, 30), 2, 1, 0, 1, 1),
        ])
    db.commit()

    result = generate_optimization(
        db,
        1,
        execution_courses(prepared),
        generation_dates,
        prepared.shared_snapshot_token,
    )

    assert result.summary.stale == 1
    assert result.summary.optimal_for_prepared_snapshot is False
    assert result.outcomes[0].status == "stale"
    assert result.outcomes[0].saved is False
    assert load_course_plan(db, 1).id == 1
    assert db.query(DraftSchedule).filter_by(course_id=1, semester_id=1).one_or_none() is None
