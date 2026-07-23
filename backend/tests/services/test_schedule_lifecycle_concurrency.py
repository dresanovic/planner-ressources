from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import ScheduleRevision, ScheduleRevisionEvent, Semester
from app.services.schedule_lifecycle import (
    LifecycleConflict,
    claim_active_working_revision,
    create_working_revision,
    get_lifecycle_overview,
    prepare_publication,
    transition_revision,
)
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester


def test_competing_first_draft_creation_retains_one_working_revision(tmp_path: Path):
    database = tmp_path / "lifecycle-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        db.add(
            Semester(
                id=1,
                name="Fall",
                start_date=__import__("datetime").date(2026, 9, 1),
                end_date=__import__("datetime").date(2026, 12, 20),
            )
        )
        db.commit()
        token = get_lifecycle_overview(db, 1)["stateToken"]

    barrier = Barrier(2)

    def attempt():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = create_working_revision(db, 1, token)
                db.commit()
                return result["activeWorkingRevision"]["revisionId"]
            except (LifecycleConflict, Exception) as exc:
                db.rollback()
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _item: attempt(), range(2)))

    with Session(engine) as db:
        revisions = db.query(ScheduleRevision).all()
        assert len(revisions) == 1
        assert revisions[0].state == "draft"
    assert sum(isinstance(result, int) for result in results) == 1


def test_mutation_waiting_on_publication_revalidates_after_semester_claim(tmp_path: Path):
    database = tmp_path / "lifecycle-publication-mutation-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        revision = created["activeWorkingRevision"]
        prepared = prepare_publication(
            db, revision["revisionId"], revision["revisionVersion"], created["stateToken"]
        )

    publication_claimed = Event()
    mutation_attempting = Event()

    def publish():
        with Session(engine) as db:
            transition_revision(
                db,
                revision["revisionId"],
                action="publish",
                expected_revision_version=revision["revisionVersion"],
                expected_state_token=created["stateToken"],
                confirmed=True,
                publication_token=prepared["preparationToken"],
            )
            publication_claimed.set()
            assert mutation_attempting.wait(timeout=5)
            db.commit()

    def mutate():
        assert publication_claimed.wait(timeout=5)
        with Session(engine) as db:
            mutation_attempting.set()
            try:
                claim_active_working_revision(db, 1, revision["revisionId"])
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code
            raise AssertionError("A mutation acquired an already-published revision.")

    with ThreadPoolExecutor(max_workers=2) as pool:
        publication_future = pool.submit(publish)
        mutation_future = pool.submit(mutate)
        publication_future.result(timeout=10)
        assert mutation_future.result(timeout=10) == "revision_not_editable"


def test_competing_first_publications_create_one_publication_and_event(tmp_path: Path):
    database = tmp_path / "lifecycle-first-publication-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
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

    barrier = Barrier(2)

    def attempt():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = transition_revision(
                    db,
                    revision["revisionId"],
                    action="publish",
                    expected_revision_version=revision["revisionVersion"],
                    expected_state_token=created["stateToken"],
                    confirmed=True,
                    publication_token=preparation["preparationToken"],
                )
                db.commit()
                return result["currentPublication"]["revisionId"]
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _item: attempt(), range(2)))

    assert outcomes.count(revision["revisionId"]) == 1
    with Session(engine) as db:
        assert db.query(ScheduleRevision).filter(
            ScheduleRevision.state == "published"
        ).count() == 1
        assert db.query(ScheduleRevisionEvent).filter(
            ScheduleRevisionEvent.event_type == "published"
        ).count() == 1


def test_competing_replacement_publications_keep_one_current_revision_and_order_events(tmp_path: Path):
    database = tmp_path / "lifecycle-replacement-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
        initial = get_lifecycle_overview(db, 1)
        first = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        first_revision = first["activeWorkingRevision"]
        first_preparation = prepare_publication(
            db,
            first_revision["revisionId"],
            first_revision["revisionVersion"],
            first["stateToken"],
        )
        published = transition_revision(
            db,
            first_revision["revisionId"],
            action="publish",
            expected_revision_version=first_revision["revisionVersion"],
            expected_state_token=first["stateToken"],
            confirmed=True,
            publication_token=first_preparation["preparationToken"],
        )
        db.commit()
        successor_overview = create_working_revision(db, 1, published["stateToken"])
        db.commit()
        successor = successor_overview["activeWorkingRevision"]
        preparation = prepare_publication(
            db,
            successor["revisionId"],
            successor["revisionVersion"],
            successor_overview["stateToken"],
        )

    barrier = Barrier(2)

    def attempt():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = transition_revision(
                    db,
                    successor["revisionId"],
                    action="publish",
                    expected_revision_version=successor["revisionVersion"],
                    expected_state_token=successor_overview["stateToken"],
                    confirmed=True,
                    publication_token=preparation["preparationToken"],
                )
                db.commit()
                return result["currentPublication"]["revisionId"]
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _item: attempt(), range(2)))

    assert results.count(successor["revisionId"]) == 1
    assert len(results) == 2
    with Session(engine) as db:
        revisions = db.query(ScheduleRevision).order_by(ScheduleRevision.revision_number).all()
        assert [revision.state for revision in revisions] == ["superseded", "published"]
        replacement_events = db.query(ScheduleRevisionEvent).filter(
            ScheduleRevisionEvent.event_type.in_(["superseded", "published"]),
            ScheduleRevisionEvent.event_sequence > 2,
        ).order_by(ScheduleRevisionEvent.event_sequence).all()
        assert [event.event_type for event in replacement_events] == ["superseded", "published"]


def test_replacement_publication_rolls_back_supersession_and_publication_together(tmp_path: Path):
    database = tmp_path / "lifecycle-replacement-rollback.db"
    engine = create_engine(f"sqlite:///{database}")
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
        initial = get_lifecycle_overview(db, 1)
        first = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        first_revision = first["activeWorkingRevision"]
        first_preparation = prepare_publication(
            db,
            first_revision["revisionId"],
            first_revision["revisionVersion"],
            first["stateToken"],
        )
        published = transition_revision(
            db,
            first_revision["revisionId"],
            action="publish",
            expected_revision_version=first_revision["revisionVersion"],
            expected_state_token=first["stateToken"],
            confirmed=True,
            publication_token=first_preparation["preparationToken"],
        )
        db.commit()
        successor_overview = create_working_revision(db, 1, published["stateToken"])
        db.commit()
        successor = successor_overview["activeWorkingRevision"]
        preparation = prepare_publication(
            db,
            successor["revisionId"],
            successor["revisionVersion"],
            successor_overview["stateToken"],
        )

        transition_revision(
            db,
            successor["revisionId"],
            action="publish",
            expected_revision_version=successor["revisionVersion"],
            expected_state_token=successor_overview["stateToken"],
            confirmed=True,
            publication_token=preparation["preparationToken"],
        )
        db.rollback()

        current = get_lifecycle_overview(db, 1)
        assert current["currentPublication"]["revisionId"] == first_revision["revisionId"]
        assert current["activeWorkingRevision"]["revisionId"] == successor["revisionId"]


def test_create_and_restore_race_retains_exactly_one_working_revision(tmp_path: Path):
    database = tmp_path / "lifecycle-create-restore-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        revision = created["activeWorkingRevision"]
        abandoned = transition_revision(
            db,
            revision["revisionId"],
            action="abandon",
            expected_revision_version=revision["revisionVersion"],
            expected_state_token=created["stateToken"],
            confirmed=True,
        )
        db.commit()
        abandoned_revision = next(
            item for item in abandoned["revisions"] if item["revisionId"] == revision["revisionId"]
        )

    barrier = Barrier(2)

    def create():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = create_working_revision(db, 1, abandoned["stateToken"])
                db.commit()
                return result["activeWorkingRevision"]["revisionId"]
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code

    def restore():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = transition_revision(
                    db,
                    abandoned_revision["revisionId"],
                    action="restore",
                    expected_revision_version=abandoned_revision["revisionVersion"],
                    expected_state_token=abandoned["stateToken"],
                    confirmed=True,
                )
                db.commit()
                return result["activeWorkingRevision"]["revisionId"]
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(create), pool.submit(restore)]
        outcomes = [future.result(timeout=10) for future in results]

    assert sum(isinstance(outcome, int) for outcome in outcomes) == 1
    with Session(engine) as db:
        assert db.query(ScheduleRevision).filter(
            ScheduleRevision.state.in_(["draft", "ready_for_review"])
        ).count() == 1


def test_competing_restores_add_one_restoration_event(tmp_path: Path):
    database = tmp_path / "lifecycle-restore-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        revision = created["activeWorkingRevision"]
        abandoned = transition_revision(
            db,
            revision["revisionId"],
            action="abandon",
            expected_revision_version=revision["revisionVersion"],
            expected_state_token=created["stateToken"],
            confirmed=True,
        )
        db.commit()
        abandoned_revision = next(
            item for item in abandoned["revisions"] if item["revisionId"] == revision["revisionId"]
        )

    barrier = Barrier(2)

    def attempt():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = transition_revision(
                    db,
                    abandoned_revision["revisionId"],
                    action="restore",
                    expected_revision_version=abandoned_revision["revisionVersion"],
                    expected_state_token=abandoned["stateToken"],
                    confirmed=True,
                )
                db.commit()
                return result["activeWorkingRevision"]["revisionId"]
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _item: attempt(), range(2)))

    assert outcomes.count(revision["revisionId"]) == 1
    with Session(engine) as db:
        assert db.query(ScheduleRevisionEvent).filter(
            ScheduleRevisionEvent.event_type == "restored"
        ).count() == 1


def test_mutation_waiting_on_abandon_revalidates_after_semester_claim(tmp_path: Path):
    database = tmp_path / "lifecycle-abandon-mutation-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=False)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        revision = created["activeWorkingRevision"]

    abandonment_claimed = Event()
    mutation_attempting = Event()

    def abandon():
        with Session(engine) as db:
            transition_revision(
                db,
                revision["revisionId"],
                action="abandon",
                expected_revision_version=revision["revisionVersion"],
                expected_state_token=created["stateToken"],
                confirmed=True,
            )
            abandonment_claimed.set()
            assert mutation_attempting.wait(timeout=5)
            db.commit()

    def mutate():
        assert abandonment_claimed.wait(timeout=5)
        with Session(engine) as db:
            mutation_attempting.set()
            try:
                claim_active_working_revision(db, 1, revision["revisionId"])
            except LifecycleConflict as exc:
                db.rollback()
                return exc.code
            raise AssertionError("A mutation acquired an abandoned revision.")

    with ThreadPoolExecutor(max_workers=2) as pool:
        abandonment_future = pool.submit(abandon)
        mutation_future = pool.submit(mutate)
        abandonment_future.result(timeout=10)
        assert mutation_future.result(timeout=10) == "revision_not_editable"
