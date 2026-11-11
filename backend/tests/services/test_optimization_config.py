import json

import pytest

from app.services.optimization_config import OptimizationConfigurationError, load_optimization_policy


def test_shipped_defaults_and_fingerprint(monkeypatch):
    from pathlib import Path
    monkeypatch.delenv("TEACHING_OPTIMIZATION_POLICY_FILE", raising=False)
    policy = load_optimization_policy()
    installed = json.loads((Path(__file__).resolve().parents[3] / 'config/optimization/policy.json').read_text())
    assert (policy.default_seconds, policy.ceiling_seconds) == (installed.get('defaultSeconds', 300), installed.get('ceilingSeconds', 1800))
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


@pytest.mark.parametrize('algorithm', ['standard', 'cohort', 'lecturer', 'standard_optimized'])
def test_valid_algorithm_is_captured_and_fingerprinted(monkeypatch, tmp_path, algorithm):
    path = tmp_path / 'policy.json'
    monkeypatch.setenv('TEACHING_OPTIMIZATION_POLICY_FILE', str(path))
    path.write_text('{}')
    standard = load_optimization_policy()
    assert standard.active_algorithm == 'standard'
    path.write_text(json.dumps({'activeAlgorithm': algorithm}))
    selected = load_optimization_policy()
    assert selected.active_algorithm == algorithm
    assert selected.strategy_profile == ({'standard':'standard-v1', 'standard_optimized':'standard-optimized-v1'}.get(algorithm, 'heuristic-v1'))
    assert (selected.policy_fingerprint == standard.policy_fingerprint) == (algorithm == 'standard')
    path.write_text(json.dumps({'ceilingSeconds': 1800, 'activeAlgorithm': algorithm, 'defaultSeconds': 300}, indent=4))
    assert load_optimization_policy() == selected


@pytest.mark.parametrize('value', [None, '', 'Standard', 'unknown', 1, True, [], {}])
def test_invalid_explicit_algorithm_never_defaults(monkeypatch, tmp_path, value):
    path = tmp_path / 'policy.json'
    path.write_text(json.dumps({'activeAlgorithm': value}))
    monkeypatch.setenv('TEACHING_OPTIMIZATION_POLICY_FILE', str(path))
    with pytest.raises(OptimizationConfigurationError, match='activeAlgorithm'):
        load_optimization_policy()


def test_normal_policy_is_source_relative_even_from_different_cwd(monkeypatch, tmp_path):
    monkeypatch.delenv('TEACHING_OPTIMIZATION_POLICY_FILE', raising=False)
    expected = load_optimization_policy()
    monkeypatch.chdir(tmp_path)
    assert load_optimization_policy() == expected


def test_normal_missing_policy_requires_provisioning(monkeypatch, tmp_path):
    from app.services import optimization_config as config
    monkeypatch.delenv('TEACHING_OPTIMIZATION_POLICY_FILE', raising=False)
    monkeypatch.setattr(config, 'DEFAULT_POLICY_PATH', tmp_path / 'missing.json', raising=False)
    with pytest.raises(OptimizationConfigurationError) as failure:
        load_optimization_policy()
    message = str(failure.value)
    assert str(tmp_path / 'missing.json') in message
    assert 'bereitstellen' in message


def test_duplicate_selector_rejected(monkeypatch, tmp_path):
    path = tmp_path / 'policy.json'
    path.write_text('{"activeAlgorithm":"standard","activeAlgorithm":"cohort"}')
    monkeypatch.setenv('TEACHING_OPTIMIZATION_POLICY_FILE', str(path))
    with pytest.raises(OptimizationConfigurationError):
        load_optimization_policy()
