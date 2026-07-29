from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = BACKEND_ROOT / "planner.db"
DEFAULT_BACKUP_DIR = BACKEND_ROOT / "backups"


def sqlite_path_from_database_url(database_url: str | None) -> Path:
    if not database_url:
        return DEFAULT_DATABASE

    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError(
            "Only SQLite DATABASE_URL values are supported by this backup script."
        )

    if database_url in {"sqlite://", "sqlite:///:memory:", "sqlite:///:memory"}:
        raise ValueError("In-memory SQLite databases cannot be backed up to a file.")

    if parsed.path.startswith("/") and len(parsed.path) >= 3 and parsed.path[2] == ":":
        return Path(unquote(parsed.path.lstrip("/")))

    if parsed.path.startswith("//"):
        return Path(unquote(parsed.path))

    path = unquote(parsed.path.lstrip("/"))
    if not path:
        raise ValueError(f"Could not determine database file from {database_url!r}.")

    database_path = Path(path)
    if database_path.is_absolute():
        return database_path
    return Path.cwd() / database_path


def backup_database(source: Path, backup_dir: Path) -> Path:
    source = source.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        raise FileNotFoundError(f"Database file does not exist: {source}")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"{source.stem}-{timestamp}{source.suffix}"

    with sqlite3.connect(source) as source_connection:
        with sqlite3.connect(target) as target_connection:
            source_connection.backup(target_connection)

    with sqlite3.connect(target) as backup_connection:
        result = backup_connection.execute("PRAGMA integrity_check").fetchone()
        if result is None or result[0] != "ok":
            target.unlink(missing_ok=True)
            raise RuntimeError(f"Backup integrity check failed: {result}")

    return target


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a consistent backup of the local SQLite planner database."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="SQLite database file to back up. Defaults to DATABASE_URL or backend/planner.db.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Directory for backup files. Defaults to backend/backups.",
    )
    args = parser.parse_args()

    source = args.database or sqlite_path_from_database_url(os.getenv("DATABASE_URL"))
    backup_path = backup_database(source, args.output_dir)
    print(f"Backup created: {backup_path}")


if __name__ == "__main__":
    main()
