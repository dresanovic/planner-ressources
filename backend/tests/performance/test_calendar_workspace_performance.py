from datetime import timedelta
from time import perf_counter

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import ExamSession, InstitutionHoliday, Semester
from app.services.calendar_workspace import get_calendar_workspace
from app.services.schedule_lifecycle import (
    create_working_revision,
    get_lifecycle_overview,
)
from tests.performance.test_schedule_lifecycle_performance import (
    _seed_reference_schedule,
)


def test_reference_workspace_initial_loads_meet_success_criteria(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'calendar-workspace-performance.db'}")
    initialize_database(engine)
    with Session(engine) as db:
        _seed_reference_schedule(db)
        db.execute(delete(ExamSession))
        semester = get_lifecycle_overview(db, 1)
        create_working_revision(db, 1, semester["stateToken"])
        start = db.get(InstitutionHoliday, 1)
        assert start is None
        db.add_all(
            [
                InstitutionHoliday(
                    date=db.get(Semester, 1).start_date + timedelta(days=index * 2),
                    name=f"Institution holiday {index + 1:02d}",
                )
                for index in range(50)
            ]
        )
        db.commit()

        durations = []
        for _index in range(20):
            db.expire_all()
            started = perf_counter()
            workspace = get_calendar_workspace(db, 1)
            durations.append(perf_counter() - started)
            assert len(workspace["courses"]) == 100
            assert len(workspace["occurrences"]) == 500
            assert len(workspace["holidays"]) == 50

        assert sum(duration <= 3 for duration in durations) >= 19
        assert all(duration <= 10 for duration in durations)
