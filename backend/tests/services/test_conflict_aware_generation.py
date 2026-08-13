import pytest
import app.services.conflict_aware_generation as conflict_aware_service
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
    ExamSession,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    Lecturer,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
    Room,
    ScheduleRevision,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
    InstitutionHoliday,
)
from app.schemas.conflict_aware_generation import PreparedOptimizationCourseInput
from app.services.conflict_aware_generation import accept_optimization, InvalidOptimizationSelection, candidate_fingerprint, generate_optimization, load_operation, prepare_optimization
from app.services.draft_schedule_repository import load_course_plan, replace_draft_schedule
from app.services.schedule_generation import GeneratedSession
from app.services.semester_optimization import CourseOptimization, SemesterOptimizationResult
from tests.optimization_fixtures import active_exam, past_exam, seed_optimization_planner


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
    assert db.query(GenerationConstraintSet).count() == 0


def test_active_exams_are_loaded_as_protected_occupancy_and_past_exams_are_absent_from_tokens(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    import app.services.conflict_aware_generation as service

    monkeypatch.setattr(conflict_aware_service, "institution_today", lambda: date(2026, 9, 1))
    db.add(active_exam(exam_id=40, course_id=1))
    db.commit()
    before_past = prepare_optimization(db, 1, [1], [])

    db.add(past_exam(exam_id=41, course_id=1))
    db.commit()
    after_past = prepare_optimization(db, 1, [1], [])
    loaded = load_operation(db, 1, [1], [])

    assert before_past.shared_snapshot_token == after_past.shared_snapshot_token
    assert before_past.courses[0].input_snapshot_token == after_past.courses[0].input_snapshot_token
    assert {(row.source_kind, row.source_id) for row in loaded.fixed_sessions} == {
        ("active_exam", 40)
    }
    assert loaded.courses[0].optimization.latest_teaching_end.date() == date(2026, 10, 5)
    assert loaded.courses[0].optimization.latest_teaching_source_id == 40

    db.add(active_exam(exam_id=42, course_id=1, exam_date=date(2026, 10, 12)))
    db.commit()
    after_active = prepare_optimization(db, 1, [1], [])
    assert after_active.shared_snapshot_token != after_past.shared_snapshot_token


def test_active_exam_resource_conflicts_keep_precise_codes_and_source_evidence(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2, total_units=4)
    import app.services.conflict_aware_generation as service

    monkeypatch.setattr(conflict_aware_service, "institution_today", lambda: date(2026, 9, 1))
    db.query(CourseEligibleLecturer).filter(CourseEligibleLecturer.course_id == 2).delete()
    db.query(CourseEligibleRoom).filter(CourseEligibleRoom.course_id == 2).delete()
    db.add_all([
        CourseEligibleLecturer(course_id=2, lecturer_id=1),
        CourseEligibleRoom(course_id=2, room_id=1),
        active_exam(
            exam_id=50,
            course_id=1,
            exam_date=date(2026, 10, 5),
            start=time(8),
            end=time(12),
        ),
        GenerationConstraintSet(
            course_id=2,
            semester_id=1,
            planning_start_date=date(2026, 10, 5),
            planning_end_date=date(2026, 10, 5),
        ),
    ])
    db.get(Course, 2).cohort_id = 1
    db.commit()
    prepared = prepare_optimization(db, 1, [2], [])

    result = generate_optimization(
        db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token
    )

    reasons = {(row.code.value, row.source_kind, row.source_id) for row in result.outcomes[0].reasons}
    assert reasons >= {
        ("LECTURER_OCCUPIED", "active_exam", 50),
        ("ROOM_OCCUPIED", "active_exam", 50),
        ("COHORT_OCCUPIED", "active_exam", 50),
    }
    assert db.query(DraftSchedule).count() == 0
    protected_exam = db.get(ExamSession, 50)
    assert (protected_exam.exam_date, protected_exam.start_time, protected_exam.end_time, protected_exam.revision) == (
        date(2026, 10, 5), time(8), time(12), 1
    )


def test_active_same_course_exam_boundary_and_short_study_window_are_precise(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=2, total_units=4)
    import app.services.conflict_aware_generation as service

    monkeypatch.setattr(service, "institution_today", lambda: date(2026, 9, 1))
    db.add_all([
        active_exam(
            exam_id=60,
            course_id=1,
            exam_date=date(2026, 9, 7),
            start=time(9, 40),
            end=time(11, 40),
        ),
        GenerationConstraintSet(
            course_id=1,
            semester_id=1,
            planning_start_date=date(2026, 9, 7),
            planning_end_date=date(2026, 9, 7),
        ),
        StudyType(id=2, name="Short-window study"),
        StudyTypeTimeWindow(
            id=3,
            study_type_id=2,
            weekday=0,
            start_time=time(8),
            end_time=time(9),
            sort_order=1,
        ),
    ])
    db.get(Course, 2).study_type_id = 2
    db.commit()

    boundary_prepared = prepare_optimization(db, 1, [1], [])
    boundary = generate_optimization(
        db, 1, execution_courses(boundary_prepared), [], boundary_prepared.shared_snapshot_token
    ).outcomes[0]
    with pytest.raises(InvalidOptimizationSelection) as unavailable:
        prepare_optimization(db, 1, [2], [])

    assert boundary.scheduled_units == 2
    reason = next(row for row in boundary.reasons if row.code == "ACTIVE_EXAM_BOUNDARY")
    assert (reason.source_kind, reason.source_id) == ("active_exam", 60)
    assert unavailable.value.code == "STUDY_TYPE_WINDOW_UNAVAILABLE"


def test_unproven_solver_result_preserves_all_existing_state(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    original = replace_draft_schedule(db, load_course_plan(db, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    db.commit()
    prepared = prepare_optimization(db, 1, [1], [], schedule_revision_id=1)
    import app.services.conflict_aware_generation as service
    from app.services.semester_optimization import OptimalResultNotProven

    monkeypatch.setattr(
        service,
        "optimize_semester",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OptimalResultNotProven("timeout")),
    )
    with pytest.raises(OptimalResultNotProven):
        generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token, schedule_revision_id=1)
    db.rollback()

    preserved = db.get(DraftSchedule, original.id)
    assert preserved.revision == original.revision
    assert [(row.date, row.start_time, row.end_time) for row in preserved.sessions] == [
        (date(2026, 9, 7), time(8), time(9, 40))
    ]


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


def test_existing_drafts_are_previewed_then_replaced_as_one_accepted_result():
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
    prepared = prepare_optimization(db, 1, [1, 2], [], schedule_revision_id=1)
    preview = generate_optimization(
        db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token,
        schedule_revision_id=1,
    )
    assert partial.revision == partial_revision
    assert complete.revision == complete_revision
    result = accept_optimization(
        db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token, 1,
        preview.candidate_fingerprint,
    )
    db.commit()

    one = next(item for item in result.outcomes if item.course_id == 1)
    two = next(item for item in result.outcomes if item.course_id == 2)
    assert one.status == "complete" and one.scheduled_units == 8 and one.draft_revision == partial_revision + 1
    assert two.status == "complete" and two.saved is True and two.draft_revision == complete_revision + 1


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


def test_post_solve_stale_course_invalidates_complete_operation_without_saving(monkeypatch):
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
    assert result.summary.stale == 2 and result.summary.complete == 0
    assert result.summary.optimal_for_prepared_snapshot is False
    assert all(item.saved is False for item in result.outcomes)
    assert db.query(DraftSchedule).count() == 0


def test_course_save_failure_rolls_back_every_selected_course(monkeypatch):
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
    with pytest.raises(RuntimeError, match="injected course save failure"):
        generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)
    db.rollback()

    assert db.query(DraftSchedule).count() == 0


def test_unavailable_selected_course_rejects_complete_selection_without_mutation():
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

    with pytest.raises(InvalidOptimizationSelection) as rejected:
        prepare_optimization(db, 1, [1, 2], [])
    drafts = {item.course_id: item for item in db.query(DraftSchedule).all()}

    assert rejected.value.code == "RECORD_INACTIVE"
    assert drafts[1].sessions[0].date == date(2026, 9, 7)
    assert 2 not in drafts


def test_inactive_cohort_rejects_selection_and_cannot_be_saved():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    db.get(Cohort, 1).is_active = False
    db.commit()

    with pytest.raises(InvalidOptimizationSelection) as rejected:
        prepare_optimization(db, 1, [1], [])

    assert rejected.value.code == "COHORT_INACTIVE"
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


def test_save_failure_preserves_existing_draft_and_discards_later_results(monkeypatch):
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
    first_constraints = db.query(GenerationConstraintSet).filter_by(course_id=1).one()
    first_constraints.planning_start_date = date(2026, 9, 9)
    first_constraints.planning_end_date = date(2026, 9, 9)
    second_constraints = db.query(GenerationConstraintSet).filter_by(course_id=2).one()
    second_constraints.planning_start_date = date(2026, 9, 7)
    second_constraints.planning_end_date = date(2026, 9, 7)
    db.commit()
    prepared = prepare_optimization(db, 1, [1, 2], [], schedule_revision_id=1)
    preview = generate_optimization(
        db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token,
        schedule_revision_id=1,
    )
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    with pytest.raises(RuntimeError, match="injected course save failure"):
        accept_optimization(
            db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token, 1,
            preview.candidate_fingerprint,
        )
    db.rollback()
    draft = db.query(DraftSchedule).one()

    assert draft.course_id == 1
    assert draft.revision == 1


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


def test_asymmetric_save_failure_rolls_back_all_dependency_results(monkeypatch):
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
    prepared = prepare_optimization(db, 1, [1, 2], [], schedule_revision_id=1)
    preview = generate_optimization(
        db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token,
        schedule_revision_id=1,
    )
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    with pytest.raises(RuntimeError, match="injected course save failure"):
        accept_optimization(
            db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token, 1,
            preview.candidate_fingerprint,
        )
    db.rollback()
    drafts = {item.course_id: item for item in db.query(DraftSchedule).all()}

    assert drafts[1].revision == 1
    assert drafts[2].revision == 1


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
    prepared = prepare_optimization(db, 1, [1, 2], [], schedule_revision_id=1)
    preview = generate_optimization(
        db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token,
        schedule_revision_id=1,
    )
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_first(database, course_plan, *args, **kwargs):
        if course_plan.id == 1:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_first)
    with pytest.raises(RuntimeError, match="injected course save failure"):
        accept_optimization(
            db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token, 1,
            preview.candidate_fingerprint,
        )
    db.rollback()
    drafts = {item.course_id: item for item in db.query(DraftSchedule).all()}

    assert drafts[1].revision == 1
    assert drafts[2].revision == 1


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


def test_active_exam_added_after_preparation_is_stale_and_preserves_saved_constraints(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    save_custom_constraints(db, 1, 0, 1)
    db.commit()
    monkeypatch.setattr(conflict_aware_service, "institution_today", lambda: date(2026, 9, 1))
    prepared = prepare_optimization(db, 1, [1], [])
    saved_revision = db.query(GenerationConstraintSet).filter_by(course_id=1, semester_id=1).one().revision

    db.add(active_exam(exam_id=90, course_id=1, exam_date=date(2026, 10, 5)))
    db.commit()
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert result.outcomes[0].status == "stale"
    assert result.outcomes[0].saved is False
    assert db.query(DraftSchedule).filter_by(course_id=1, semester_id=1).one_or_none() is None
    assert db.query(GenerationConstraintSet).filter_by(course_id=1, semester_id=1).one().revision == saved_revision


def test_past_exam_added_after_preparation_does_not_make_snapshot_stale(monkeypatch):
    db = make_session()
    seed_optimization_planner(db, course_count=1, total_units=4)
    monkeypatch.setattr(conflict_aware_service, "institution_today", lambda: date(2026, 9, 1))
    prepared = prepare_optimization(db, 1, [1], [])

    db.add(past_exam(exam_id=91, course_id=1))
    db.commit()
    result = generate_optimization(db, 1, execution_courses(prepared), [], prepared.shared_snapshot_token)

    assert result.summary.stale == 0
    assert result.outcomes[0].status in {"complete", "partial"}
    assert result.outcomes[0].saved is True


def test_candidate_fingerprint_is_canonical_and_covers_exact_joint_session_fields():
    first_session = GeneratedSession(
        date(2026, 9, 7), time(8), time(9, 40), 2, 11, 0, 101, 201
    )
    second_session = GeneratedSession(
        date(2026, 9, 14), time(10), time(11, 40), 2, 12, 1, 102, 202
    )
    courses = (
        CourseOptimization(2, (second_session, first_session), False, 4, 1, 1, ()),
        CourseOptimization(1, (first_session,), False, 2, 0, 0, ()),
    )
    reordered = (
        CourseOptimization(1, (first_session,), False, 2, 0, 0, ()),
        CourseOptimization(2, (first_session, second_session), False, 4, 1, 1, ()),
    )
    first = SemesterOptimizationResult(courses, 6, 0, 1, 1, 0, 10)
    second = SemesterOptimizationResult(reordered, 6, 0, 1, 1, 0, 999)

    assert candidate_fingerprint(first, {1: 301, 2: 302}) == candidate_fingerprint(
        second, {1: 301, 2: 302}
    )
    assert candidate_fingerprint(first, {1: 301, 2: 999}) != candidate_fingerprint(
        first, {1: 301, 2: 302}
    )


def test_preparation_snapshot_tracks_working_revision_state_and_row_version():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    revision = db.get(ScheduleRevision, 1)
    original = prepare_optimization(db, 1, [1], [], schedule_revision_id=1)

    revision.row_version += 1
    db.commit()
    version_changed = prepare_optimization(db, 1, [1], [], schedule_revision_id=1)

    revision.state = "ready_for_review"
    revision.row_version += 1
    db.commit()
    state_changed = prepare_optimization(db, 1, [1], [], schedule_revision_id=1)

    assert original.shared_snapshot_token != version_changed.shared_snapshot_token
    assert version_changed.shared_snapshot_token != state_changed.shared_snapshot_token
    assert original.courses[0].input_snapshot_token != version_changed.courses[0].input_snapshot_token
    assert version_changed.courses[0].input_snapshot_token != state_changed.courses[0].input_snapshot_token
