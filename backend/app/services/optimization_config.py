"""Hot-read installation policy for teaching optimization; never a request override."""
import hashlib
import json
import math
import os
from pathlib import Path

from app.schemas.conflict_aware_generation import OptimizationBudgetPolicy


class OptimizationConfigurationError(ValueError):
    pass


def load_optimization_policy() -> OptimizationBudgetPolicy:
    configured_path = os.environ.get("TEACHING_OPTIMIZATION_POLICY_FILE")
    location = configured_path or "shipped defaults"

    def invalid(reason: str):
        return OptimizationConfigurationError(
            f"Optimierungskonfiguration ({location}): {reason}. "
            "Bitte die Installationsbetreuung kontaktieren und die Richtliniendatei korrigieren."
        )

    def unique_keys(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise invalid(f"duplicate key {key}")
            values[key] = value
        return values

    values = {}
    if configured_path:
        try:
            # Open anew for every preparation/start, including atomic file replacement.
            values = json.loads(Path(configured_path).read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            # Do not echo file contents, which may contain unintended secrets.
            raise invalid(f"file unreadable or malformed ({type(exc).__name__})") from exc
    if not isinstance(values, dict):
        raise invalid("expected a JSON object")
    if set(values) - {"defaultSeconds", "ceilingSeconds"}:
        raise invalid("unknown policy key; use defaultSeconds and ceilingSeconds only")

    def seconds(key: str, default: int) -> int:
        value = values.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise invalid(f"{key} must be a finite positive whole number")
        if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
            raise invalid(f"{key} must be a finite positive whole number")
        if value <= 0:
            raise invalid(f"{key} must be a finite positive whole number")
        return int(value)

    default = seconds("defaultSeconds", 300)
    ceiling = seconds("ceilingSeconds", 1800)
    if default > ceiling:
        raise invalid("defaultSeconds must not exceed ceilingSeconds")
    canonical = json.dumps({"defaultSeconds": default, "ceilingSeconds": ceiling}, sort_keys=True, separators=(",", ":"))
    return OptimizationBudgetPolicy(
        defaultSeconds=default,
        ceilingSeconds=ceiling,
        policyFingerprint=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )
