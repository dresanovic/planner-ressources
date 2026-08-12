from copy import deepcopy
from datetime import time, timedelta
from uuid import UUID

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import pytest

from app.db.schema import initialize_database
from app.models.planning import Course, CourseExamConfiguration, DraftSchedule, DraftSession, ExamSession, GenerationConstraintSet, GenerationConstraintWindow, Lecturer, LecturerReviewActivityEvent, LecturerReviewFeedback, LecturerReviewLink, Room, ScheduleRevision, Semester, StudyType, StudyTypeTimeWindow
from app.schemas.lecturer_review import FeedbackInput
from app.services.academic_catalog import usage_for
from app.services.lecturer_review import (
    get_lecturer_review_overview,
    issue_lecturer_review_link,
    submit_lecturer_review_feedback,
)
from app.services.resource_catalog import assess_resource_usage
from app.services.schedule_lifecycle import (
    LifecycleConflict,
    create_working_revision,
    get_lifecycle_overview,
    get_revision_content,
    prepare_publication,
    require_active_working_revision,
    transition_revision,
)
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester
from tests.lecturer_review_fixtures import DeterministicUtcClock, FIXED_UTC


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    initialize_database(engine)
    with Session(engine) as session:
        yield session


def test_explicit_initial_draft_establishment_accepts_empty_and_populated_semesters(db):
    populated, _course = seed_lifecycle_semester(db, semester_id=1, with_schedule=True)
    empty = Semester(
        id=2,
        name="Empty Semester",
        start_date=populated.start_date,
        end_date=populated.end_date,
    )
    db.add(empty)
    db.commit()

    for semester_id in (1, 2):
        before = get_lifecycle_overview(db, semester_id)
        assert before["activeWorkingRevision"] is None
        assert before["allowedActions"]["createWorkingRevision"] is True
        created = create_working_revision(db, semester_id, before["stateToken"])
        db.commit()
        assert created["activeWorkingRevision"]["state"] == "draft"
        assert created["activeWorkingRevision"]["revisionNumber"] == 1
        assert created["activeWorkingRevision"]["events"][0]["eventType"] == "created"


def test_direct_first_publication_captures_stable_snapshot_and_nonblocking_conditions(db):
    seed_lifecycle_semester(db, with_schedule=True)
    db.get(Room, 1).capacity = 1
    exam = db.scalar(select(ExamSession))
    exam.exam_date = exam.recommended_start_date - timedelta(days=1)
    db.commit()
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]

    preparation = prepare_publication(
        db,
        revision["revisionId"],
        revision["revisionVersion"],
        created["stateToken"],
    )
    assert preparation["consequence"] == "first_publication"
    assert preparation["remainingUnits"] == 2
    assert {item["code"] for item in preparation["conditions"]} >= {
        "course_units_remaining",
        "teaching_validation_alert",
        "exam_validity_issue",
    }
    remaining = next(item for item in preparation["conditions"] if item["code"] == "course_units_remaining")
    assert remaining["details"]["courseName"] == "Course 1"
    teaching = next(item for item in preparation["conditions"] if item["code"] == "teaching_validation_alert")
    assert teaching["details"]["courseName"] == "Course 1"
    assert teaching["details"]["sessionDate"] == "2026-10-05"
    validity = next(item for item in preparation["conditions"] if item["code"] == "exam_validity_issue")
    assert validity["details"]["courseName"] == "Course 1"
    assert validity["details"]["examDate"] == exam.exam_date.isoformat()
    outside = next(item for item in preparation["conditions"] if item["code"] == "exam_outside_recommendation")
    assert outside["details"] == {
        "courseName": "Course 1",
        "examDate": exam.exam_date.isoformat(),
        "recommendedStartDate": exam.recommended_start_date.isoformat(),
        "recommendedEndDate": exam.recommended_end_date.isoformat(),
    }

    published = transition_revision(
        db,
        revision["revisionId"],
        action="publish",
        expected_revision_version=revision["revisionVersion"],
        expected_state_token=created["stateToken"],
        confirmed=True,
        publication_token=preparation["preparationToken"],
    )
    db.commit()
    current = published["currentPublication"]
    assert current["revisionId"] == revision["revisionId"]
    assert current["state"] == "published"
    assert current["publishedAt"].endswith("Z")
    assert published["activeWorkingRevision"] is None

    db.get(Course, 1).name = "Renamed current course"
    db.commit()
    content = get_revision_content(db, revision["revisionId"])
    assert content["contentSource"] == "captured_snapshot"
    assert content["snapshot"]["courses"][0]["name"] == "Course 1"
    assert content["snapshot"]["examSessions"][0]["configurationIdentifier"] == "FINAL"
    assert content["snapshot"]["courses"][0]["teachingSessions"][0]["validationAlerts"]
    assert content["snapshot"]["examSessions"][0]["validityIssues"]
    assert content["snapshot"]["schemaVersion"] == 2
    assert content["snapshot"]["courses"][0]["constraintProfile"] == {
        "isCustom": False,
        "sourceRevision": None,
        "planningStartDate": "2026-09-01",
        "planningEndDate": "2026-12-20",
        "allowedTeachingWindows": [],
    }

    legacy_snapshot = deepcopy(content["snapshot"])
    legacy_snapshot["schemaVersion"] = 1
    for course in legacy_snapshot["courses"]:
        course.pop("constraintProfile", None)
    stored_revision = db.get(ScheduleRevision, revision["revisionId"])
    stored_revision.snapshot_schema_version = 1
    stored_revision.snapshot_document = legacy_snapshot
    db.commit()

    legacy_content = get_revision_content(db, revision["revisionId"])
    assert legacy_content["contentSource"] == "captured_snapshot"
    assert legacy_content["snapshot"] == legacy_snapshot
    assert "constraintProfile" not in legacy_content["snapshot"]["courses"][0]

    with pytest.raises(LifecycleConflict) as exc_info:
        require_active_working_revision(db, 1, revision["revisionId"])
    assert exc_info.value.code == "revision_not_editable"


def test_publication_condition_for_enabled_unscheduled_exam_contains_course_context(db):
    seed_lifecycle_semester(db, with_schedule=False)
    db.add(
        CourseExamConfiguration(
            course_id=1,
            semester_id=1,
            enabled=True,
            identifier="FINAL",
            duration_minutes=90,
            required_capacity=30,
            exam_type="Written",
            responsible_lecturer_id=1,
        )
    )
    db.commit()
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]

    preparation = prepare_publication(
        db,
        revision["revisionId"],
        revision["revisionVersion"],
        created["stateToken"],
    )

    condition = next(item for item in preparation["conditions"] if item["code"] == "enabled_exam_unscheduled")
    assert condition["details"]["courseName"] == "Course 1"


def test_publication_uses_current_study_type_for_default_generation_constraints(db):
    semester, _course = seed_lifecycle_semester(db, with_schedule=True)
    db.add_all([
        StudyTypeTimeWindow(
            study_type_id=1,
            weekday=0,
            start_time=time(9),
            end_time=time(11),
            sort_order=0,
        ),
        StudyType(id=2, name="Current study type"),
    ])
    db.flush()
    current_window = StudyTypeTimeWindow(
        study_type_id=2,
        weekday=1,
        start_time=time(9),
        end_time=time(11),
        sort_order=0,
    )
    db.add(current_window)
    db.flush()
    db.get(Course, 1).study_type_id = 2
    db.add(
        GenerationConstraintSet(
            course_id=1,
            semester_id=1,
            planning_start_date=semester.start_date,
            planning_end_date=semester.end_date,
            windows=[
                GenerationConstraintWindow(
                    weekday=0,
                    start_time=time(9),
                    end_time=time(11),
                    sort_order=0,
                )
            ],
        )
    )
    db.commit()
    original_session = db.scalar(select(DraftSession).where(DraftSession.course_id == 1))
    original_interval = (original_session.date, original_session.start_time, original_session.end_time)
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]

    preparation = prepare_publication(
        db,
        revision["revisionId"],
        revision["revisionVersion"],
        created["stateToken"],
    )

    alert_codes = {
        condition["details"].get("alertCode")
        for condition in preparation["conditions"]
        if condition["code"] == "teaching_validation_alert"
    }
    assert "GENERATION_CONSTRAINT_VIOLATION" not in alert_codes
    assert "STUDY_TYPE_WINDOW_VIOLATION" in alert_codes
    db.refresh(original_session)
    assert (original_session.date, original_session.start_time, original_session.end_time) == original_interval

    published = transition_revision(
        db,
        revision["revisionId"],
        action="publish",
        expected_revision_version=revision["revisionVersion"],
        expected_state_token=created["stateToken"],
        confirmed=True,
        publication_token=preparation["preparationToken"],
    )
    db.commit()
    content = get_revision_content(db, published["currentPublication"]["revisionId"])
    constraint_profile = content["snapshot"]["courses"][0]["constraintProfile"]
    assert constraint_profile["isCustom"] is True
    assert constraint_profile["allowedTeachingWindows"] == [
        {
            "sourceTimeWindowId": current_window.id,
            "weekday": 1,
            "startTime": "09:00:00",
            "endTime": "11:00:00",
            "sortOrder": 0,
        }
    ]


def test_stale_and_repeated_first_publication_write_no_duplicate_events(db):
    seed_lifecycle_semester(db, with_schedule=False)
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]
    preparation = prepare_publication(
        db, revision["revisionId"], revision["revisionVersion"], created["stateToken"]
    )
    transition_revision(
        db,
        revision["revisionId"],
        action="publish",
        expected_revision_version=revision["revisionVersion"],
        expected_state_token=created["stateToken"],
        confirmed=True,
        publication_token=preparation["preparationToken"],
    )
    db.commit()

    with pytest.raises(LifecycleConflict) as exc_info:
        transition_revision(
            db,
            revision["revisionId"],
            action="publish",
            expected_revision_version=revision["revisionVersion"],
            expected_state_token=created["stateToken"],
            confirmed=True,
            publication_token=preparation["preparationToken"],
        )
    assert exc_info.value.code in {"stale_lifecycle_state", "revision_not_editable"}
    db.rollback()
    stored = db.get(ScheduleRevision, revision["revisionId"])
    assert [event.event_type for event in stored.events] == ["created", "published"]


def _publish_initial(db):
    overview = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, overview["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]
    prepared = prepare_publication(db, revision["revisionId"], revision["revisionVersion"], created["stateToken"])
    published = transition_revision(db, revision["revisionId"], action="publish", expected_revision_version=revision["revisionVersion"], expected_state_token=created["stateToken"], confirmed=True, publication_token=prepared["preparationToken"])
    db.commit()
    return published


def test_successor_keeps_current_visible_until_atomic_replacement(db):
    seed_lifecycle_semester(db, with_schedule=True)
    first = _publish_initial(db)
    successor_overview = create_working_revision(db, 1, first["stateToken"])
    db.commit()
    successor = successor_overview["activeWorkingRevision"]
    assert successor["revisionNumber"] == 2
    assert successor["originRevisionId"] == first["currentPublication"]["revisionId"]
    assert successor_overview["currentPublication"]["revisionId"] == first["currentPublication"]["revisionId"]

    prepared = prepare_publication(db, successor["revisionId"], successor["revisionVersion"], successor_overview["stateToken"])
    replaced = transition_revision(db, successor["revisionId"], action="publish", expected_revision_version=successor["revisionVersion"], expected_state_token=successor_overview["stateToken"], confirmed=True, publication_token=prepared["preparationToken"])
    db.commit()
    assert replaced["currentPublication"]["revisionId"] == successor["revisionId"]
    history = {item["revisionNumber"]: item for item in replaced["revisions"]}
    assert history[1]["state"] == "superseded"
    sequences = [event["eventSequence"] for item in replaced["revisions"] for event in item["events"]]
    assert sorted(sequences) == list(range(1, len(sequences) + 1))


def test_ready_is_informative_editable_and_publishable(db):
    seed_lifecycle_semester(db, with_schedule=True)
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]
    ready = transition_revision(db, revision["revisionId"], action="mark_ready", expected_revision_version=revision["revisionVersion"], expected_state_token=created["stateToken"], confirmed=False)
    db.commit()
    ready_revision = ready["activeWorkingRevision"]
    assert ready_revision["state"] == "ready_for_review"
    assert require_active_working_revision(db, 1, revision["revisionId"]).id == revision["revisionId"]
    draft = transition_revision(db, revision["revisionId"], action="return_to_draft", expected_revision_version=ready_revision["revisionVersion"], expected_state_token=ready["stateToken"], confirmed=False)
    db.commit()
    assert draft["activeWorkingRevision"]["state"] == "draft"


def test_abandon_preserves_publication_and_restore_reuses_identity_and_content(db):
    seed_lifecycle_semester(db, with_schedule=True)
    first = _publish_initial(db)
    successor_overview = create_working_revision(db, 1, first["stateToken"])
    db.commit()
    successor = successor_overview["activeWorkingRevision"]
    db.get(Course, 1).name = "Working name"
    abandoned = transition_revision(db, successor["revisionId"], action="abandon", expected_revision_version=successor["revisionVersion"], expected_state_token=successor_overview["stateToken"], confirmed=True)
    db.commit()
    assert abandoned["currentPublication"]["revisionId"] == first["currentPublication"]["revisionId"]
    abandoned_revision = next(item for item in abandoned["revisions"] if item["revisionId"] == successor["revisionId"])
    restored = transition_revision(db, successor["revisionId"], action="restore", expected_revision_version=abandoned_revision["revisionVersion"], expected_state_token=abandoned["stateToken"], confirmed=True)
    db.commit()
    assert restored["activeWorkingRevision"]["revisionId"] == successor["revisionId"]
    assert restored["currentPublication"]["revisionId"] == first["currentPublication"]["revisionId"]
    assert get_revision_content(db, successor["revisionId"])["snapshot"]["courses"][0]["name"] == "Working name"


def test_review_link_survives_first_publication_but_abandon_restore_never_reactivates(db):
    seed_lifecycle_semester(db, with_schedule=True)
    clock = DeterministicUtcClock()
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    first_revision = created["activeWorkingRevision"]
    first_issued = issue_lecturer_review_link(
        db,
        first_revision["revisionId"],
        1,
        clock=clock,
    )
    db.commit()

    first_preparation = prepare_publication(
        db,
        first_revision["revisionId"],
        first_revision["revisionVersion"],
        created["stateToken"],
    )
    published = transition_revision(
        db,
        first_revision["revisionId"],
        action="publish",
        expected_revision_version=first_revision["revisionVersion"],
        expected_state_token=created["stateToken"],
        confirmed=True,
        publication_token=first_preparation["preparationToken"],
    )
    db.commit()
    db.expire_all()
    first_link = db.get(LecturerReviewLink, first_issued.issued_link.id)
    assert first_link.status == "active"
    assert first_link.ended_at is None
    assert first_link.end_reason is None

    successor_overview = create_working_revision(db, 1, published["stateToken"])
    db.commit()
    successor = successor_overview["activeWorkingRevision"]
    successor_issued = issue_lecturer_review_link(
        db,
        successor["revisionId"],
        1,
        clock=clock,
    )
    db.commit()

    abandoned = transition_revision(
        db,
        successor["revisionId"],
        action="abandon",
        expected_revision_version=successor["revisionVersion"],
        expected_state_token=successor_overview["stateToken"],
        confirmed=True,
    )
    db.commit()
    db.expire_all()
    successor_link = db.get(LecturerReviewLink, successor_issued.issued_link.id)
    assert successor_link.status == "revision_ended"
    assert successor_link.ended_at is not None
    assert successor_link.end_reason == "abandoned"
    assert db.scalar(
        select(LecturerReviewActivityEvent).where(
            LecturerReviewActivityEvent.review_link_id == successor_link.id,
            LecturerReviewActivityEvent.event_type == "revision_ended",
            LecturerReviewActivityEvent.reason_code == "abandoned",
        )
    ) is not None

    abandoned_revision = next(
        item
        for item in abandoned["revisions"]
        if item["revisionId"] == successor["revisionId"]
    )
    transition_revision(
        db,
        successor["revisionId"],
        action="restore",
        expected_revision_version=abandoned_revision["revisionVersion"],
        expected_state_token=abandoned["stateToken"],
        confirmed=True,
    )
    db.commit()
    db.expire_all()
    restored_link = db.get(LecturerReviewLink, successor_issued.issued_link.id)
    assert restored_link.status == "revision_ended"
    assert restored_link.end_reason == "abandoned"
    terminal_events = db.scalars(
        select(LecturerReviewActivityEvent).where(
            LecturerReviewActivityEvent.review_link_id == restored_link.id,
            LecturerReviewActivityEvent.event_type == "revision_ended",
        )
    ).all()
    assert len(terminal_events) == 1


def test_passed_review_deadline_without_feedback_does_not_gate_publication(db):
    seed_lifecycle_semester(db, with_schedule=True)
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    revision = created["activeWorkingRevision"]
    issued = issue_lecturer_review_link(
        db,
        revision["revisionId"],
        1,
        duration_days=1,
        clock=DeterministicUtcClock(FIXED_UTC - timedelta(days=2)),
    )
    db.commit()

    review = get_lecturer_review_overview(
        db,
        revision["revisionId"],
        clock=DeterministicUtcClock(FIXED_UTC),
    )
    db.commit()
    assert review.total_feedback_count == 0
    assert review.impossible_flag_count == 0
    assert review.links[0].status == "expired"
    assert db.query(LecturerReviewFeedback).count() == 0

    prepared = prepare_publication(
        db,
        revision["revisionId"],
        revision["revisionVersion"],
        created["stateToken"],
    )
    published = transition_revision(
        db,
        revision["revisionId"],
        action="publish",
        expected_revision_version=revision["revisionVersion"],
        expected_state_token=created["stateToken"],
        confirmed=True,
        publication_token=prepared["preparationToken"],
    )
    db.commit()

    assert issued.issued_link.id == review.links[0].id
    assert published["currentPublication"]["revisionId"] == revision["revisionId"]
    assert published["currentPublication"]["state"] == "published"
    assert db.query(LecturerReviewFeedback).count() == 0


def test_comments_and_flags_survive_publish_abandon_restore_and_supersession(db):
    seed_lifecycle_semester(db, with_schedule=True)
    initial = get_lifecycle_overview(db, 1)
    created = create_working_revision(db, 1, initial["stateToken"])
    db.commit()
    first = created["activeWorkingRevision"]
    teaching_id = db.scalar(select(DraftSession.id))
    assert teaching_id is not None
    first_issued = issue_lecturer_review_link(
        db,
        first["revisionId"],
        1,
        clock=DeterministicUtcClock(),
    )
    db.commit()
    submit_lecturer_review_feedback(
        db,
        first_issued.secret,
        FeedbackInput(
            client_submission_id=UUID(int=1001),
            kind="revision_comment",
            comment="Publication remains the planner's decision.",
        ),
        clock=DeterministicUtcClock(),
    )
    submit_lecturer_review_feedback(
        db,
        first_issued.secret,
        FeedbackInput(
            client_submission_id=UUID(int=1002),
            kind="impossible_session",
            session_ref=f"teaching:{teaching_id}",
            comment="This time is not possible.",
        ),
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(seconds=1)),
    )
    db.commit()
    first_feedback = _review_feedback_signatures(db)

    first_prepared = prepare_publication(
        db,
        first["revisionId"],
        first["revisionVersion"],
        created["stateToken"],
    )
    published = transition_revision(
        db,
        first["revisionId"],
        action="publish",
        expected_revision_version=first["revisionVersion"],
        expected_state_token=created["stateToken"],
        confirmed=True,
        publication_token=first_prepared["preparationToken"],
    )
    db.commit()
    assert _review_feedback_signatures(db) == first_feedback

    successor_overview = create_working_revision(db, 1, published["stateToken"])
    db.commit()
    successor = successor_overview["activeWorkingRevision"]
    successor_issued = issue_lecturer_review_link(
        db,
        successor["revisionId"],
        1,
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=1)),
    )
    db.commit()
    submit_lecturer_review_feedback(
        db,
        successor_issued.secret,
        FeedbackInput(
            client_submission_id=UUID(int=1003),
            kind="revision_comment",
            comment="The successor still needs planner review.",
        ),
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=1)),
    )
    submit_lecturer_review_feedback(
        db,
        successor_issued.secret,
        FeedbackInput(
            client_submission_id=UUID(int=1004),
            kind="impossible_session",
            session_ref=f"teaching:{teaching_id}",
        ),
        clock=DeterministicUtcClock(FIXED_UTC + timedelta(minutes=1, seconds=1)),
    )
    db.commit()
    all_feedback = _review_feedback_signatures(db)

    abandoned = transition_revision(
        db,
        successor["revisionId"],
        action="abandon",
        expected_revision_version=successor["revisionVersion"],
        expected_state_token=successor_overview["stateToken"],
        confirmed=True,
    )
    db.commit()
    assert _review_feedback_signatures(db) == all_feedback
    abandoned_revision = next(
        item
        for item in abandoned["revisions"]
        if item["revisionId"] == successor["revisionId"]
    )
    restored = transition_revision(
        db,
        successor["revisionId"],
        action="restore",
        expected_revision_version=abandoned_revision["revisionVersion"],
        expected_state_token=abandoned["stateToken"],
        confirmed=True,
    )
    db.commit()
    assert _review_feedback_signatures(db) == all_feedback

    restored_revision = restored["activeWorkingRevision"]
    successor_prepared = prepare_publication(
        db,
        successor["revisionId"],
        restored_revision["revisionVersion"],
        restored["stateToken"],
    )
    replaced = transition_revision(
        db,
        successor["revisionId"],
        action="publish",
        expected_revision_version=restored_revision["revisionVersion"],
        expected_state_token=restored["stateToken"],
        confirmed=True,
        publication_token=successor_prepared["preparationToken"],
    )
    db.commit()

    assert replaced["currentPublication"]["revisionId"] == successor["revisionId"]
    assert next(
        item
        for item in replaced["revisions"]
        if item["revisionId"] == first["revisionId"]
    )["state"] == "superseded"
    assert _review_feedback_signatures(db) == all_feedback
    assert {
        link.id: (link.status, link.end_reason)
        for link in db.scalars(select(LecturerReviewLink))
    } == {
        first_issued.issued_link.id: ("revision_ended", "superseded"),
        successor_issued.issued_link.id: ("revision_ended", "abandoned"),
    }
    first_review = get_lecturer_review_overview(db, first["revisionId"])
    successor_review = get_lecturer_review_overview(db, successor["revisionId"])
    # Feedback on a superseded revision remains available as history, but its
    # impossible-session marker is no longer an actionable notification.
    assert (
        first_review.total_feedback_count,
        first_review.impossible_flag_count,
    ) == (2, 0)
    first_session_group = next(
        group for group in first_review.feedback_groups if group.level == "session"
    )
    assert first_session_group.items[0].session_status == "unavailable"
    assert (
        successor_review.total_feedback_count,
        successor_review.impossible_flag_count,
    ) == (2, 1)


def test_inactive_snapshot_references_protect_catalog_and_resource_identity(db):
    _semester, course = seed_lifecycle_semester(db, with_schedule=True)
    _publish_initial(db)
    db.execute(delete(ExamSession).where(ExamSession.semester_id == 1))
    db.execute(delete(DraftSession))
    db.execute(delete(DraftSchedule).where(DraftSchedule.semester_id == 1))
    course.is_active = False
    db.commit()
    assert usage_for(db, course)["canDelete"] is False
    lecturer_usage = assess_resource_usage(db, db.get(Lecturer, 1))
    assert lecturer_usage["disposition"] == "inactivate"
    assert lecturer_usage["sessionUsage"]["draftSessionCount"] > 0
    assert lecturer_usage["examUsage"]["examSessionCount"] > 0


def _review_feedback_signatures(db: Session) -> list[tuple]:
    return [
        (
            item.id,
            item.review_link_id,
            item.kind,
            item.session_kind,
            item.source_session_id,
            item.comment_text,
            item.session_context,
            item.client_submission_id,
            item.request_fingerprint,
            item.submitted_at,
        )
        for item in db.scalars(
            select(LecturerReviewFeedback).order_by(LecturerReviewFeedback.id)
        )
    ]
