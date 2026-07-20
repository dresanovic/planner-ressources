import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Engine, event, inspect

from app.db.base import Base
from app.models import planning as _planning  # noqa: F401 - registers model metadata


class UnsupportedSchemaStateError(RuntimeError):
    pass


def initialize_database(engine: Engine) -> None:
    """Create a new schema or upgrade supported planner schemas sequentially."""
    with engine.connect() as connection:
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
        with connection.begin():
            inspector = inspect(connection)
            if not inspector.get_table_names():
                Base.metadata.create_all(bind=connection)
                inspector = inspect(connection)
            elif not _is_current_schema(inspector):
                if _is_slice_1_to_5_schema(inspector):
                    migration = _load_migration("0002_course_semester_drafts.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()
                    inspector = inspect(connection)
                if _is_slice_6_schema(inspector):
                    migration = _load_migration("0003_academic_catalog_administration.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()
                    inspector = inspect(connection)
                if _is_slice_7_schema(inspector):
                    migration = _load_migration("0004_resource_eligibility_availability.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()
                    inspector = inspect(connection)
                if _is_pre_exam_schema(inspector):
                    migration = _load_migration("0006_conflict_aware_exam_scheduling.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()
                    inspector = inspect(connection)
                elif not _is_pre_holiday_schema(inspector):
                    raise UnsupportedSchemaStateError(
                        "Database schema is not a supported FS-001 through FS-010 state. "
                        "Back up the database and inspect its migration state."
                    )

                if not _is_pre_exam_schema(inspector) and "institution_holidays" not in inspector.get_table_names():
                    migration = _load_migration("0005_institution_holidays.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()
                    inspector = inspect(connection)
                if _is_pre_exam_schema(inspector):
                    migration = _load_migration("0006_conflict_aware_exam_scheduling.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()

                if not _is_current_schema(inspect(connection)):
                    raise UnsupportedSchemaStateError(
                        "FS-012 database migration completed without producing the expected schema."
                    )
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()
    _configure_sqlite_foreign_keys(engine)


def _is_current_schema(inspector) -> bool:
    return (
        _has_holiday_schema(inspector)
        and {"course_exam_configurations", "exam_sessions"}.issubset(inspector.get_table_names())
        and {"course_id", "semester_id", "enabled", "revision"}.issubset(_column_names(inspector, "course_exam_configurations"))
        and {"exam_date", "start_time", "end_time", "source", "revision", "final_teaching_session_id_snapshot"}.issubset(_column_names(inspector, "exam_sessions"))
        and _has_unique_columns(inspector, "course_exam_configurations", ("course_id", "semester_id"))
    )


def _is_pre_exam_schema(inspector) -> bool:
    return (
        _has_holiday_schema(inspector)
        and "course_exam_configurations" not in inspector.get_table_names()
        and "exam_sessions" not in inspector.get_table_names()
    )


def _has_holiday_schema(inspector) -> bool:
    return (
        _is_pre_holiday_schema(inspector)
        and "institution_holidays" in inspector.get_table_names()
        and {"id", "date", "name", "revision"}.issubset(
            _column_names(inspector, "institution_holidays")
        )
        and _has_unique_columns(inspector, "institution_holidays", ("date",))
    )


def _is_pre_holiday_schema(inspector) -> bool:
    tables = set(inspector.get_table_names())
    required_tables = {
        "course_eligible_lecturers",
        "course_eligible_rooms",
        "resource_unavailability_periods",
        "resource_unavailability_weekdays",
    }
    lecturer_columns = _column_names(inspector, "lecturers")
    room_columns = _column_names(inspector, "rooms")
    course_columns = _column_names(inspector, "courses")
    draft_columns = _column_names(inspector, "draft_schedules")
    constraint_columns = _column_names(inspector, "generation_constraint_sets")
    return (
        required_tables.issubset(tables)
        and {"reference_code", "normalized_reference_code", "is_active", "revision"}.issubset(
            lecturer_columns
        )
        and {"reference_code", "normalized_reference_code", "is_active", "revision"}.issubset(
            room_columns
        )
        and "lecturer_id" not in course_columns
        and "room_id" not in course_columns
        and "revision" in draft_columns
        and "revision" in constraint_columns
        and "current_semester_id" in course_columns
        and "course_name_snapshot" in draft_columns
        and _has_unique_columns(
            inspector,
            "draft_schedules",
            ("course_id", "semester_id"),
        )
        and not _has_unique_columns(inspector, "draft_schedules", ("course_id",))
    )


def _is_slice_7_schema(inspector) -> bool:
    course_columns = _column_names(inspector, "courses")
    draft_columns = _column_names(inspector, "draft_schedules")
    constraint_columns = _column_names(inspector, "generation_constraint_sets")
    return (
        "lecturer_id" in course_columns
        and "room_id" in course_columns
        and "current_semester_id" in course_columns
        and "reference_code" not in _column_names(inspector, "lecturers")
        and "reference_code" not in _column_names(inspector, "rooms")
        and "revision" in draft_columns
        and "revision" in constraint_columns
        and "course_name_snapshot" in draft_columns
    )


def _is_slice_6_schema(inspector) -> bool:
    draft_columns = _column_names(inspector, "draft_schedules")
    constraint_columns = _column_names(inspector, "generation_constraint_sets")
    return (
        "revision" in draft_columns
        and "course_name_snapshot" not in draft_columns
        and "revision" in constraint_columns
        and "current_semester_id" not in _column_names(inspector, "courses")
        and _has_unique_columns(inspector, "draft_schedules", ("course_id", "semester_id"))
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


def _configure_sqlite_foreign_keys(engine: Engine) -> None:
    if engine.dialect.name != "sqlite" or getattr(engine, "_fs007_fk_listener", False):
        return

    def enable(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(engine, "connect", enable)
    setattr(engine, "_fs007_fk_listener", True)
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
