from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.db.session import get_db
from tests.lecturer_review_fixtures import seed_lecturer_review_fixture


app_main = importlib.import_module("app.main")


@pytest.fixture()
def client_and_db(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    db = Session(engine)
    app_main.app.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(app_main, "SessionLocal", lambda: Session(engine))
    try:
        with TestClient(app_main.app) as client:
            yield client, db
    finally:
        app_main.app.dependency_overrides.clear()
        db.close()
        engine.dispose()


def _issue(client: TestClient) -> dict:
    response = client.post(
        "/api/schedule-revisions/2/lecturer-review-links",
        json={"lecturerId": 1},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/semesters/not-an-integer/calendar-workspace"),
        ("POST", "/api/lecturer-review-links/not-an-integer/revoke"),
    ],
)
def test_stored_active_lecturer_secret_is_rejected_before_route_validation(
    client_and_db,
    method: str,
    path: str,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue(client)

    response = client.request(
        method,
        path,
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "PLANNER_AUTHORIZATION_REQUIRED",
        "message": "Planner authorization is required.",
    }


def test_stored_ended_lecturer_secret_remains_rejected(client_and_db):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue(client)
    link_id = issued["issuedLink"]["id"]
    revoked = client.post(f"/api/lecturer-review-links/{link_id}/revoke")
    assert revoked.status_code == 200, revoked.text

    response = client.get(
        "/api/semesters/not-an-integer/calendar-workspace",
        headers={"Authorization": f"Bearer {issued['secret']}"},
    )

    assert response.status_code == 403


def test_unrelated_exact_shape_bearer_is_left_to_gateway_authorization(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)

    response = client.get(
        "/api/semesters/not-an-integer/calendar-workspace",
        headers={"Authorization": "Bearer " + ("u" * 43)},
    )

    assert response.status_code == 422


def test_gateway_authorized_planner_request_still_reaches_planner_route(
    client_and_db,
):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)

    response = client.get(
        "/api/schedule-revisions/2/lecturer-review",
        headers={"Authorization": "Bearer gateway-authorized-planner"},
    )

    assert response.status_code == 200


def test_public_operations_are_the_only_stored_secret_allowlist(client_and_db):
    client, db = client_and_db
    seed_lecturer_review_fixture(db)
    issued = _issue(client)
    headers = {"Authorization": f"Bearer {issued['secret']}"}

    review = client.get("/api/public/lecturer-review", headers=headers)
    calendar = client.get(
        "/api/public/lecturer-review/calendar", headers=headers
    )
    invalid_feedback = client.post(
        "/api/public/lecturer-review/feedback",
        headers=headers,
        json={},
    )
    near_miss = client.get(
        "/api/public/lecturer-review/feedback",
        headers=headers,
    )
    trailing_calendar = client.get(
        "/api/public/lecturer-review/calendar/", headers=headers
    )
    wrong_method_calendar = client.post(
        "/api/public/lecturer-review/calendar", headers=headers
    )
    cookie_only_calendar = client.get(
        "/api/public/lecturer-review/calendar",
        cookies={"lecturer_review": issued["secret"]},
    )

    assert review.status_code == 200
    assert calendar.status_code == 200
    assert invalid_feedback.status_code == 422
    assert near_miss.status_code == 403
    assert trailing_calendar.status_code == 403
    assert wrong_method_calendar.status_code == 403
    assert cookie_only_calendar.status_code == 404
