"""Offline SQLite restore with validation, preview, and a pre-restore backup."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
import tempfile

from backup_sqlite_db import (
    DEFAULT_BACKUP_DIR,
    backup_database,
    sqlite_path_from_database_url,
)


def connect_readonly(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0)


def validate_backup(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"Backup file not found: {path}")
    with path.open("rb") as handle:
        if handle.read(16) != b"SQLite format 3\x00":
            raise ValueError("Backup is not a SQLite database.")
    connection = connect_readonly(path)
    try:
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("Backup integrity check failed.")
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
        if not {"courses", "semesters"}.issubset(tables):
            raise ValueError("Backup does not contain the planner courses/semesters tables.")
    finally:
        connection.close()


def check_target(database: Path) -> None:
    # Never mix old WAL/journal state with a restored database or delete it here.
    for suffix in ("-wal", "-shm", "-journal"):
        if Path(str(database) + suffix).exists():
            raise ValueError(
                f"SQLite sidecar exists: {database}{suffix}. Stop the backend "
                "cleanly and resolve its SQLite state before restoring. "
                "Do not delete a journal or WAL containing uncheckpointed data."
            )
    if database.exists():
        connection = sqlite3.connect(database.as_uri() + "?mode=rw", uri=True, timeout=0)
        try:
            connection.execute("BEGIN EXCLUSIVE")
            connection.rollback()
        finally:
            connection.close()


def restore_database(
    backup: Path,
    database: Path,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    *,
    apply: bool = False,
    backend_stopped: bool = False,
) -> Path | None:
    backup, database, backup_dir = backup.resolve(), database.resolve(), backup_dir.resolve()
    validate_backup(backup)
    if backup == database or (database.exists() and os.path.samefile(backup, database)):
        raise ValueError("Backup source and target database must be different files.")
    if not database.parent.is_dir():
        raise ValueError(f"Target directory does not exist: {database.parent}")
    if not apply:
        return None
    if not backend_stopped:
        raise ValueError("Stop the backend first, then specify --backend-stopped with --apply.")
    check_target(database)

    # Build a standalone candidate first. SQLite's backup API includes any
    # committed source WAL data without copying its sidecar files.
    descriptor, staged_name = tempfile.mkstemp(prefix=".planner-restore-", suffix=".db", dir=database.parent)
    os.close(descriptor)
    staged = Path(staged_name)
    try:
        source = connect_readonly(backup)
        destination = sqlite3.connect(staged)
        try:
            source.backup(destination)
        finally:
            destination.close()
            source.close()
        validate_backup(staged)
        previous_backup = None
        if database.exists():
            # A unique directory prevents overwriting any timestamped backup,
            # including repeated restores within the same second.
            backup_dir.mkdir(parents=True, exist_ok=True)
            safety_dir = Path(tempfile.mkdtemp(prefix="before-restore-", dir=backup_dir))
            previous_backup = backup_database(database, safety_dir)
            staged.chmod(database.stat().st_mode)
        check_target(database)
        os.replace(staged, database)
        return previous_backup
    finally:
        staged.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path, required=True, help="Planner SQLite backup to restore.")
    parser.add_argument("--database", type=Path, help="Defaults to DATABASE_URL or backend/planner.db.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR,
                        help="Pre-restore backup parent directory (default: backend/backups).")
    parser.add_argument("--apply", action="store_true", help="Restore; without this flag only validate and preview.")
    parser.add_argument("--backend-stopped", action="store_true",
                        help="Confirm all processes using the target database are stopped.")
    args = parser.parse_args()
    try:
        target = (args.database or sqlite_path_from_database_url(os.getenv("DATABASE_URL"))).resolve()
        previous = restore_database(args.backup, target, args.backup_dir,
                                    apply=args.apply, backend_stopped=args.backend_stopped)
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, f"Restore failed: {exc}\n")
    print(f"Backup: {args.backup.resolve()}")
    print(f"Target: {target}")
    if args.apply:
        if previous:
            print(f"Previous database backed up: {previous}")
        print("Restore completed. Start the backend and check the application.")
    else:
        print("Preview only. No files changed. Stop the backend, then add --apply --backend-stopped.")


if __name__ == "__main__":
    main()
