import pytest


@pytest.fixture
def isolated_standard_policy(tmp_path, monkeypatch):
    """Keep Standard-based scenarios independent of the installation policy.

    Tests for policy reloads and other strategies may replace this file or
    override the environment variable within their own scenario.
    """
    path = tmp_path / "operation-policy.json"
    path.write_text(
        '{"activeAlgorithm":"standard","defaultSeconds":300,"ceilingSeconds":1800}',
        encoding="utf-8",
    )
    monkeypatch.setenv("TEACHING_OPTIMIZATION_POLICY_FILE", str(path))
    return path
