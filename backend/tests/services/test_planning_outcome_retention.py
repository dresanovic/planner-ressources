from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.models.planning import Cohort, Course, PlanningOutcome, ScheduleRevision, Semester, StudyType
from app.services.planning_outcomes import (
    StalePlanningOutcomeError,
    list_planning_outcomes,
    retain_planning_outcome,
)


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    with Session(engine) as db:
        db.add_all(
            [
                Cohort(id=1, name="Cohort", student_count=20),
                StudyType(id=1, name="Full-time"),
                Semester(
                    id=1,
                    name="Fall",
                    start_date=date(2026, 9, 1),
                    end_date=date(2026, 12, 20),
                ),
                Course(
                    id=1,
                    name="Course",
                    total_units=4,
                    min_session_units=2,
                    max_session_units=2,
                    cohort_id=1,
                    study_type_id=1,
                    current_semester_id=1,
                ),
                ScheduleRevision(
                    id=1,
                    semester_id=1,
                    revision_number=1,
                    row_version=1,
                    state="draft",
                ),
            ]
        )
        db.commit()
        yield db


def test_insert_reload_and_newer_same_key_upsert(db_session):
    completed_at = datetime(2026, 9, 1, 8, tzinfo=timezone.utc)
    first = retain_planning_outcome(
        db_session,
        schedule_revision_id=1,
        course_id=1,
        operation_kind="single_course_generation",
        classification="failed",
        source_status="no_feasible_slot",
        result_payload={"reason": "room"},
        completed_at=completed_at,
    )
    db_session.commit()
    first_id = first.id
    db_session.expire_all()

    retained = list_planning_outcomes(db_session, 1)
    assert [(row.id, row.classification) for row in retained] == [(first_id, "failed")]

    updated = retain_planning_outcome(
        db_session,
        schedule_revision_id=1,
        course_id=1,
        operation_kind="single_course_generation",
        classification="successful",
        source_status="generated",
        result_payload={"scheduledUnits": 4},
        completed_at=completed_at + timedelta(minutes=1),
    )
    db_session.commit()

    assert updated.id == first_id
    assert updated.classification == "successful"
    assert updated.result_payload == {"scheduledUnits": 4}
    assert db_session.scalar(select(PlanningOutcome).where(PlanningOutcome.id == first_id)) is updated


def test_cross_kind_isolation_and_older_completion_does_not_supersede(db_session):
    newest = datetime(2026, 9, 1, 9, tzinfo=timezone.utc)
    retain_planning_outcome(
        db_session,
        schedule_revision_id=1,
        course_id=1,
        operation_kind="single_course_generation",
        classification="successful",
        source_status="generated",
        result_payload={"version": 2},
        completed_at=newest,
    )
    retained = retain_planning_outcome(
        db_session,
        schedule_revision_id=1,
        course_id=1,
        operation_kind="single_course_generation",
        classification="failed",
        source_status="late_response",
        result_payload={"version": 1},
        completed_at=newest - timedelta(minutes=1),
    )
    retain_planning_outcome(
        db_session,
        schedule_revision_id=1,
        course_id=1,
        operation_kind="exam_generation",
        classification="unchanged",
        source_status="unchanged",
        result_payload={},
        completed_at=newest,
    )
    db_session.commit()

    assert retained.classification == "successful"
    assert retained.result_payload == {"version": 2}
    assert {row.operation_kind for row in list_planning_outcomes(db_session, 1)} == {
        "single_course_generation",
        "exam_generation",
    }


def test_stale_revision_rejected_and_successor_does_not_inherit(db_session):
    completed_at = datetime(2026, 9, 1, 9, tzinfo=timezone.utc)
    retain_planning_outcome(
        db_session,
        schedule_revision_id=1,
        course_id=1,
        operation_kind="semester_optimization",
        classification="failed",
        source_status="failed",
        result_payload={},
        completed_at=completed_at,
    )
    revision = db_session.get(ScheduleRevision, 1)
    revision.state = "abandoned"
    revision.snapshot_schema_version = 1
    revision.snapshot_document = {
        "schemaVersion": 1,
        "capturedAt": completed_at.isoformat(),
        "semester": {},
        "courses": [],
        "examSessions": [],
        "capturedConditions": [],
    }
    successor = ScheduleRevision(
        id=2,
        semester_id=1,
        revision_number=2,
        row_version=1,
        state="draft",
        origin_revision_id=1,
    )
    db_session.add(successor)
    db_session.commit()

    with pytest.raises(StalePlanningOutcomeError):
        retain_planning_outcome(
            db_session,
            schedule_revision_id=1,
            course_id=1,
            operation_kind="semester_optimization",
            classification="successful",
            source_status="generated",
            result_payload={},
            completed_at=completed_at + timedelta(minutes=1),
        )
    assert list_planning_outcomes(db_session, 2) == []
