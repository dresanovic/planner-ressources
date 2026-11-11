"""Hot-read installation policy for teaching optimization; never a request override."""
import hashlib
import json
import math
import os
from pathlib import Path

from app.schemas.conflict_aware_generation import OptimizationBudgetPolicy


DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[3] / 'config' / 'optimization' / 'policy.json'
SETTINGS_VERSION = 'teaching-v1'


def strategy_settings(algorithm: str) -> dict:
    if algorithm == 'standard_optimized':
        from app.services.standard_optimized import STAGE_WEIGHTS
        return {'version': 'standard-optimized-v1', 'weeklySpread': 'cumulative-feasible-weeks-v1',
            'stageBudgetWeights': list(STAGE_WEIGHTS)}
    return ({'version': SETTINGS_VERSION} if algorithm == 'standard' else {
        'version': SETTINGS_VERSION, 'repairAlternatives': 1000,
        'maxDisplacedSessions': 8, 'checkpointSeconds': 5,
    })


class OptimizationConfigurationError(ValueError):
    pass


def load_optimization_policy() -> OptimizationBudgetPolicy:
    configured_path = os.environ.get("TEACHING_OPTIMIZATION_POLICY_FILE")
    location = Path(configured_path) if configured_path is not None else DEFAULT_POLICY_PATH

    def invalid(reason: str):
        return OptimizationConfigurationError(
            f"Optimierungskonfiguration ({location}): {reason}. "
            "Bitte die Installationsbetreuung kontaktieren und die Richtliniendatei an diesem Ort bereitstellen oder korrigieren."
        )

    def unique_keys(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise invalid(f"duplicate key {key}")
            values[key] = value
        return values

    try:
        # Open anew for every preparation/start, including atomic file replacement.
        values = json.loads(location.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        # Do not echo file contents, which may contain unintended secrets.
        raise invalid(f"Datei nicht lesbar oder ungültig ({type(exc).__name__})") from exc
    if not isinstance(values, dict):
        raise invalid("expected a JSON object")
    if set(values) - {"defaultSeconds", "ceilingSeconds", "activeAlgorithm"}:
        raise invalid("unknown policy key; use defaultSeconds, ceilingSeconds and activeAlgorithm only")
    algorithm = values.get('activeAlgorithm', 'standard')
    if not isinstance(algorithm, str) or algorithm not in ('standard', 'cohort', 'lecturer', 'standard_optimized'):
        raise invalid('activeAlgorithm muss standard, standard_optimized, cohort oder lecturer sein')

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
    profile = {'standard': 'standard-v1', 'standard_optimized': 'standard-optimized-v1'}.get(algorithm, 'heuristic-v1')
    settings = strategy_settings(algorithm)
    canonical = json.dumps({'activeAlgorithm': algorithm, 'strategyProfile': profile,
        'strategySettings': settings, "defaultSeconds": default, "ceilingSeconds": ceiling},
        sort_keys=True, separators=(",", ":"))
    return OptimizationBudgetPolicy(
        defaultSeconds=default,
        ceilingSeconds=ceiling,
        activeAlgorithm=algorithm, strategyProfile=profile, strategySettings=settings,
        policyFingerprint=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    )
