from datetime import date, datetime, time

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.planning import CourseExamConfiguration, ExamSession, InstitutionHoliday
from app.services.exam_scheduling import (
    ExamSchedulingError,
    create_manual_exam,
    delete_exam,
    get_exam_planning_overview,
    prepare_exam_generation,
    save_exam_configuration,
    update_exam,
)
from tests.exam_fixtures import exam_catalog, teaching_draft


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all(exam_catalog())
    session.commit()
    yield session
    session.close()


def _input(**changes):
    value = dict(identifier=" Final exam ", duration_minutes=120, recommended_start_override=None, recommended_end_override=None, required_capacity=40, exam_type=" Written ", responsible_lecturer_id=1)
    value.update(changes)
    return value


def test_explicit_configuration_anchorless_then_default_recommendation(db):
    state, created = save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(), today=date(2026, 9, 1))
    assert created is True
    assert state["enabled"] is True
    assert state["configuration"]["identifier"] == "Final exam"
    assert state["configuration"]["recommendedStartDate"] is None
    assert state["generationEligibility"]["code"] == "FINAL_TEACHING_SESSION_MISSING"
    db.commit()
    db.add(teaching_draft())
    db.commit()
    state = get_exam_planning_overview(db, 1, today=date(2026, 9, 1))["courses"][0]
    assert state["configuration"]["recommendedStartDate"] == date(2026, 10, 9)
    assert state["configuration"]["recommendedEndDate"] == date(2026, 10, 16)
    assert state["generationEligibility"]["eligible"] is True


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"identifier": " "}, "identifier"),
        ({"duration_minutes": 0}, "durationMinutes"),
        ({"required_capacity": 0}, "requiredCapacity"),
        ({"exam_type": " "}, "examType"),
        ({"recommended_start_override": date(2026, 10, 10)}, "recommendedEndOverride"),
        ({"recommended_start_override": date(2026, 10, 12), "recommended_end_override": date(2026, 10, 10)}, "recommendedEndOverride"),
    ],
)
def test_configuration_validation_is_atomic(db, changes, field):
    with pytest.raises(ExamSchedulingError) as raised:
        save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(**changes), today=date(2026, 9, 1))
    assert field in {error.field for error in raised.value.errors}
    assert db.scalar(select(CourseExamConfiguration)) is None


def test_manual_override_active_guard_correction_and_exact_deletion(db):
    db.add(teaching_draft())
    db.commit()
    state, _ = save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(recommended_start_override=date(2026, 10, 20), recommended_end_override=date(2026, 10, 22)), today=date(2026, 9, 1))
    db.commit()
    exam_state = create_manual_exam(db, course_id=1, semester_id=1, exam_date=date(2026, 10, 5), start_time=time(13, 15), lecturer_id=1, room_id=1, expected_configuration_revision=1, input_snapshot_token=state["inputSnapshotToken"], today=date(2026, 9, 1))
    db.commit()
    exam = exam_state["activeExam"]
    assert exam["outsideRecommendedWindow"] is True
    assert exam["endTime"] == time(15, 15)
    with pytest.raises(ExamSchedulingError) as duplicate:
        create_manual_exam(db, course_id=1, semester_id=1, exam_date=date(2026, 10, 6), start_time=time(9), lecturer_id=1, room_id=1, expected_configuration_revision=2, input_snapshot_token=exam_state["inputSnapshotToken"], today=date(2026, 9, 1))
    assert duplicate.value.errors[0].code == "DUPLICATE_ACTIVE_EXAM"
    updated = update_exam(db, exam["id"], exam_date=date(2026, 10, 7), start_time=time(9), lecturer_id=1, room_id=1, expected_exam_revision=1, input_snapshot_token=exam["inputSnapshotToken"], today=date(2026, 9, 1))
    db.commit()
    assert updated["activeExam"]["revision"] == 2
    response = delete_exam(db, exam["id"], confirmed=True, expected_exam_revision=2, input_snapshot_token=updated["activeExam"]["inputSnapshotToken"], today=date(2026, 9, 1))
    db.commit()
    assert response["consequence"] == "configuration_enabled_unscheduled"
    assert db.scalar(select(ExamSession)) is None


def test_manual_hard_constraints_aggregate(db):
    db.add(teaching_draft())
    db.commit()
    state, _ = save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(required_capacity=100), today=date(2026, 9, 1))
    db.commit()
    with pytest.raises(ExamSchedulingError) as raised:
        create_manual_exam(db, course_id=1, semester_id=1, exam_date=date(2026, 10, 1), start_time=time(23), lecturer_id=1, room_id=1, expected_configuration_revision=1, input_snapshot_token=state["inputSnapshotToken"], today=date(2026, 9, 1))
    assert {item.code for item in raised.value.errors} >= {"BEFORE_FINAL_TEACHING", "INSUFFICIENT_ROOM_CAPACITY", "INVALID_EXAM_INTERVAL"}


def test_institution_clock_classifies_only_today_and_future_as_active(db):
    db.add(teaching_draft())
    db.commit()
    state, _ = save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(), today=date(2026, 9, 1))
    db.commit()
    create_manual_exam(db, course_id=1, semester_id=1, exam_date=date(2026, 10, 5), start_time=time(13), lecturer_id=1, room_id=1, expected_configuration_revision=1, input_snapshot_token=state["inputSnapshotToken"], today=date(2026, 9, 1))
    db.commit()
    overview = get_exam_planning_overview(db, 1, today=date(2026, 10, 6))
    assert overview["courses"][0]["activeExam"] is None
    assert len(overview["courses"][0]["pastExams"]) == 1


def test_authoritative_read_reports_new_hard_issue_without_repair_and_stales_old_token(db):
    db.add(teaching_draft())
    db.commit()
    state, _ = save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(), today=date(2026, 9, 1))
    db.commit()
    created = create_manual_exam(db, course_id=1, semester_id=1, exam_date=date(2026, 10, 5), start_time=time(13), lecturer_id=1, room_id=1, expected_configuration_revision=1, input_snapshot_token=state["inputSnapshotToken"], today=date(2026, 9, 1))
    db.commit()
    original = created["activeExam"]

    db.add(InstitutionHoliday(date=date(2026, 10, 5), name="New holiday", revision=1))
    db.commit()
    refreshed = get_exam_planning_overview(db, 1, today=date(2026, 9, 1))["courses"][0]["activeExam"]

    assert refreshed["id"] == original["id"]
    assert refreshed["date"] == original["date"]
    assert {issue["code"] for issue in refreshed["validityIssues"]} == {"INSTITUTION_HOLIDAY"}
    with pytest.raises(ExamSchedulingError) as raised:
        update_exam(db, original["id"], exam_date=date(2026, 10, 6), start_time=time(13), lecturer_id=1, room_id=1, expected_exam_revision=1, input_snapshot_token=original["inputSnapshotToken"], today=date(2026, 9, 1))
    assert raised.value.status_code == 409
    assert raised.value.errors[0].code == "STALE_INPUT_SNAPSHOT"


def test_preparation_token_is_bound_to_the_exact_selected_courses(db):
    second = exam_catalog(course_id=2, semester_id=2)
    second[-1].current_semester_id = 1
    db.add_all([second[0], second[1], second[2], second[4], second[5]])
    db.commit()

    first_selection = prepare_exam_generation(db, 1, [1], today=date(2026, 9, 1))
    second_selection = prepare_exam_generation(db, 1, [2], today=date(2026, 9, 1))

    assert first_selection["sharedSnapshotToken"] != second_selection["sharedSnapshotToken"]


def test_exam_retains_the_saved_final_teaching_session_identity(db):
    draft = teaching_draft()
    draft.sessions[0].id = 42
    db.add(draft)
    db.commit()
    state, _ = save_exam_configuration(db, course_id=1, semester_id=1, enabled=True, expected_revision=None, configuration=_input(), today=date(2026, 9, 1))
    db.commit()
    created = create_manual_exam(db, course_id=1, semester_id=1, exam_date=date(2026, 10, 5), start_time=time(13), lecturer_id=1, room_id=1, expected_configuration_revision=1, input_snapshot_token=state["inputSnapshotToken"], today=date(2026, 9, 1))
    db.commit()
    db.delete(draft)
    db.commit()

    overview = get_exam_planning_overview(db, 1, today=date(2026, 9, 1))

    assert created["activeExam"]["finalTeachingAnchor"]["teachingSessionId"] == 42
    assert overview["courses"][0]["activeExam"]["finalTeachingAnchor"]["teachingSessionId"] == 42
