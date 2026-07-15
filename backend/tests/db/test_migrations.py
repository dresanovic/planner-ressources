import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database


def test_initial_migration_matches_current_persistence_columns():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    migration = _load_initial_migration()

    with engine.begin() as connection:
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        inspector = inspect(connection)
        draft_schedule_columns = _columns_by_name(inspector, "draft_schedules")
        draft_session_columns = _columns_by_name(inspector, "draft_sessions")

        assert draft_schedule_columns["selected_time_window_id"]["nullable"] is True
        assert draft_session_columns["time_window_id"]["nullable"] is True
        assert "constraint_window_index" in draft_session_columns
        assert draft_session_columns["constraint_window_index"]["nullable"] is False
        assert "generation_constraint_sets" in inspector.get_table_names()
        assert "generation_constraint_windows" in inspector.get_table_names()


def test_second_migration_preserves_rows_backfills_revisions_and_allows_cross_semester_drafts():
    engine = create_engine("sqlite://")
    first = _load_initial_migration()
    second = _load_migration("0002_course_semester_drafts.py", "course_semester_migration")

    with engine.begin() as connection:
        first.op = Operations(MigrationContext.configure(connection))
        first.upgrade()
        connection.execute(text("INSERT INTO lecturers VALUES (1, 'L')"))
        connection.execute(text("INSERT INTO cohorts VALUES (1, 'C', 10)"))
        connection.execute(text("INSERT INTO rooms VALUES (1, 'R', 20)"))
        connection.execute(text("INSERT INTO semesters VALUES (1, 'Fall', '2026-09-01', '2026-12-20')"))
        connection.execute(text("INSERT INTO semesters VALUES (2, 'Spring', '2027-02-01', '2027-06-20')"))
        connection.execute(text("INSERT INTO study_types VALUES (1, 'Full-time')"))
        connection.execute(text("INSERT INTO courses VALUES (1, 'Course', 4, 2, 4, 1, 1, 1, 1)"))
        connection.execute(text("INSERT INTO draft_schedules VALUES (1, 1, 1, NULL, 'generated', CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO generation_constraint_sets VALUES (1, 1, 1, '2026-09-01', '2026-12-20', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))

        second.op = Operations(MigrationContext.configure(connection))
        second.upgrade()

        assert connection.execute(text("SELECT revision FROM draft_schedules WHERE id=1")).scalar_one() == 1
        assert connection.execute(text("SELECT revision FROM generation_constraint_sets WHERE id=1")).scalar_one() == 1
        connection.execute(text("INSERT INTO draft_schedules (id, course_id, semester_id, status, created_at, revision) VALUES (2, 1, 2, 'generated', CURRENT_TIMESTAMP, 1)"))
        with pytest.raises(Exception):
            connection.execute(text("INSERT INTO draft_schedules (id, course_id, semester_id, status, created_at, revision) VALUES (3, 1, 2, 'generated', CURRENT_TIMESTAMP, 1)"))


def test_startup_initialization_upgrades_legacy_database_and_is_idempotent():
    engine = create_engine("sqlite://")
    first = _load_initial_migration()

    with engine.begin() as connection:
        first.op = Operations(MigrationContext.configure(connection))
        first.upgrade()
        connection.execute(text("INSERT INTO lecturers VALUES (1, 'L')"))
        connection.execute(text("INSERT INTO cohorts VALUES (1, 'C', 10)"))
        connection.execute(text("INSERT INTO rooms VALUES (1, 'R', 20)"))
        connection.execute(text("INSERT INTO semesters VALUES (1, 'Fall', '2026-09-01', '2026-12-20')"))
        connection.execute(text("INSERT INTO study_types VALUES (1, 'Full-time')"))
        connection.execute(text("INSERT INTO courses VALUES (1, 'Course', 4, 2, 4, 1, 1, 1, 1)"))
        connection.execute(text("INSERT INTO draft_schedules VALUES (1, 1, 1, NULL, 'generated', CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO generation_constraint_sets VALUES (1, 1, 1, '2026-09-01', '2026-12-20', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))

    initialize_database(engine)
    initialize_database(engine)

    with engine.connect() as connection:
        inspector = inspect(connection)
        assert _columns_by_name(inspector, "draft_schedules")["revision"]["nullable"] is False
        assert _columns_by_name(inspector, "generation_constraint_sets")["revision"]["nullable"] is False
        assert connection.execute(text("SELECT revision FROM draft_schedules WHERE id=1")).scalar_one() == 1
        assert connection.execute(text("SELECT revision FROM generation_constraint_sets WHERE id=1")).scalar_one() == 1


def test_third_migration_preserves_legacy_conflicts_assignments_and_snapshots():
    engine = create_engine("sqlite://")
    first = _load_initial_migration()
    second = _load_migration("0002_course_semester_drafts.py", "course_semester_migration_for_admin")
    third = _load_migration("0003_academic_catalog_administration.py", "academic_admin_migration")

    with engine.begin() as connection:
        first.op = Operations(MigrationContext.configure(connection))
        first.upgrade()
        connection.execute(text("INSERT INTO lecturers VALUES (1, 'L')"))
        connection.execute(text("INSERT INTO cohorts VALUES (1, 'AI 1', 10), (2, ' ai 1 ', 20)"))
        connection.execute(text("INSERT INTO rooms VALUES (1, 'R', 30)"))
        connection.execute(text("INSERT INTO semesters VALUES (1, 'Fall', '2026-09-01', '2026-12-20')"))
        connection.execute(text("INSERT INTO study_types VALUES (1, 'Full-time')"))
        connection.execute(text("INSERT INTO courses VALUES (1, 'Course', 4, 2, 4, 1, 1, 1, 1)"))
        connection.execute(text("INSERT INTO draft_schedules VALUES (1, 1, 1, NULL, 'generated', CURRENT_TIMESTAMP)"))
        second.op = Operations(MigrationContext.configure(connection))
        second.upgrade()

        third.op = Operations(MigrationContext.configure(connection))
        third.upgrade()

        cohort_rows = connection.execute(
            text("SELECT normalized_name, name_repair_required, normalized_name_key FROM cohorts ORDER BY id")
        ).all()
        assert [row.name_repair_required for row in cohort_rows] == [1, 1]
        assert [row.normalized_name for row in cohort_rows] == [None, None]
        assert len({row.normalized_name_key for row in cohort_rows}) == 2
        assert connection.execute(text("SELECT current_semester_id FROM courses WHERE id=1")).scalar_one() == 1
        snapshot = connection.execute(
            text("SELECT course_name_snapshot, cohort_name_snapshot, study_type_name_snapshot, semester_name_snapshot FROM draft_schedules WHERE id=1")
        ).one()
        assert tuple(snapshot) == ("Course", "AI 1", "Full-time", "Fall")


def test_current_schema_enables_sqlite_foreign_keys_and_exact_window_uniqueness():
    engine = create_engine("sqlite://")
    initialize_database(engine)

    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
        inspector = inspect(connection)
        assert "current_semester_id" in _columns_by_name(inspector, "courses")
        assert "course_name_snapshot" in _columns_by_name(inspector, "draft_schedules")
        unique_sets = {
            tuple(item.get("column_names") or [])
            for item in inspector.get_unique_constraints("study_type_time_windows")
        }
        assert ("study_type_id", "weekday", "start_time", "end_time") in unique_sets


def _load_initial_migration():
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "db"
        / "migrations"
        / "0001_create_planning_tables.py"
    )
    spec = importlib.util.spec_from_file_location("initial_planning_migration", migration_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_migration(filename: str, module_name: str):
    migration_path = Path(__file__).resolve().parents[2] / "app" / "db" / "migrations" / filename
    spec = importlib.util.spec_from_file_location(module_name, migration_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _columns_by_name(inspector, table_name: str):
    return {column["name"]: column for column in inspector.get_columns(table_name)}
