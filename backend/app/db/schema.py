import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Engine, inspect

from app.db.base import Base
from app.models import planning as _planning  # noqa: F401 - registers model metadata


class UnsupportedSchemaStateError(RuntimeError):
    pass


def initialize_database(engine: Engine) -> None:
    """Create a new schema or upgrade the supported pre-Slice-6 schema in place."""
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        inspector = inspect(connection)
        if _is_current_schema(inspector):
            return
        if not _is_slice_1_to_5_schema(inspector):
            raise UnsupportedSchemaStateError(
                "Database schema is neither the pre-Slice-6 schema nor the current schema. "
                "Back up the database and inspect its Draft Schedule migration state."
            )

        migration = _load_migration("0002_course_semester_drafts.py")
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        if not _is_current_schema(inspect(connection)):
            raise UnsupportedSchemaStateError(
                "Slice 6 database migration completed without producing the expected schema."
            )


def _is_current_schema(inspector) -> bool:
    draft_columns = _column_names(inspector, "draft_schedules")
    constraint_columns = _column_names(inspector, "generation_constraint_sets")
    return (
        "revision" in draft_columns
        and "revision" in constraint_columns
        and _has_unique_columns(
            inspector,
            "draft_schedules",
            ("course_id", "semester_id"),
        )
        and not _has_unique_columns(inspector, "draft_schedules", ("course_id",))
    )


def _is_slice_1_to_5_schema(inspector) -> bool:
    tables = set(inspector.get_table_names())
    if not {"draft_schedules", "generation_constraint_sets"}.issubset(tables):
        return False
    return (
        "revision" not in _column_names(inspector, "draft_schedules")
        and "revision" not in _column_names(inspector, "generation_constraint_sets")
        and _has_unique_columns(inspector, "draft_schedules", ("course_id",))
        and not _has_unique_columns(
            inspector,
            "draft_schedules",
            ("course_id", "semester_id"),
        )
    )


def _column_names(inspector, table_name: str) -> set[str]:
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _has_unique_columns(inspector, table_name: str, columns: tuple[str, ...]) -> bool:
    expected = set(columns)
    return any(
        set(constraint.get("column_names") or []) == expected
        for constraint in inspector.get_unique_constraints(table_name)
    )


def _load_migration(filename: str):
    path = Path(__file__).resolve().parent / "migrations" / filename
    spec = importlib.util.spec_from_file_location("runtime_course_semester_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load database migration: {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
