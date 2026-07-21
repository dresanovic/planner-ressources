from time import perf_counter

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import ScheduleRevision, ScheduleRevisionEvent
from app.services.schedule_lifecycle import create_working_revision, get_lifecycle_overview, get_revision_content, prepare_publication, transition_revision
from tests.schedule_lifecycle_fixtures import FIXED_UTC, seed_lifecycle_semester


LIMIT_SECONDS = 2.0


def test_lifecycle_reference_operations_remain_bounded(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'lifecycle-performance.db'}")
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=True)
        initial = get_lifecycle_overview(db, 1)
        working = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        revision = working["activeWorkingRevision"]

        started = perf_counter()
        prepared = prepare_publication(db, revision["revisionId"], revision["revisionVersion"], working["stateToken"])
        assert perf_counter() - started < LIMIT_SECONDS
        started = perf_counter()
        published = transition_revision(db, revision["revisionId"], action="publish", expected_revision_version=revision["revisionVersion"], expected_state_token=working["stateToken"], confirmed=True, publication_token=prepared["preparationToken"])
        db.commit()
        assert perf_counter() - started < LIMIT_SECONDS
        started = perf_counter()
        successor = create_working_revision(db, 1, published["stateToken"])
        db.commit()
        assert perf_counter() - started < LIMIT_SECONDS
        started = perf_counter()
        assert get_revision_content(db, published["currentPublication"]["revisionId"])["contentSource"] == "captured_snapshot"
        assert perf_counter() - started < LIMIT_SECONDS

        active = db.get(ScheduleRevision, successor["activeWorkingRevision"]["revisionId"])
        active.state = "abandoned"
        active.snapshot_schema_version = 1
        active.snapshot_document = {"schemaVersion": 1}
        for number in range(3, 102):
            row = ScheduleRevision(semester_id=1, revision_number=number, state="abandoned", row_version=1, snapshot_schema_version=1, snapshot_document={"schemaVersion": 1}, created_at=FIXED_UTC, state_changed_at=FIXED_UTC, updated_at=FIXED_UTC)
            row.events.append(ScheduleRevisionEvent(semester_id=1, event_sequence=number + 1, event_type="abandoned", from_state="draft", to_state="abandoned", occurred_at=FIXED_UTC))
            db.add(row)
        db.commit()
        started = perf_counter()
        history = get_lifecycle_overview(db, 1)
        assert len(history["revisions"]) == 101
        assert perf_counter() - started < LIMIT_SECONDS
