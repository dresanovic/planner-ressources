from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import pytest

from app.db.schema import initialize_database
from app.models.planning import Course, DraftSchedule, DraftSession, ExamSession, Lecturer, Room, ScheduleRevision, Semester
from app.services.academic_catalog import usage_for
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

    with pytest.raises(LifecycleConflict) as exc_info:
        require_active_working_revision(db, 1, revision["revisionId"])
    assert exc_info.value.code == "revision_not_editable"


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
