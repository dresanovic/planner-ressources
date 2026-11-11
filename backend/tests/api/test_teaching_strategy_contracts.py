"""Shared semantic acceptance contracts; deliberately authored before production."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.conflict_aware_generation import (
    CandidateProof, CoverageFacts, OptimizationOperationStart, OptimizationOperationStatus, CourseRegenerationComparison,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = json.loads((ROOT / 'backend/tests/fixtures/teaching_strategy_contracts.json').read_text())
MODELS = {'proof': CandidateProof, 'coverage': CoverageFacts,
          'start': OptimizationOperationStart, 'status': OptimizationOperationStatus, 'comparison': CourseRegenerationComparison}


def test_client_and_backend_semantic_fixtures_match():
    assert FIXTURES == json.loads((ROOT / 'client/src/test/teachingStrategyContracts.json').read_text())


@pytest.mark.parametrize('case', FIXTURES['cases'], ids=lambda case: case['name'])
def test_shared_contract(case):
    model = MODELS[case['kind']]
    if case['valid']:
        result = model.model_validate(case['value'])
        encoded = result.model_dump(mode='json', by_alias=True)
        assert model.model_validate(encoded) == result
        if case['name'] == 'legacy-proof':
            assert encoded['objectiveProfile'] == 'standard-v1'
    else:
        with pytest.raises(ValidationError):
            model.model_validate(case['value'])
