import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool


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


def _columns_by_name(inspector, table_name: str):
    return {column["name"]: column for column in inspector.get_columns(table_name)}
