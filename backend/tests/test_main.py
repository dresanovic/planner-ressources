from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.terminology import TerminologyConfigurationError


def test_invalid_configured_terminology_blocks_startup(monkeypatch, tmp_path: Path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text('{"unknown":"value"}', encoding="utf-8")
    monkeypatch.setenv("CUSTOMER_TERMINOLOGY_FILE", str(invalid))
    with pytest.raises(TerminologyConfigurationError):
        with TestClient(app):
            pass
