"""Recorded before any strategy/optimizer production changes."""
import json
from pathlib import Path

import pytest

from app.services.semester_optimization import optimize_semester
from tests.fixtures.teaching_strategies import standard_cases, snapshot_identity, completed_facts
from tests.fixtures.teaching_strategies import preference_inputs, PORTION_CASES, isolated_planner


@pytest.mark.parametrize('name', tuple(standard_cases()))
def test_prechange_completed_standard_baseline(name):
    courses, fixed = standard_cases()[name]
    expected = json.loads((Path(__file__).parents[1] / 'fixtures' /
                          'teaching_standard_baselines.json').read_text())[name]
    assert snapshot_identity(courses, fixed) == expected['snapshot']
    result = optimize_semester(courses, fixed, generated_only=True, deadline_seconds=10)
    assert result.optimal
    assert completed_facts(result) == expected['result']


def test_acceptance_inputs_are_detached_and_fixed():
    cases = preference_inputs()
    assert len(cases['twenty'][0]) == 20
    assert cases['exact22'][0][0].total_units == 22
    assert all(sum(targets) == total for total, _, targets in PORTION_CASES)
    assert snapshot_identity(*cases['distinct_owner']) == snapshot_identity(*preference_inputs()['distinct_owner'])


@pytest.mark.parametrize('count', [1, 20])
def test_database_and_policy_helpers_are_isolated(tmp_path, monkeypatch, count):
    from sqlalchemy import text
    engine, policy = isolated_planner(tmp_path, monkeypatch, count=count)
    try:
        assert str(tmp_path) in str(engine.url)
        with engine.connect() as connection:
            assert connection.execute(text('SELECT count(*) FROM courses')).scalar() == count
        assert json.loads(policy.read_text())['activeAlgorithm'] == 'standard'
    finally:
        engine.dispose()
