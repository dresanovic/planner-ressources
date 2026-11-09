"""Operation wire-contract and API behavior for I-006 (isolated test database)."""
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.conflict_aware_generation import (
    OptimizationOperationStart, OptimizationOperationStatus, OptimizationOperationDecision,
)
from tests.optimization_fixtures import OPERATION_ID, CONTEXT_SECRET, POLICY_FINGERPRINT
from tests.services.test_optimization_operations import setup_operation


def start_payload():
    return {
        "operationId": OPERATION_ID, "contextSecret": CONTEXT_SECRET,
        "policyFingerprint": POLICY_FINGERPRINT,
        "preparation": {
            "semesterId": 1, "scheduleRevisionId": 1, "unavailableDates": [],
            "sharedSnapshotToken": "d" * 64,
            "courses": [{"courseId": 1, "inputSnapshotToken": "e" * 64}],
        },
    }


def test_operation_start_identity_and_no_authored_candidate_or_override():
    payload = start_payload()
    parsed = OptimizationOperationStart.model_validate(payload)
    assert parsed.operation_id == UUID(OPERATION_ID)
    assert parsed.preparation.courses[0].expected_draft_schedule_id is None
    for key, value in [("sessions", []), ("budgetSeconds", 600), ("ownerAccountId", 1)]:
        with pytest.raises(ValidationError):
            OptimizationOperationStart.model_validate({**payload, key: value})


@pytest.mark.parametrize("field,value", [
    ("operationId", "00000000-0000-1000-8000-000000000001"),
    ("contextSecret", "ab"), ("contextSecret", "AB" * 32),
    ("policyFingerprint", "wrong"),
])
def test_operation_start_rejects_invalid_identity(field, value):
    with pytest.raises(ValidationError):
        OptimizationOperationStart.model_validate({**start_payload(), field: value})


@pytest.mark.parametrize("ids", [[], [1, 1], list(range(1, 22)), [0]])
def test_operation_start_rejects_invalid_selection(ids):
    payload = start_payload()
    payload["preparation"]["courses"] = [{"courseId": i, "inputSnapshotToken": "e" * 64} for i in ids]
    with pytest.raises(ValidationError):
        OptimizationOperationStart.model_validate(payload)


def test_decision_requires_exact_candidate_and_context_only():
    payload = {"contextSecret": CONTEXT_SECRET, "candidateFingerprint": "a" * 64}
    assert OptimizationOperationDecision.model_validate(payload).candidate_fingerprint == "a" * 64
    for bad in [{"candidateFingerprint": "a" * 64}, {**payload, "courseIds": [1]}]:
        with pytest.raises(ValidationError):
            OptimizationOperationDecision.model_validate(bad)


def test_outcome_only_status_has_no_review_and_supports_more_than_sixty_seconds():
    status = OptimizationOperationStatus.model_validate({
        "operationId": OPERATION_ID, "semesterId": 1, "scheduleRevisionId": 1,
        "selectedCourseIds": [1], "selectionCount": 1, "phase": "optimizing",
        "budgetSeconds": 300, "elapsedMilliseconds": 65001, "budgetExhausted": False,
        "currentObjectiveKey": None, "saved": False, "canAccept": False,
        "canFinalize": False, "review": None, "result": None,
    })
    assert status.elapsed_milliseconds == 65001
    assert "contextSecret" not in status.model_dump(by_alias=True)


def test_saved_summary_does_not_reintroduce_sixty_second_limit():
    from app.schemas.conflict_aware_generation import OptimizationSummary
    summary = OptimizationSummary(total=1, complete=1, improvedPartial=0, unchanged=0,
        failed=0, stale=0, scheduledUnits=8, remainingUnits=0,
        elapsedMilliseconds=300001, optimalForPreparedSnapshot=True)
    assert summary.elapsed_milliseconds == 300001


def test_operation_http_start_poll_finalize_and_passive_auth(setup_operation):
    from fastapi.testclient import TestClient
    from time import sleep
    from app.main import app
    from app.db.session import get_db
    from app.models.planning import PlannerSession
    factory, auth, request, worker = setup_operation
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            client.cookies.set('planner_session', 's' * 43)
            headers = {'X-CSRF-Protection':'1', 'Content-Type':'application/json'}
            response = client.post('/api/draft-schedules/optimization/operations',
                json=request.model_dump(by_alias=True, mode='json'), headers=headers)
            assert response.status_code == 202
            with factory() as db: original_activity = db.get(PlannerSession, auth.session.id).last_activity_at
            for _ in range(200):
                status = client.get(f'/api/draft-schedules/optimization/operations/{OPERATION_ID}', headers={'X-Optimization-Context':CONTEXT_SECRET})
                assert status.status_code == 200
                assert status.headers['cache-control'] == 'no-store'
                if status.json()['phase'] == 'ready_to_save': break
                sleep(.01)
            assert status.json()['canFinalize']
            with factory() as db: assert db.get(PlannerSession, auth.session.id).last_activity_at == original_activity
            result = client.post(f'/api/draft-schedules/optimization/operations/{OPERATION_ID}/finalize',
                json={'contextSecret':CONTEXT_SECRET, 'candidateFingerprint':status.json()['review']['candidateFingerprint']}, headers=headers)
            assert result.status_code == 200
            assert result.json()['saved']
            assert result.json()['result']['summary']['scheduledUnits'] == 16
            bad = client.post('/api/draft-schedules/optimization/operations', headers=headers,
                json={'contextSecret':'never-echo-this-secret'})
            assert bad.status_code == 422
            assert 'never-echo-this-secret' not in bad.text
    finally:
        app.dependency_overrides.clear()


def test_retired_synchronous_routes_cannot_bypass_operation_identity(setup_operation):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db
    from app.models.planning import DraftSchedule
    factory, auth, request, worker=setup_operation
    def override():
        with factory() as db: yield db
    app.dependency_overrides[get_db]=override
    try:
        with TestClient(app) as client:
            client.cookies.set('planner_session','s'*43)
            for route in ('generate','accept'):
                body=request.preparation.model_dump(mode='json',by_alias=True)
                if route=='accept': body['candidateFingerprint']='a'*64
                response=client.post(f'/api/draft-schedules/optimization/{route}',json=body,headers={'X-CSRF-Protection':'1'})
                assert response.status_code==409
                assert response.json()['errors'][0]['code']=='OPERATION_API_REQUIRED'
        with factory() as db: assert db.query(DraftSchedule).count()==0
    finally: app.dependency_overrides.clear()


@pytest.mark.parametrize("method,path", [
    ("get", f"/operations/{OPERATION_ID}"),
    ("post", "/operations"),
    ("post", f"/operations/{OPERATION_ID}/accept"),
    ("post", f"/operations/{OPERATION_ID}/finalize"),
    ("post", f"/operations/{OPERATION_ID}/cancel"),
])
def test_operation_routes_require_planner_authentication(method, path):
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.db.base import Base
    from app.db.session import get_db
    from app.main import app
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    def override():
        yield db
    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            response = client.request(method, "/api/draft-schedules/optimization" + path,
                headers={"X-CSRF-Protection": "1", "Content-Type": "application/json"},
                **({"json": {}} if method == "post" else {}))
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()


@pytest.mark.parametrize('change,code',[
    ('published','revision_not_editable'),('abandoned','revision_not_editable'),
    ('missing_revision','working_revision_required'),('missing_semester','semester_not_found')])
def test_definitive_start_rejection_creates_no_receipt_or_worker(setup_operation,change,code):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db
    from app.models.planning import OptimizationOperation
    from tests.services.test_optimization_operations import close_working_revision,saved_state
    factory,auth,request,worker=setup_operation
    if change in ('published','abandoned'):
        with factory() as db:close_working_revision(db,change)
    body=request.model_dump(by_alias=True,mode='json')
    if change=='missing_revision':body['preparation']['scheduleRevisionId']=999
    if change=='missing_semester':body['preparation']['semesterId']=999
    before=saved_state(factory)
    def override():
        with factory() as db:yield db
    app.dependency_overrides[get_db]=override
    try:
        with TestClient(app) as client:
            client.cookies.set('planner_session','s'*43)
            response=client.post('/api/draft-schedules/optimization/operations',json=body,headers={'X-CSRF-Protection':'1'})
            assert response.status_code==(404 if change=='missing_semester' else 409)
            assert response.json()['errors'][0]['code']==code
            assert client.get(f'/api/draft-schedules/optimization/operations/{request.operation_id}').status_code==404
        with factory() as db:assert db.get(OptimizationOperation,str(request.operation_id)) is None
        assert worker.calls==0 and saved_state(factory)==before
    finally:app.dependency_overrides.clear()


@pytest.mark.parametrize('origin',['http://localhost:5173','http://127.0.0.1:5173'])
def test_development_status_poll_allows_live_context_cors_preflight(setup_operation,origin):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db
    factory,auth,request,worker=setup_operation
    def override():
        with factory() as db:yield db
    app.dependency_overrides[get_db]=override
    try:
        with TestClient(app) as client:
            response=client.options(f'/api/draft-schedules/optimization/operations/{request.operation_id}',headers={
                'Origin':origin,'Access-Control-Request-Method':'GET',
                'Access-Control-Request-Headers':'x-optimization-context'})
            assert response.status_code==200
            assert response.headers['access-control-allow-origin']==origin
            assert response.headers['access-control-allow-credentials']=='true'
            assert 'x-optimization-context' in response.headers['access-control-allow-headers'].lower()
            denied=client.options(f'/api/draft-schedules/optimization/operations/{request.operation_id}',headers={
                'Origin':'https://untrusted.example','Access-Control-Request-Method':'GET',
                'Access-Control-Request-Headers':'x-optimization-context'})
            assert denied.status_code==400 and 'access-control-allow-origin' not in denied.headers
    finally:app.dependency_overrides.clear()


def test_cancel_api_records_the_supplied_reason(setup_operation):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db.session import get_db
    from app.models.planning import OptimizationOperation
    from app.services import optimization_operations as operations
    from tests.services.test_optimization_operations import settled
    factory,auth,request,worker=setup_operation
    with factory() as db:operations.start_operation(db,request,auth)
    settled(factory,auth,request)
    def override():
        with factory() as db:yield db
    app.dependency_overrides[get_db]=override
    try:
        with TestClient(app) as client:
            client.cookies.set('planner_session','s'*43)
            response=client.post(f'/api/draft-schedules/optimization/operations/{request.operation_id}/cancel',
                json={'reason':'navigation'},headers={'X-CSRF-Protection':'1'})
            assert response.status_code==200
            assert response.json()['phase']=='cancelled'
            assert response.json()['terminalCode']=='CANCELLED_BY_NAVIGATION'
        with factory() as db:
            assert db.get(OptimizationOperation,str(request.operation_id)).terminal_code=='CANCELLED_BY_NAVIGATION'
    finally:app.dependency_overrides.clear()
