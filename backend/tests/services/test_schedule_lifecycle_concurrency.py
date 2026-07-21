from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import ScheduleRevision, Semester
from app.services.schedule_lifecycle import (
    LifecycleConflict,
    create_working_revision,
    get_lifecycle_overview,
)


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
