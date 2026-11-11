import json
from pathlib import Path

import pytest

from app.services.teaching_strategies import get_strategy
from tests.fixtures.teaching_strategies import standard_cases, completed_facts


def test_unknown_strategy_never_falls_back():
    with pytest.raises(ValueError):
        get_strategy('unknown')


@pytest.mark.parametrize('name', tuple(standard_cases()))
def test_standard_adapter_preserves_completed_baseline(name):
    expected = json.loads((Path(__file__).parents[1] / 'fixtures/teaching_standard_baselines.json').read_text())[name]
    courses, fixed = standard_cases()[name]
    result = get_strategy('standard').optimize(courses, fixed, generated_only=True, deadline_seconds=10)
    assert completed_facts(result) == expected['result']
