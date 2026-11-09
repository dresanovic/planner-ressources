from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from pathlib import Path
from threading import Barrier

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.models.planning import DraftSchedule
from app.schemas.conflict_aware_generation import PreparedOptimizationCourseInput
from app.services.conflict_aware_generation import (
    StaleOptimizationCandidate,
    accept_optimization,
    generate_optimization,
    prepare_optimization,
)
from app.services.draft_schedule_repository import load_course_plan, replace_draft_schedule
from app.services.schedule_generation import GeneratedSession
from tests.optimization_fixtures import seed_optimization_planner


def test_preference_only_marker_change_rejects_both_concurrent_accepts_without_business_writes(tmp_path):
    from tests.fixtures.dated_intensive_windows import seed_acceptance_context,mutate_acceptance_window,business_rows
    engine=create_engine(f"sqlite:///{tmp_path/'dated-marker-race.db'}",connect_args={'check_same_thread':False,'timeout':10})
    initialize_database(engine)
    with Session(engine) as db:
        seed_acceptance_context(db,with_selected=True)
        prepared=prepare_optimization(db,1,[1],[],1)
        courses=[PreparedOptimizationCourseInput(courseId=c.course_id,expectedDraftScheduleId=c.draft_schedule_id,expectedDraftRevision=c.draft_revision,inputSnapshotToken=c.input_snapshot_token) for c in prepared.courses]
        preview=generate_optimization(db,1,courses,[],prepared.shared_snapshot_token,1)
        mutate_acceptance_window(db,'fixed_marker')
    before=business_rows(engine);barrier=Barrier(2)
    def accept():
        with Session(engine) as db:
            barrier.wait(timeout=5)
            try:accept_optimization(db,1,courses,[],prepared.shared_snapshot_token,1,preview.candidate_fingerprint)
            except StaleOptimizationCandidate:
                db.rollback();return 'stale'
            return 'unexpected-save'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:accept(),range(2)))
    assert results==['stale','stale']
    assert business_rows(engine)==before


def test_simultaneous_acceptance_commits_the_joint_candidate_at_most_once(tmp_path: Path):
    database = tmp_path / "regeneration-accept-race.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False, "timeout": 10}
    )
    initialize_database(engine)
    with Session(engine) as db:
        seed_optimization_planner(db, course_count=2, total_units=4)
        replace_draft_schedule(db, load_course_plan(db, 1), 1, [
            GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1),
        ])
        db.commit()
        prepared = prepare_optimization(db, 1, [1, 2], [], schedule_revision_id=1)
        courses = [
            {
                "courseId": item.course_id,
                "expectedDraftScheduleId": item.draft_schedule_id,
                "expectedDraftRevision": item.draft_revision,
                "inputSnapshotToken": item.input_snapshot_token,
            }
            for item in prepared.courses
        ]
        preview = generate_optimization(
            db,
            1,
            [PreparedOptimizationCourseInput(**item) for item in courses],
            [],
            prepared.shared_snapshot_token,
            schedule_revision_id=1,
        )
        fingerprint = preview.candidate_fingerprint
        shared_token = prepared.shared_snapshot_token
        db.rollback()

    barrier = Barrier(2)

    def attempt():
        with Session(engine) as db:
            barrier.wait()
            try:
                result = accept_optimization(
                    db,
                    1,
                    [PreparedOptimizationCourseInput(**item) for item in courses],
                    [],
                    shared_token,
                    1,
                    fingerprint,
                )
                db.commit()
                return ("saved", tuple(item.draft_revision for item in result.outcomes))
            except StaleOptimizationCandidate:
                db.rollback()
                return ("stale", ())

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _item: attempt(), range(2)))

    assert [item[0] for item in results].count("saved") == 1
    assert [item[0] for item in results].count("stale") == 1
    with Session(engine) as db:
        drafts = {item.course_id: item for item in db.query(DraftSchedule).all()}
        assert set(drafts) == {1, 2}
        assert drafts[1].revision == 2
        assert drafts[2].revision == 1
