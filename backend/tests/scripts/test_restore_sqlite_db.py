import sqlite3
import sys
import tempfile
from pathlib import Path
import unittest
from contextlib import closing

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from restore_sqlite_db import restore_database


def create_database(path, value):
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE courses (name TEXT)")
        connection.execute("CREATE TABLE semesters (name TEXT)")
        connection.execute("INSERT INTO courses VALUES (?)", (value,))


def course_name(path):
    connection = sqlite3.connect(path)
    try:
        return connection.execute("SELECT name FROM courses").fetchone()[0]
    finally:
        connection.close()


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.backup = self.root / "backup.db"
        self.target = self.root / "planner.db"
        self.safety = self.root / "backups"
        create_database(self.backup, "server")
        create_database(self.target, "local")

    def restore(self, **kwargs):
        return restore_database(self.backup, self.target, self.safety, **kwargs)

    def test_preview_creates_no_files_and_preserves_target(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        self.restore()
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_restore_preserves_source_and_previous_database(self):
        original = self.backup.read_bytes()
        previous = self.restore(apply=True, backend_stopped=True)
        self.assertEqual(course_name(self.target), "server")
        self.assertEqual(course_name(previous), "local")
        self.assertEqual(self.backup.read_bytes(), original)
        second = self.restore(apply=True, backend_stopped=True)
        self.assertNotEqual(previous, second)
        self.assertEqual(course_name(previous), "local")
        self.assertEqual(course_name(second), "server")

    def test_corrupt_or_unrelated_backup_does_not_touch_target(self):
        original = self.target.read_bytes()
        for content in (b"", b"not sqlite", b"SQLite format 3\x00broken"):
            self.backup.write_bytes(content)
            with self.assertRaises((ValueError, sqlite3.Error)):
                self.restore(apply=True, backend_stopped=True)
            self.assertEqual(self.target.read_bytes(), original)
        self.backup.unlink()
        with closing(sqlite3.connect(self.backup)) as connection, connection:
            connection.execute("CREATE TABLE unrelated (id INTEGER)")
        with self.assertRaisesRegex(ValueError, "planner"):
            self.restore(apply=True, backend_stopped=True)
        self.assertFalse(self.safety.exists())

    def test_apply_requires_stopped_confirmation(self):
        with self.assertRaisesRegex(ValueError, "backend-stopped"):
            self.restore(apply=True)
        self.assertEqual(course_name(self.target), "local")

    def test_same_file_rejected(self):
        with self.assertRaisesRegex(ValueError, "different files"):
            restore_database(self.target, self.target, apply=True, backend_stopped=True)

    def test_sidecars_are_preserved_and_restore_refused(self):
        for suffix in ("-wal", "-shm", "-journal"):
            with self.subTest(suffix=suffix):
                sidecar = Path(str(self.target) + suffix)
                sidecar.write_bytes(b"preserve")
                with self.assertRaisesRegex(ValueError, "sidecar"):
                    self.restore(apply=True, backend_stopped=True)
                self.assertEqual(sidecar.read_bytes(), b"preserve")
                sidecar.unlink()
        self.assertEqual(course_name(self.target), "local")

    def test_locked_target_is_not_replaced(self):
        connection = sqlite3.connect(self.target)
        try:
            connection.execute("BEGIN EXCLUSIVE")
            with self.assertRaises(sqlite3.OperationalError):
                self.restore(apply=True, backend_stopped=True)
        finally:
            connection.rollback()
            connection.close()
        self.assertEqual(course_name(self.target), "local")

    def test_restore_to_missing_target(self):
        self.target.unlink()
        self.assertIsNone(self.restore(apply=True, backend_stopped=True))
        self.assertEqual(course_name(self.target), "server")


if __name__ == "__main__":
    unittest.main()
