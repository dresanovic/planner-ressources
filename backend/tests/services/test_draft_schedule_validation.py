from datetime import date, time

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.planning import Cohort, Course, Lecturer, Room, Semester, StudyType, StudyTypeTimeWindow
from app.services.draft_schedule_repository import (
    load_course_plan,
    load_generation_constraints,
    load_semester_plan,
    load_time_windows,
    replace_draft_schedule,
    save_generation_constraints,
)
from app.services.draft_schedule_validation import ValidationAlertCode, collect_validation_alerts
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


def seed_validation_courses(db):
    study_type = StudyType(id=1, name="Full-time")
    db.add_all(
        [
            Lecturer(id=1, name="Ada Lovelace"),
            Lecturer(id=2, name="Grace Hopper"),
            Cohort(id=1, name="AI 1", student_count=30),
            Cohort(id=2, name="AI 2", student_count=24),
            Room(id=1, name="R1", capacity=40),
            Room(id=2, name="R2", capacity=50),
            Room(id=3, name="Tiny", capacity=20),
            study_type,
            Semester(id=1, name="Fall", start_date=date(2026, 9, 7), end_date=date(2026, 12, 20)),
            StudyTypeTimeWindow(
                id=1,
                study_type_id=1,
                weekday=0,
                start_time=time(8, 0),
                end_time=time(12, 0),
                sort_order=1,
            ),
            StudyTypeTimeWindow(
                id=2,
                study_type_id=1,
                weekday=2,
                start_time=time(8, 0),
                end_time=time(12, 0),
                sort_order=2,
            ),
            Course(
                id=1,
                name="Planning 101",
                total_units=20,
                min_session_units=2,
                max_session_units=4,
                lecturer_id=1,
                cohort_id=1,
                room_id=1,
                study_type_id=1,
            ),
            Course(
                id=2,
                name="Scheduling 201",
                total_units=16,
                min_session_units=2,
                max_session_units=4,
                lecturer_id=1,
                cohort_id=2,
                room_id=2,
                study_type_id=1,
            ),
            Course(
                id=3,
                name="Studio 301",
                total_units=16,
                min_session_units=2,
                max_session_units=4,
                lecturer_id=2,
                cohort_id=1,
                room_id=1,
                study_type_id=1,
            ),
        ]
    )
    db.commit()


def replace_course_draft(db, course_id, sessions):
    return replace_draft_schedule(
        db,
        course_plan=load_course_plan(db, course_id),
        semester_id=1,
        generated_sessions=sessions,
    )


def generated_session(
    day=date(2026, 9, 7),
    start=time(8, 0),
    end=time(10, 0),
    *,
    window_id=1,
):
    return GeneratedSession(
        date=day,
        start_time=start,
        end_time=end,
        units=2,
        time_window_id=window_id,
        constraint_window_index=0,
    )


def validation_context(db, drafts):
    rooms_by_id = {room.id: room for room in db.execute(select(Room)).scalars().all()}
    semester_plan = load_semester_plan(db, 1)
    constraints = {
        draft.course_id: load_generation_constraints(db, load_course_plan(db, draft.course_id), semester_plan)
        for draft in drafts
    }
    windows = {1: load_time_windows(db, 1)}
    return {
        "rooms_by_id": rooms_by_id,
        "constraints_by_course_id": constraints,
        "study_windows_by_study_type_id": windows,
    }


def alert_codes(alerts_by_session, session_id):
    return {alert.code for alert in alerts_by_session[session_id]}


def test_overlap_alerts_apply_to_all_affected_sessions_with_related_context():
    db = make_session()
    seed_validation_courses(db)
    first = replace_course_draft(db, 1, [generated_session()])
    second = replace_course_draft(db, 2, [generated_session(start=time(9, 0), end=time(11, 0))])
    third = replace_course_draft(db, 3, [generated_session(start=time(9, 30), end=time(11, 30))])

    alerts = collect_validation_alerts([first, second, third], **validation_context(db, [first, second, third]))

    first_session = first.sessions[0]
    second_session = second.sessions[0]
    third_session = third.sessions[0]
    assert ValidationAlertCode.LECTURER_OVERLAP in alert_codes(alerts, first_session.id)
    assert ValidationAlertCode.ROOM_OVERLAP in alert_codes(alerts, first_session.id)
    assert ValidationAlertCode.COHORT_OVERLAP in alert_codes(alerts, first_session.id)
    lecturer_alert = next(alert for alert in alerts[first_session.id] if alert.code == ValidationAlertCode.LECTURER_OVERLAP)
    assert [related.course_name for related in lecturer_alert.related_sessions] == ["Scheduling 201"]
    cohort_alert = next(alert for alert in alerts[first_session.id] if alert.code == ValidationAlertCode.COHORT_OVERLAP)
    assert [related.session_id for related in cohort_alert.related_sessions] == [third_session.id]
    assert ValidationAlertCode.LECTURER_OVERLAP in alert_codes(alerts, second_session.id)
    assert ValidationAlertCode.COHORT_OVERLAP in alert_codes(alerts, third_session.id)


def test_back_to_back_sessions_and_single_session_do_not_create_overlap_alerts():
    db = make_session()
    seed_validation_courses(db)
    first = replace_course_draft(db, 1, [generated_session(start=time(8, 0), end=time(10, 0))])
    second = replace_course_draft(db, 2, [generated_session(start=time(10, 0), end=time(12, 0))])

    alerts = collect_validation_alerts([first, second], **validation_context(db, [first, second]))

    assert alert_codes(alerts, first.sessions[0].id) == set()
    assert alert_codes(alerts, second.sessions[0].id) == set()


def test_room_capacity_and_missing_reference_data_create_alerts():
    db = make_session()
    seed_validation_courses(db)
    draft = replace_course_draft(db, 1, [generated_session()])
    draft.sessions[0].room_id = 3
    db.commit()

    context = validation_context(db, [draft])
    alerts = collect_validation_alerts([draft], **context)
    assert ValidationAlertCode.ROOM_CAPACITY in alert_codes(alerts, draft.sessions[0].id)

    alerts_with_missing_room = collect_validation_alerts(
        [draft],
        rooms_by_id={},
        constraints_by_course_id=context["constraints_by_course_id"],
        study_windows_by_study_type_id=context["study_windows_by_study_type_id"],
    )
    assert ValidationAlertCode.VALIDATION_DATA_MISSING in alert_codes(alerts_with_missing_room, draft.sessions[0].id)


def test_current_generation_constraints_and_default_fallback_create_window_alerts():
    db = make_session()
    seed_validation_courses(db)
    course_plan = load_course_plan(db, 1)
    semester_plan = load_semester_plan(db, 1)
    save_generation_constraints(
        db,
        course_plan=course_plan,
        semester_plan=semester_plan,
        planning_period=PlanningPeriodPlan(date(2026, 9, 14), date(2026, 9, 28)),
        allowed_windows=[
            TimeWindowPlan(
                id=None,
                weekday=2,
                start_time=time(8, 0),
                end_time=time(12, 0),
                constraint_window_index=0,
            )
        ],
    )
    draft = replace_course_draft(db, 1, [generated_session(day=date(2026, 9, 7))])

    alerts = collect_validation_alerts([draft], **validation_context(db, [draft]))

    assert ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION in alert_codes(alerts, draft.sessions[0].id)


def test_custom_active_constraints_allow_friday_evening_without_study_type_alert():
    db = make_session()
    seed_validation_courses(db)
    course_plan = load_course_plan(db, 1)
    semester_plan = load_semester_plan(db, 1)
    save_generation_constraints(
        db,
        course_plan=course_plan,
        semester_plan=semester_plan,
        planning_period=PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20)),
        allowed_windows=[
            TimeWindowPlan(
                id=None,
                weekday=4,
                start_time=time(18, 0),
                end_time=time(22, 0),
                constraint_window_index=0,
            )
        ],
    )
    draft = replace_course_draft(
        db,
        1,
        [generated_session(day=date(2026, 9, 11), start=time(18, 0), end=time(21, 30), window_id=None)],
    )

    alerts = collect_validation_alerts([draft], **validation_context(db, [draft]))

    assert ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION not in alert_codes(alerts, draft.sessions[0].id)
    assert ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION not in alert_codes(alerts, draft.sessions[0].id)


def test_custom_active_constraints_report_only_generation_violation_when_session_is_outside_custom_window():
    db = make_session()
    seed_validation_courses(db)
    course_plan = load_course_plan(db, 1)
    semester_plan = load_semester_plan(db, 1)
    save_generation_constraints(
        db,
        course_plan=course_plan,
        semester_plan=semester_plan,
        planning_period=PlanningPeriodPlan(date(2026, 9, 7), date(2026, 12, 20)),
        allowed_windows=[
            TimeWindowPlan(
                id=None,
                weekday=4,
                start_time=time(18, 0),
                end_time=time(22, 0),
                constraint_window_index=0,
            )
        ],
    )
    draft = replace_course_draft(
        db,
        1,
        [generated_session(day=date(2026, 9, 11), start=time(17, 1), end=time(21, 30), window_id=None)],
    )

    alerts = collect_validation_alerts([draft], **validation_context(db, [draft]))

    assert ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION in alert_codes(alerts, draft.sessions[0].id)
    assert ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION not in alert_codes(alerts, draft.sessions[0].id)


def test_study_type_window_and_multiple_alerts_are_reported_together():
    db = make_session()
    seed_validation_courses(db)
    draft = replace_course_draft(
        db,
        1,
        [generated_session(day=date(2026, 9, 8), start=time(13, 0), end=time(15, 0), window_id=None)],
    )
    draft.sessions[0].room_id = 3
    db.commit()

    alerts = collect_validation_alerts([draft], **validation_context(db, [draft]))

    codes = alert_codes(alerts, draft.sessions[0].id)
    assert ValidationAlertCode.ROOM_CAPACITY in codes
    assert ValidationAlertCode.GENERATION_CONSTRAINT_VIOLATION in codes
    assert ValidationAlertCode.STUDY_TYPE_WINDOW_VIOLATION in codes


def test_regeneration_replacement_removes_prior_alerts():
    db = make_session()
    seed_validation_courses(db)
    first = replace_course_draft(db, 1, [generated_session()])
    second = replace_course_draft(db, 2, [generated_session(start=time(9, 0), end=time(11, 0))])
    initial = collect_validation_alerts([first, second], **validation_context(db, [first, second]))
    assert ValidationAlertCode.LECTURER_OVERLAP in alert_codes(initial, first.sessions[0].id)

    replaced = replace_course_draft(
        db,
        2,
        [generated_session(day=date(2026, 9, 14), start=time(9, 0), end=time(11, 0))],
    )
    refreshed = collect_validation_alerts([first, replaced], **validation_context(db, [first, replaced]))

    assert ValidationAlertCode.LECTURER_OVERLAP not in alert_codes(refreshed, first.sessions[0].id)
