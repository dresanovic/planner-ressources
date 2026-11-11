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
from tests.fixtures.dated_intensive_windows import ACCEPTANCE_WINDOW_CHANGES


def exact_candidate_fixture():
    from tests.optimization_fixtures import optimization_course
    course = optimization_course(1, total_units=4)
    session = GeneratedSession(date=date(2026, 9, 7), start_time=time(8), end_time=time(9, 40),
        units=2, time_window_id=1, constraint_window_index=0, lecturer_id=1, room_id=1)
    result = CourseOptimization(1, (session,), False, 2, 0, 0, ())
    return course, result


def test_exact_candidate_passes_without_inserting_provisional_records():
    course, candidate = exact_candidate_fixture()
    conflict_aware_service.validate_exact_candidate((course,), (), (), {}, (candidate,))


@pytest.mark.parametrize('mutation', [
    'outside_dates', 'wrong_weekday', 'too_short', 'too_long', 'bad_duration',
    'wrong_lecturer', 'wrong_room', 'wrong_window', 'wrong_window_index',
    'wrong_sum', 'duplicate_date', 'missing_course', 'duplicate_course',
    'holiday', 'unavailable_date', 'fixed_overlap', 'exam_boundary',
    'inactive_lecturer', 'inactive_room', 'lecturer_unavailable', 'room_unavailable',
    'insufficient_capacity', 'too_many_units',
])
def test_exact_candidate_rejects_each_hard_rule(mutation):
    from dataclasses import replace
    from datetime import datetime
    from tests.optimization_fixtures import fixed_session
    course, candidate = exact_candidate_fixture()
    session = candidate.sessions[0]
    fixed, unavailable, holidays = (), (), {}
    if mutation == 'outside_dates': session = replace(session, date=date(2025, 9, 1))
    if mutation == 'wrong_weekday': session = replace(session, date=date(2026, 9, 8))
    if mutation == 'too_short': session = replace(session, units=1, end_time=time(8, 45))
    if mutation == 'too_long': session = replace(session, units=5)
    if mutation == 'bad_duration': session = replace(session, end_time=time(10))
    if mutation == 'wrong_lecturer': session = replace(session, lecturer_id=99)
    if mutation == 'wrong_room': session = replace(session, room_id=99)
    if mutation == 'wrong_window': session = replace(session, time_window_id=99)
    if mutation == 'wrong_window_index': session = replace(session, constraint_window_index=99)
    if mutation == 'exam_boundary': course = replace(course, latest_teaching_end=datetime(2026,9,7,9))
    if mutation == 'inactive_lecturer': course = replace(course, lecturers=(replace(course.lecturers[0], active=False),))
    if mutation == 'inactive_room': course = replace(course, rooms=(replace(course.rooms[0], active=False),))
    if mutation in ('lecturer_unavailable', 'room_unavailable'):
        period = ResourceUnavailabilityPeriod(kind='recurring', start_time=time(8), end_time=time(12),
            weekdays=[ResourceUnavailabilityWeekday(weekday=0)])
        if mutation == 'lecturer_unavailable': course = replace(course, lecturers=(replace(course.lecturers[0], unavailable_periods=(period,)),))
        else: course = replace(course, rooms=(replace(course.rooms[0], unavailable_periods=(period,)),))
    if mutation == 'insufficient_capacity': course = replace(course, rooms=(replace(course.rooms[0], capacity=1),))
    if mutation == 'too_many_units': course = replace(course, total_units=1)
    if mutation == 'holiday': holidays = {session.date: object()}
    if mutation == 'unavailable_date': unavailable = (session.date,)
    if mutation == 'fixed_overlap': fixed = (fixed_session(lecturer_id=1),)
    candidate = replace(candidate, sessions=(session,))
    if mutation == 'wrong_sum': candidate = replace(candidate, scheduled_units=3)
    if mutation == 'duplicate_date': candidate = replace(candidate, sessions=(session, session), scheduled_units=4)
    candidates = (candidate,)
    if mutation == 'missing_course': candidates = ()
    if mutation == 'duplicate_course': candidates = (candidate, candidate)
    with pytest.raises(conflict_aware_service.InvalidExactCandidate):
        conflict_aware_service.validate_exact_candidate((course,), fixed, unavailable, holidays, candidates)


@pytest.mark.parametrize('shared', ['lecturer', 'room', 'cohort'])
def test_exact_candidate_rejects_joint_selected_course_resource_collisions(shared):
    from dataclasses import replace
    from tests.optimization_fixtures import optimization_course
    first, candidate = exact_candidate_fixture()
    second = optimization_course(2, lecturer_ids=(1,) if shared == 'lecturer' else (2,),
        room_ids=(1,) if shared == 'room' else (2,), cohort_id=1 if shared == 'cohort' else 2)
    session = replace(candidate.sessions[0], lecturer_id=second.lecturers[0].id, room_id=second.rooms[0].id)
    other = replace(candidate, course_id=2, sessions=(session,))
    with pytest.raises(conflict_aware_service.InvalidExactCandidate):
        conflict_aware_service.validate_exact_candidate((first, second), (), (), {}, (candidate, other))


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


def test_preference_is_captured_and_invalidates_prepared_course_identity():
    db = make_session()
    seed_optimization_planner(db, course_count=1)
    first = prepare_optimization(db, 1, [1], [])
    db.get(Course, 1).preferred_session_units = 3
    db.commit()
    second = prepare_optimization(db, 1, [1], [])
    assert first.courses[0].input_snapshot_token != second.courses[0].input_snapshot_token
    loaded = load_operation(db, 1, [1], [])
    assert loaded.courses[0].optimization.preferred_session_units == 3


def test_preparation_tokens_are_bound_to_the_schedule_revision():
    db = make_session()
    seed_optimization_planner(db, course_count=1)

    first = prepare_optimization(db, 1, [1], [], schedule_revision_id=11)
    second = prepare_optimization(db, 1, [1], [], schedule_revision_id=12)

    assert first.shared_snapshot_token != second.shared_snapshot_token
    assert first.courses[0].input_snapshot_token != second.courses[0].input_snapshot_token


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
