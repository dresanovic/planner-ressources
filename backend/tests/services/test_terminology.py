import json
from pathlib import Path

import pytest

from app.terminology import (
    TerminologyConfigurationError,
    load_effective_terminology,
)


SCHEMA_PATH = Path(__file__).parents[3] / "specs" / "I-002" / "contracts" / "terminology-overrides.schema.json"


def test_defaults_match_the_published_exact_key_set():
    expected = set(json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["properties"])
    actual = load_effective_terminology(None)
    assert set(actual) == expected
    assert all(isinstance(value, str) and value.strip() for value in actual.values())
    with pytest.raises(TypeError):
        actual["course.singular"] = "changed"


def test_partial_unicode_override_keeps_omitted_defaults(tmp_path):
    path = tmp_path / "customer.json"
    path.write_text('{"course.singular":"Lehrangebot","room.plural":"Hörsäle"}', encoding="utf-8")
    result = load_effective_terminology(path)
    assert result["course.singular"] == "Lehrangebot"
    assert result["room.plural"] == "Hörsäle"
    assert result["lecturer.singular"] == "Lehrende Person"


@pytest.mark.parametrize(
    "content,category",
    [
        ('{"course.singular":"A","course.singular":"B"}', "duplicate"),
        ('{"course.singular":', "malformed"),
        ('[]', "object"),
        ('{"unknown.key":"A"}', "unknown.key"),
        ('{"course.singular":"   "}', "course.singular"),
        ('{"course.singular":2}', "course.singular"),
        ('{"course.singular":"A\\nB"}', "course.singular"),
    ],
)
def test_invalid_override_is_rejected_without_echoing_values(tmp_path, content, category):
    path = tmp_path / "customer.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(TerminologyConfigurationError) as caught:
        load_effective_terminology(path)
    message = str(caught.value)
    assert category in message
    assert "A\\nB" not in message


def test_configured_missing_file_is_not_treated_as_absent(tmp_path):
    path = tmp_path / "missing.json"
    with pytest.raises(TerminologyConfigurationError, match="cannot be read"):
        load_effective_terminology(path)
