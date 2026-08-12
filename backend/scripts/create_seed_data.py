from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_ROOT / 'planner.db').as_posix()}"
DEFAULT_OUTPUT_FILE = BACKEND_ROOT / "scripts" / "planning_baseline_export.json"

if os.getenv("DATABASE_URL") in {None, "sqlite:///./planner.db"}:
    os.environ["DATABASE_URL"] = DEFAULT_DATABASE_URL

sys.path.insert(0, str(BACKEND_ROOT))

from scripts.seed_dummy_planning_data import export_current_configuration  # noqa: E402


def create_seed_data(output_file: Path) -> None:
    export_current_configuration(output_file)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create an editable JSON seed-data file from the current planning setup. "
            "Generated schedules, sessions, and generation constraints are excluded."
        )
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=(
            "JSON file to write. Use a mounted path such as /data/planning-setup.json "
            "when running inside Docker."
        ),
    )
    args = parser.parse_args()

    create_seed_data(args.output_file)


if __name__ == "__main__":
    main()
