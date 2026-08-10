import json
import os
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any


DEFAULT_TERMINOLOGY_PATH = Path(__file__).parent / "config" / "terminology.de.json"
TERMINOLOGY_KEYS = (
    "course.singular", "course.plural", "course.navigation", "course.heading", "course.fieldLabel", "course.tableHeading",
    "lecturer.singular", "lecturer.plural", "lecturer.navigation", "lecturer.heading", "lecturer.fieldLabel", "lecturer.tableHeading",
    "cohort.singular", "cohort.plural", "cohort.navigation", "cohort.heading", "cohort.fieldLabel", "cohort.tableHeading",
    "room.singular", "room.plural", "room.navigation", "room.heading", "room.fieldLabel", "room.tableHeading",
    "schedule.navigation", "schedule.heading", "academicData.navigation", "academicData.heading",
)
_KEY_SET = frozenset(TERMINOLOGY_KEYS)


class TerminologyConfigurationError(RuntimeError):
    """Raised when deployment terminology cannot safely serve the interface."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TerminologyConfigurationError(f"duplicate terminology key: {key}")
        result[key] = value
    return result


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TerminologyConfigurationError(
            f"terminology configuration cannot be read: {path}"
        ) from exc
    try:
        value = json.loads(content, object_pairs_hook=_unique_object)
    except TerminologyConfigurationError:
        raise
    except json.JSONDecodeError as exc:
        raise TerminologyConfigurationError(
            f"malformed terminology configuration: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise TerminologyConfigurationError(
            f"terminology configuration must contain one JSON object: {path}"
        )
    return value


def _validate_value(key: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TerminologyConfigurationError(f"invalid terminology value for key: {key}")
    if not value.strip() or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise TerminologyConfigurationError(f"invalid terminology value for key: {key}")
    return value


def load_effective_terminology(
    override_path: str | Path | None = None,
) -> Mapping[str, str]:
    defaults = _read_json_object(DEFAULT_TERMINOLOGY_PATH)
    if set(defaults) != _KEY_SET:
        raise TerminologyConfigurationError("shipped terminology keys are incomplete")
    effective = {key: _validate_value(key, defaults[key]) for key in TERMINOLOGY_KEYS}

    if override_path is not None:
        path = Path(override_path)
        overrides = _read_json_object(path)
        for key, value in overrides.items():
            if key not in _KEY_SET:
                raise TerminologyConfigurationError(f"unknown terminology key: {key}")
            effective[key] = _validate_value(key, value)
    return MappingProxyType(effective)


def load_terminology_from_environment() -> Mapping[str, str]:
    configured = os.getenv("CUSTOMER_TERMINOLOGY_FILE")
    return load_effective_terminology(configured if configured else None)
