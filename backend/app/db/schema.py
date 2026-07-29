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
                if _is_pre_lecturer_review_schema(inspector):
                    migration = _load_migration("0009_lecturer_token_review.py")
                    migration.op = Operations(MigrationContext.configure(connection))
                    migration.upgrade()
                    inspector = inspect(connection)
                elif _has_any_lecturer_review_table(inspector):
                    raise UnsupportedSchemaStateError(
                        "Database schema is not a supported FS-001 through FS-012 state "
                        "or a complete FS-015 state. Back up the database and inspect "
                        "its lifecycle and lecturer review tables."
                    )
                else:
                    if _is_pre_calendar_workspace_schema(inspector):
                        migration = _load_migration("0008_calendar_workspace_outcomes.py")
                        migration.op = Operations(MigrationContext.configure(connection))
                        migration.upgrade()
                        inspector = inspect(connection)
                    elif _has_any_lifecycle_table(inspector):
                        raise UnsupportedSchemaStateError(
                            "Database schema is not a supported FS-001 through FS-012 state or a complete FS-013 state. "
                            "Back up the database and inspect its lifecycle tables."
                        )
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

                    inspector = inspect(connection)
                    if _is_pre_lifecycle_schema(inspector):
                        migration = _load_migration("0007_versioned_schedule_lifecycle.py")
                        migration.op = Operations(MigrationContext.configure(connection))
                        migration.upgrade()
                        inspector = inspect(connection)

                    if _is_pre_calendar_workspace_schema(inspector):
                        migration = _load_migration("0008_calendar_workspace_outcomes.py")
                        migration.op = Operations(MigrationContext.configure(connection))
                        migration.upgrade()
                        inspector = inspect(connection)

                    if _is_pre_lecturer_review_schema(inspector):
                        migration = _load_migration("0009_lecturer_token_review.py")
                        migration.op = Operations(MigrationContext.configure(connection))
                        migration.upgrade()

                if not _is_current_schema(inspect(connection)):
                    raise UnsupportedSchemaStateError(
                        "FS-015 database migration completed without producing the expected schema."
                    )
        if engine.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()
    _configure_sqlite_foreign_keys(engine)


def _is_current_schema(inspector) -> bool:
    tables = set(inspector.get_table_names())
    return (
        _has_complete_calendar_workspace_schema(inspector)
        and {
            "lecturer_review_links",
            "lecturer_review_feedback",
            "lecturer_review_activity_events",
            "lecturer_review_invalid_source_states",
        }.issubset(tables)
        and {
            "schedule_revision_id",
            "lecturer_id",
            "intended_lecturer_name",
            "secret_digest",
            "duration_days",
            "issued_at",
            "expires_at",
            "status",
            "ended_at",
            "end_reason",
            "replaced_by_id",
            "access_blocked_until",
        }.issubset(_column_names(inspector, "lecturer_review_links"))
        and {
            "review_link_id",
            "kind",
            "session_kind",
            "source_session_id",
            "comment_text",
            "session_context",
            "client_submission_id",
            "request_fingerprint",
            "submitted_at",
        }.issubset(_column_names(inspector, "lecturer_review_feedback"))
        and {
            "event_type",
            "review_link_id",
            "schedule_revision_id",
            "lecturer_id",
            "feedback_id",
            "reason_code",
            "occurred_at",
        }.issubset(_column_names(inspector, "lecturer_review_activity_events"))
        and {
            "source_fingerprint",
            "attempt_timestamps",
            "blocked_until",
            "last_relevant_at",
        }.issubset(
            _column_names(inspector, "lecturer_review_invalid_source_states")
        )
        and _has_unique_columns(
            inspector,
            "lecturer_review_links",
            ("secret_digest",),
        )
        and _has_unique_columns(
            inspector,
            "lecturer_review_feedback",
            ("review_link_id", "client_submission_id"),
        )
        and _has_unique_index(
            inspector,
            "lecturer_review_links",
            "uq_lecturer_review_link_active_pair",
            ("schedule_revision_id", "lecturer_id"),
        )
        and _has_index(
            inspector,
            "lecturer_review_invalid_source_states",
            "ix_lecturer_review_invalid_source_cleanup",
            ("last_relevant_at",),
        )
    )


def _is_pre_lecturer_review_schema(inspector) -> bool:
    return (
        _has_complete_calendar_workspace_schema(inspector)
        and not _has_any_lecturer_review_table(inspector)
    )


def _has_complete_calendar_workspace_schema(inspector) -> bool:
    tables = set(inspector.get_table_names())
    return (
        _has_complete_lifecycle_schema(inspector)
        and "planning_outcomes" in tables
        and {
            "schedule_revision_id",
            "course_id",
            "operation_kind",
            "classification",
            "source_status",
            "result_payload",
            "completed_at",
        }.issubset(_column_names(inspector, "planning_outcomes"))
        and _has_unique_columns(
            inspector,
            "planning_outcomes",
            ("schedule_revision_id", "course_id", "operation_kind"),
        )
    )


def _has_any_lecturer_review_table(inspector) -> bool:
    return bool(
        {
            "lecturer_review_links",
            "lecturer_review_feedback",
            "lecturer_review_activity_events",
            "lecturer_review_invalid_source_states",
        }
        & set(inspector.get_table_names())
    )


def _is_pre_calendar_workspace_schema(inspector) -> bool:
    tables = set(inspector.get_table_names())
    return (
        _has_complete_lifecycle_schema(inspector)
        and "planning_outcomes" not in tables
    )


def _has_complete_lifecycle_schema(inspector) -> bool:
    tables = set(inspector.get_table_names())
    return (
        _is_pre_lifecycle_schema(inspector)
        and {"schedule_revisions", "schedule_revision_events"}.issubset(tables)
        and {
            "semester_id",
            "revision_number",
            "state",
            "row_version",
            "snapshot_document",
            "created_at",
            "state_changed_at",
            "published_at",
        }.issubset(_column_names(inspector, "schedule_revisions"))
        and {
            "semester_id",
            "schedule_revision_id",
            "event_sequence",
            "event_type",
            "from_state",
            "to_state",
            "occurred_at",
        }.issubset(_column_names(inspector, "schedule_revision_events"))
        and _has_unique_columns(
            inspector, "schedule_revisions", ("semester_id", "revision_number")
        )
        and _has_unique_columns(
            inspector,
            "schedule_revision_events",
            ("semester_id", "event_sequence"),
        )
    )


def _is_pre_lifecycle_schema(inspector) -> bool:
    return (
        _has_holiday_schema(inspector)
        and {"course_exam_configurations", "exam_sessions"}.issubset(inspector.get_table_names())
        and {"course_id", "semester_id", "enabled", "revision"}.issubset(_column_names(inspector, "course_exam_configurations"))
        and {"exam_date", "start_time", "end_time", "source", "revision", "final_teaching_session_id_snapshot"}.issubset(_column_names(inspector, "exam_sessions"))
        and _has_unique_columns(inspector, "course_exam_configurations", ("course_id", "semester_id"))
    )


def _has_any_lifecycle_table(inspector) -> bool:
    return bool(
        {"schedule_revisions", "schedule_revision_events"}
        & set(inspector.get_table_names())
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


def _has_unique_index(
    inspector,
    table_name: str,
    name: str,
    columns: tuple[str, ...],
) -> bool:
    return any(
        item.get("name") == name
        and bool(item.get("unique"))
        and tuple(item.get("column_names") or []) == columns
        for item in inspector.get_indexes(table_name)
    )


def _has_index(
    inspector,
    table_name: str,
    name: str,
    columns: tuple[str, ...],
) -> bool:
    return any(
        item.get("name") == name
        and tuple(item.get("column_names") or []) == columns
        for item in inspector.get_indexes(table_name)
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
