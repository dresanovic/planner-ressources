"""Connected HTTP acceptance, actual spawned workers, isolated one/20 selections."""
from time import monotonic, sleep

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db.session import get_db
from app.main import app
from app.models.planning import GenerationConstraintSet, DraftSchedule
from app.services import optimization_operations as operations
from tests.fixtures.teaching_strategies import isolated_planner
from tests.optimization_fixtures import SEMESTER_START, operation_start_payload, OPERATION_ID, CONTEXT_SECRET
from tests.planner_auth_fixtures import add_planner_account, add_current_session


@pytest.mark.parametrize('algorithm', ['standard','cohort','lecturer','standard_optimized'])
@pytest.mark.parametrize('count', [1,20])
def test_connected_actual_dispatch_identity_review_and_save(tmp_path, monkeypatch, algorithm, count, record_property):
    engine, policy = isolated_planner(tmp_path,monkeypatch,count=count,algorithm=algorithm,total_units=2)
    factory = sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as db:
        account = add_planner_account(db)
        add_current_session(db,account_id=account.id)
        # Keep the acceptance snapshot small enough to finish all searches;
        # separate benchmarks cover longer, competitive and intensive snapshots.
        for course_id in range(1,count+1):
            db.add(GenerationConstraintSet(course_id=course_id,semester_id=1,
                planning_start_date=SEMESTER_START,planning_end_date=SEMESTER_START))
        db.commit()
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            client.cookies.set('planner_session','s'*43)
            headers = {'X-CSRF-Protection':'1'}
            preparation = client.post('/api/draft-schedules/optimization/prepare',headers=headers,
                json={'semesterId':1,'scheduleRevisionId':1,'courseIds':list(range(1,count+1)),'unavailableDates':[]})
            assert preparation.status_code == 200
            prepared = preparation.json()
            assert prepared['algorithm'] == algorithm
            started = monotonic()
            response = client.post('/api/draft-schedules/optimization/operations',headers=headers,json=operation_start_payload(prepared))
            start_seconds = monotonic()-started
            assert response.status_code == 202 and start_seconds < 1
            assert response.json()['algorithm'] == algorithm
            # File deletion after Start must not change compute, replay, review
            # or acceptance. It blocks only genuinely new preparations/runs.
            policy.unlink()
            replay = client.post('/api/draft-schedules/optimization/operations',headers=headers,json=operation_start_payload(prepared))
            assert replay.status_code == 202 and replay.json()['algorithm'] == algorithm
            end = monotonic()+12
            while monotonic() < end:
                status_response = client.get(f'/api/draft-schedules/optimization/operations/{OPERATION_ID}',headers={'X-Optimization-Context':CONTEXT_SECRET})
                assert status_response.status_code == 200
                status = status_response.json()
                assert status['algorithm'] == algorithm
                if status['phase'] not in ('preparing','optimizing','checking'):
                    break
                sleep(.02)
            assert status['phase'] in ('ready_to_save','awaiting_decision'), status['phase']
            assert status['selectionCount'] == count and len(status['review']['comparison']['courses']) == count
            assert status['review']['algorithm'] == algorithm
            assert status['review']['comparison']['generated']['scheduledUnits'] == 2*count
            with factory() as db:
                assert db.query(DraftSchedule).count() == 0
            route = 'finalize' if status['canFinalize'] else 'accept'
            saved = client.post(f'/api/draft-schedules/optimization/operations/{OPERATION_ID}/{route}',headers=headers,
                json={'contextSecret':CONTEXT_SECRET,'candidateFingerprint':status['review']['candidateFingerprint']})
            assert saved.status_code == 200 and saved.json()['saved']
            assert saved.json()['result']['algorithm'] == algorithm
            assert len(saved.json()['result']['outcomes']) == count
            started = monotonic()
            cancelled = client.post(f'/api/draft-schedules/optimization/operations/{OPERATION_ID}/cancel',headers=headers,json={'reason':'cancel'})
            cancel_seconds = monotonic()-started
            assert cancelled.status_code == 200 and cancelled.json()['saved'] and cancel_seconds < 1
            record_property('connected_strategy',{'algorithm':algorithm,'courses':count,
                'startAcknowledgementSeconds':start_seconds,'postCommitCancelAcknowledgementSeconds':cancel_seconds})
    finally:
        app.dependency_overrides.clear()
        operations.shutdown_operations(engine)
        engine.dispose()
