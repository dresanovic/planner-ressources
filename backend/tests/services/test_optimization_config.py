import json

import pytest

from app.services.optimization_config import OptimizationConfigurationError, load_optimization_policy


def test_shipped_defaults_and_fingerprint(monkeypatch):
    monkeypatch.delenv("TEACHING_OPTIMIZATION_POLICY_FILE", raising=False)
    policy = load_optimization_policy()
    assert (policy.default_seconds, policy.ceiling_seconds) == (300, 1800)
    assert len(policy.policy_fingerprint) == 64
    assert policy == load_optimization_policy()


def test_optional_keys_and_hot_atomic_replacement(monkeypatch, tmp_path):
    policy_file = tmp_path / "policy.json"
    monkeypatch.setenv("TEACHING_OPTIMIZATION_POLICY_FILE", str(policy_file))
    policy_file.write_text('{}')
    captured = load_optimization_policy()
    replacement = tmp_path / "next.json"
    replacement.write_text('{"defaultSeconds":600,"ceilingSeconds":1200}')
    replacement.replace(policy_file)
    changed = load_optimization_policy()
    assert captured.default_seconds == 300
    assert changed.default_seconds == 600
    assert captured.policy_fingerprint != changed.policy_fingerprint
    policy_file.write_text('{"defaultSeconds":3600,"ceilingSeconds":7200}')
    assert load_optimization_policy().default_seconds == 3600


@pytest.mark.parametrize("value", [0, -1, 1.5, True, "300", None, float("nan"), float("inf")])
@pytest.mark.parametrize("key", ["defaultSeconds", "ceilingSeconds"])
def test_invalid_numeric_policy_never_clamped(monkeypatch, tmp_path, key, value):
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({key: value}))
    monkeypatch.setenv("TEACHING_OPTIMIZATION_POLICY_FILE", str(path))
    with pytest.raises(OptimizationConfigurationError, match=key):
        load_optimization_policy()


@pytest.mark.parametrize("text", ['[]', 'null', '{', '{"unknown":1}', '{"defaultSeconds":1801}', '{"defaultSeconds":300,"defaultSeconds":600}'])
def test_invalid_shape_unknown_keys_and_default_above_ceiling(monkeypatch, tmp_path, text):
    path = tmp_path / "policy.json"
    path.write_text(text)
    monkeypatch.setenv("TEACHING_OPTIMIZATION_POLICY_FILE", str(path))
    with pytest.raises(OptimizationConfigurationError):
        load_optimization_policy()


def test_supplied_missing_file_blocks_instead_of_falling_back(monkeypatch, tmp_path):
    monkeypatch.setenv("TEACHING_OPTIMIZATION_POLICY_FILE", str(tmp_path / "missing.json"))
    with pytest.raises(OptimizationConfigurationError, match="missing.json"):
        load_optimization_policy()


def test_unreadable_file_reports_safe_operator_diagnostic(monkeypatch):
    from pathlib import Path
    monkeypatch.setenv("TEACHING_OPTIMIZATION_POLICY_FILE", "operator/policy.json")
    def deny_read(*args, **kwargs):
        raise PermissionError("private file contents must not appear")
    monkeypatch.setattr(Path, "read_text", deny_read)
    with pytest.raises(OptimizationConfigurationError) as failure:
        load_optimization_policy()
    assert "policy.json" in str(failure.value)
    assert "PermissionError" in str(failure.value)
    assert "private file contents" not in str(failure.value)
