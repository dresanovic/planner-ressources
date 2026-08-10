from fastapi.testclient import TestClient

from app.main import app
from app.terminology import TERMINOLOGY_KEYS


def test_public_catalog_is_complete_no_store_and_needs_no_credentials():
    with TestClient(app) as client:
        response = client.get("/api/public/ui-terminology")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert set(response.json()) == {"labels"}
    assert set(response.json()["labels"]) == set(TERMINOLOGY_KEYS)
    assert "CUSTOMER_TERMINOLOGY_FILE" not in response.text


def test_public_catalog_does_not_require_or_receive_lecturer_authorization():
    with TestClient(app) as client:
        response = client.get("/api/public/ui-terminology")
    assert response.status_code == 200
