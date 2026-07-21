import importlib.util
from datetime import date, time
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    DraftSession,
    Lecturer,
    Room,
    Semester,
    StudyType,
)


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


def test_clean_create_exposes_resource_eligibility_and_unavailability_schema():
    engine = create_engine("sqlite://")

    initialize_database(engine)

    with engine.connect() as connection:
        inspector = inspect(connection)
        assert {
            "course_eligible_lecturers",
            "course_eligible_rooms",
            "resource_unavailability_periods",
            "resource_unavailability_weekdays",
        }.issubset(inspector.get_table_names())
        lecturer_columns = _columns_by_name(inspector, "lecturers")
        room_columns = _columns_by_name(inspector, "rooms")
        course_columns = _columns_by_name(inspector, "courses")
        for columns in (lecturer_columns, room_columns):
            assert {
                "reference_code",
                "normalized_reference_code",
                "is_active",
                "revision",
            }.issubset(columns)
        assert "lecturer_id" not in course_columns
        assert "room_id" not in course_columns
        assert {"course_id", "lecturer_id"} == set(
            _columns_by_name(inspector, "course_eligible_lecturers")
        )
        assert {"course_id", "room_id"} == set(
            _columns_by_name(inspector, "course_eligible_rooms")
        )


def test_fourth_migration_backfills_codes_eligibility_and_preserves_session_assignments():
    engine = create_engine("sqlite://")
    first = _load_initial_migration()
    second = _load_migration("0002_course_semester_drafts.py", "course_semester_for_resources")
    third = _load_migration("0003_academic_catalog_administration.py", "catalog_for_resources")
    fourth = _load_migration("0004_resource_eligibility_availability.py", "resource_eligibility")

    with engine.begin() as connection:
        first.op = Operations(MigrationContext.configure(connection))
        first.upgrade()
        connection.execute(text("INSERT INTO lecturers VALUES (7, 'Lecturer')"))
        connection.execute(text("INSERT INTO cohorts VALUES (1, 'Cohort', 10)"))
        connection.execute(text("INSERT INTO rooms VALUES (9, 'Room', 20)"))
        connection.execute(text("INSERT INTO semesters VALUES (1, 'Fall', '2026-09-01', '2026-12-20')"))
        connection.execute(text("INSERT INTO study_types VALUES (1, 'Full-time')"))
        connection.execute(text("INSERT INTO courses VALUES (1, 'Course', 4, 2, 4, 7, 1, 9, 1)"))
        connection.execute(text("INSERT INTO draft_schedules VALUES (1, 1, 1, NULL, 'generated', CURRENT_TIMESTAMP)"))
        connection.execute(
            text(
                "INSERT INTO draft_sessions "
                "(id, draft_schedule_id, course_id, lecturer_id, cohort_id, room_id, date, start_time, end_time, units, time_window_id, constraint_window_index) "
                "VALUES (1, 1, 1, 7, 1, 9, '2026-09-07', '08:00:00', '10:00:00', 2, NULL, 0)"
            )
        )
        second.op = Operations(MigrationContext.configure(connection))
        second.upgrade()
        third.op = Operations(MigrationContext.configure(connection))
        third.upgrade()

        fourth.op = Operations(MigrationContext.configure(connection))
        fourth.upgrade()

        inspector = inspect(connection)
        assert tuple(
            connection.execute(
                text("SELECT reference_code, normalized_reference_code, is_active, revision FROM lecturers WHERE id=7")
            ).one()
        ) == ("LECT-7", "lect-7", 1, 1)
        assert tuple(
            connection.execute(
                text("SELECT reference_code, normalized_reference_code, is_active, revision FROM rooms WHERE id=9")
            ).one()
        ) == ("ROOM-9", "room-9", 1, 1)
        assert connection.execute(text("SELECT course_id, lecturer_id FROM course_eligible_lecturers")).one() == (1, 7)
        assert connection.execute(text("SELECT course_id, room_id FROM course_eligible_rooms")).one() == (1, 9)
        assert "lecturer_id" not in _columns_by_name(inspector, "courses")
        assert "room_id" not in _columns_by_name(inspector, "courses")
        assert connection.execute(
            text("SELECT lecturer_id, room_id FROM draft_sessions WHERE id=1")
        ).one() == (7, 9)


def test_fourth_migration_downgrade_restores_resources_and_preserves_drafts_with_foreign_keys_enabled():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    _seed_current_resource_course(engine, include_room=True, include_draft=True)
    fourth = _load_migration("0004_resource_eligibility_availability.py", "resource_eligibility_downgrade")

    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        connection.commit()
        context = MigrationContext.configure(connection)
        fourth.op = Operations(context)
        with context.begin_transaction():
            fourth.downgrade()

        inspector = inspect(connection)
        assert connection.execute(text("SELECT lecturer_id, room_id FROM courses WHERE id=1")).one() == (7, 9)
        assert connection.execute(text("SELECT lecturer_id, room_id FROM draft_sessions WHERE id=1")).one() == (7, 9)
        assert "course_eligible_lecturers" not in inspector.get_table_names()
        assert "course_eligible_rooms" not in inspector.get_table_names()
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1


def test_fourth_migration_downgrade_rejects_course_without_legacy_room_before_mutating_schema():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    _seed_current_resource_course(engine, include_room=False, include_draft=False)
    fourth = _load_migration("0004_resource_eligibility_availability.py", "resource_eligibility_downgrade_guard")

    with engine.connect() as connection:
        fourth.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(RuntimeError, match="cannot be represented by the FS-007 schema"):
            fourth.downgrade()

        inspector = inspect(connection)
        assert "course_eligible_rooms" in inspector.get_table_names()
        assert "room_id" not in _columns_by_name(inspector, "courses")


def test_unavailability_database_constraints_reject_invalid_owner_and_weekday():
    engine = create_engine("sqlite://")
    initialize_database(engine)

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO lecturers (id, name, reference_code, normalized_reference_code, is_active, revision) "
                "VALUES (1, 'L', 'L-1', 'l-1', 1, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO rooms (id, name, reference_code, normalized_reference_code, capacity, is_active, revision) "
                "VALUES (1, 'R', 'R-1', 'r-1', 10, 1, 1)"
            )
        )
        with pytest.raises(Exception):
            connection.execute(
                text(
                    "INSERT INTO resource_unavailability_periods "
                    "(id, lecturer_id, room_id, kind, start_time, end_time, revision) "
                    "VALUES (1, 1, 1, 'recurring', '08:00:00', '10:00:00', 1)"
                )
            )
        connection.execute(
            text(
                "INSERT INTO resource_unavailability_periods "
                "(id, lecturer_id, room_id, kind, start_time, end_time, revision) "
                "VALUES (2, 1, NULL, 'recurring', '08:00:00', '10:00:00', 1)"
            )
        )
        with pytest.raises(Exception):
            connection.execute(
                text("INSERT INTO resource_unavailability_weekdays (period_id, weekday) VALUES (2, 7)")
            )


def test_current_schema_contains_constrained_institution_holidays_and_is_idempotent():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    initialize_database(engine)
    inspector = inspect(engine)
    assert {"id", "date", "name", "revision"} == set(
        _columns_by_name(inspector, "institution_holidays")
    )
    assert any(
        set(item.get("column_names") or []) == {"date"}
        for item in inspector.get_unique_constraints("institution_holidays")
    )
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO institution_holidays (date, name, revision) "
            "VALUES ('2026-12-25', 'Winter Holiday', 1)"
        ))
        with pytest.raises(Exception):
            connection.execute(text(
                "INSERT INTO institution_holidays (date, name, revision) "
                "VALUES ('2026-12-25', 'Duplicate', 1)"
            ))


def test_fifth_migration_upgrades_0004_and_downgrade_removes_only_holidays():
    engine = create_engine("sqlite://")
    migrations = (
        _load_initial_migration(),
        _load_migration("0002_course_semester_drafts.py", "course_semester_for_holidays"),
        _load_migration("0003_academic_catalog_administration.py", "catalog_for_holidays"),
        _load_migration("0004_resource_eligibility_availability.py", "resources_for_holidays"),
        _load_migration("0005_institution_holidays.py", "institution_holidays"),
    )
    with engine.begin() as connection:
        for migration in migrations:
            migration.op = Operations(MigrationContext.configure(connection))
            migration.upgrade()
        fifth = migrations[-1]
        assert "institution_holidays" in inspect(connection).get_table_names()
        existing_tables = set(inspect(connection).get_table_names()) - {"institution_holidays"}
        fifth.downgrade()
        remaining_tables = set(inspect(connection).get_table_names())
        assert "institution_holidays" not in remaining_tables
        assert existing_tables == remaining_tables


def test_current_schema_contains_constrained_exam_tables_and_is_idempotent():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    initialize_database(engine)
    inspector = inspect(engine)
    assert {"course_exam_configurations", "exam_sessions"}.issubset(inspector.get_table_names())
    configuration_columns = _columns_by_name(inspector, "course_exam_configurations")
    exam_columns = _columns_by_name(inspector, "exam_sessions")
    assert {"course_id", "semester_id", "enabled", "configuration_consumed", "revision"}.issubset(configuration_columns)
    assert {"exam_date", "start_time", "end_time", "source", "revision", "configuration_identifier", "final_teaching_session_id_snapshot"}.issubset(exam_columns)
    assert any(
        set(item.get("column_names") or []) == {"course_id", "semester_id"}
        for item in inspector.get_unique_constraints("course_exam_configurations")
    )
    index_columns = {
        tuple(item.get("column_names") or [])
        for item in inspector.get_indexes("exam_sessions")
    }
    assert ("course_id", "semester_id", "exam_date") in index_columns
    assert ("semester_id", "exam_date", "lecturer_id") in index_columns
    assert ("semester_id", "exam_date", "room_id") in index_columns
    assert ("semester_id", "exam_date", "cohort_id") in index_columns


def test_sixth_migration_upgrades_0005_and_downgrade_removes_only_exam_tables():
    engine = create_engine("sqlite://")
    migrations = (
        _load_initial_migration(),
        _load_migration("0002_course_semester_drafts.py", "course_semester_for_exams"),
        _load_migration("0003_academic_catalog_administration.py", "catalog_for_exams"),
        _load_migration("0004_resource_eligibility_availability.py", "resources_for_exams"),
        _load_migration("0005_institution_holidays.py", "holidays_for_exams"),
        _load_migration("0006_conflict_aware_exam_scheduling.py", "conflict_aware_exams"),
    )
    with engine.begin() as connection:
        for migration in migrations:
            migration.op = Operations(MigrationContext.configure(connection))
            migration.upgrade()
        sixth = migrations[-1]
        existing_tables = set(inspect(connection).get_table_names()) - {"course_exam_configurations", "exam_sessions"}
        sixth.downgrade()
        remaining_tables = set(inspect(connection).get_table_names())
        assert {"course_exam_configurations", "exam_sessions"}.isdisjoint(remaining_tables)
        assert existing_tables == remaining_tables


def test_current_schema_contains_constrained_versioned_lifecycle_tables_and_is_idempotent():
    engine = create_engine("sqlite://")

    initialize_database(engine)
    initialize_database(engine)

    inspector = inspect(engine)
    assert {"schedule_revisions", "schedule_revision_events"}.issubset(
        inspector.get_table_names()
    )
    assert {
        "semester_id",
        "revision_number",
        "state",
        "origin_revision_id",
        "row_version",
        "snapshot_schema_version",
        "snapshot_document",
        "created_at",
        "state_changed_at",
        "published_at",
        "updated_at",
    }.issubset(_columns_by_name(inspector, "schedule_revisions"))
    assert {
        "semester_id",
        "schedule_revision_id",
        "event_sequence",
        "event_type",
        "from_state",
        "to_state",
        "occurred_at",
    }.issubset(_columns_by_name(inspector, "schedule_revision_events"))
    index_names = {item["name"] for item in inspector.get_indexes("schedule_revisions")}
    assert "uq_schedule_revision_active_working" in index_names
    assert "uq_schedule_revision_current_publication" in index_names

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO semesters "
                "(id, name, normalized_name_key, name_repair_required, start_date, end_date, is_active, revision) "
                "VALUES (1, 'Fall', 'fall', 0, '2026-09-01', '2026-12-20', 1, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO schedule_revisions "
                "(semester_id, revision_number, state, row_version, created_at, state_changed_at, updated_at) "
                "VALUES (1, 1, 'draft', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        with pytest.raises(Exception):
            connection.execute(
                text(
                    "INSERT INTO schedule_revisions "
                    "(semester_id, revision_number, state, row_version, created_at, state_changed_at, updated_at) "
                    "VALUES (1, 2, 'ready_for_review', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )


def test_seventh_migration_upgrades_exact_0006_backfills_populated_semesters_and_preserves_data():
    engine = create_engine("sqlite://")
    migrations = _upgrade_chain_through_0006(engine)
    seventh = _load_migration(
        "0007_versioned_schedule_lifecycle.py", "versioned_schedule_lifecycle"
    )

    with engine.begin() as connection:
        _seed_fs012_lifecycle_upgrade_rows(connection)
        seventh.op = Operations(MigrationContext.configure(connection))
        seventh.upgrade()

        assert connection.execute(
            text(
                "SELECT semester_id, revision_number, state, row_version "
                "FROM schedule_revisions ORDER BY semester_id"
            )
        ).all() == [(1, 1, "draft", 1), (2, 1, "draft", 1)]
        assert connection.execute(
            text(
                "SELECT semester_id, event_sequence, event_type, from_state, to_state "
                "FROM schedule_revision_events ORDER BY semester_id"
            )
        ).all() == [
            (1, 1, "created", None, "draft"),
            (2, 1, "created", None, "draft"),
        ]
        assert connection.execute(
            text("SELECT COUNT(*) FROM schedule_revisions WHERE semester_id=3")
        ).scalar_one() == 0
        assert connection.execute(
            text("SELECT course_name_snapshot FROM draft_schedules WHERE semester_id=1")
        ).scalar_one() == "Lifecycle Course"
        assert connection.execute(
            text("SELECT configuration_identifier FROM exam_sessions WHERE semester_id=2")
        ).scalar_one() == "EXAM-1"
        assert migrations[-1].revision == "0006_conflict_aware_exam_scheduling"


def test_seventh_migration_downgrade_refuses_unrepresentable_history_before_mutation():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    seventh = _load_migration(
        "0007_versioned_schedule_lifecycle.py", "versioned_lifecycle_downgrade_guard"
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO semesters "
                "(id, name, normalized_name_key, name_repair_required, start_date, end_date, is_active, revision) "
                "VALUES (1, 'Fall', 'fall', 0, '2026-09-01', '2026-12-20', 1, 1)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO schedule_revisions "
                "(id, semester_id, revision_number, state, row_version, snapshot_schema_version, snapshot_document, "
                "created_at, state_changed_at, published_at, updated_at) "
                "VALUES (1, 1, 1, 'published', 2, 1, '{}', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO schedule_revision_events "
                "(semester_id, schedule_revision_id, event_sequence, event_type, from_state, to_state, occurred_at) "
                "VALUES (1, 1, 1, 'created', NULL, 'draft', CURRENT_TIMESTAMP), "
                "(1, 1, 2, 'published', 'draft', 'published', CURRENT_TIMESTAMP)"
            )
        )
        seventh.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(RuntimeError, match="cannot be represented by the FS-012 schema"):
            seventh.downgrade()
        assert {"schedule_revisions", "schedule_revision_events"}.issubset(
            inspect(connection).get_table_names()
        )


def test_startup_rejects_partial_versioned_lifecycle_schema():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE schedule_revision_events"))

    with pytest.raises(Exception, match="supported FS-001 through FS-012 state"):
        initialize_database(engine)


def _seed_current_resource_course(engine, *, include_room: bool, include_draft: bool) -> None:
    lecturer = Lecturer(id=7, name="Lecturer", reference_code="LECT-7", normalized_reference_code="lect-7")
    room = Room(id=9, name="Room", reference_code="ROOM-9", normalized_reference_code="room-9", capacity=30)
    cohort = Cohort(id=1, name="Cohort", student_count=20)
    semester = Semester(id=1, name="Fall", start_date=date(2026, 9, 1), end_date=date(2026, 12, 20))
    study_type = StudyType(id=1, name="Full-time")
    course = Course(
        id=1,
        name="Course",
        total_units=4,
        min_session_units=2,
        max_session_units=2,
        cohort_id=1,
        study_type_id=1,
        current_semester_id=1,
        eligible_lecturers=[CourseEligibleLecturer(lecturer_id=7)],
        eligible_rooms=[CourseEligibleRoom(room_id=9)] if include_room else [],
    )
    rows = [lecturer, room, cohort, semester, study_type, course]
    if include_draft:
        draft = DraftSchedule(
            id=1,
            course_id=1,
            semester_id=1,
            status="generated",
            revision=1,
            course_name_snapshot="Course",
            course_total_units_snapshot=4,
            course_min_session_units_snapshot=2,
            course_max_session_units_snapshot=2,
            cohort_id_snapshot=1,
            cohort_name_snapshot="Cohort",
            cohort_size_snapshot=20,
            study_type_id_snapshot=1,
            study_type_name_snapshot="Full-time",
            semester_name_snapshot="Fall",
            semester_start_date_snapshot=date(2026, 9, 1),
            semester_end_date_snapshot=date(2026, 12, 20),
            sessions=[DraftSession(
                id=1,
                course_id=1,
                lecturer_id=7,
                cohort_id=1,
                room_id=9,
                date=date(2026, 9, 7),
                start_time=time(8),
                end_time=time(10),
                units=2,
                constraint_window_index=0,
            )],
        )
        rows.append(draft)
    with Session(engine) as db:
        db.add_all(rows)
        db.commit()


def _upgrade_chain_through_0006(engine):
    migrations = (
        _load_initial_migration(),
        _load_migration("0002_course_semester_drafts.py", "lifecycle_course_semester"),
        _load_migration("0003_academic_catalog_administration.py", "lifecycle_catalog"),
        _load_migration("0004_resource_eligibility_availability.py", "lifecycle_resources"),
        _load_migration("0005_institution_holidays.py", "lifecycle_holidays"),
        _load_migration("0006_conflict_aware_exam_scheduling.py", "lifecycle_exams"),
    )
    with engine.begin() as connection:
        for migration in migrations:
            migration.op = Operations(MigrationContext.configure(connection))
            migration.upgrade()
    return migrations


def _seed_fs012_lifecycle_upgrade_rows(connection) -> None:
    connection.execute(
        text(
            "INSERT INTO lecturers "
            "(id, name, reference_code, normalized_reference_code, is_active, revision) "
            "VALUES (1, 'Lecturer', 'L-1', 'l-1', 1, 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO cohorts "
            "(id, name, normalized_name_key, name_repair_required, student_count, is_active, revision) "
            "VALUES (1, 'Cohort', 'cohort', 0, 20, 1, 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO rooms "
            "(id, name, reference_code, normalized_reference_code, capacity, is_active, revision) "
            "VALUES (1, 'Room', 'R-1', 'r-1', 30, 1, 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO semesters "
            "(id, name, normalized_name_key, name_repair_required, start_date, end_date, is_active, revision) VALUES "
            "(1, 'Fall', 'fall', 0, '2026-09-01', '2026-12-20', 1, 1), "
            "(2, 'Spring', 'spring', 0, '2027-02-01', '2027-06-20', 1, 1), "
            "(3, 'Empty', 'empty', 0, '2027-09-01', '2027-12-20', 1, 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO study_types "
            "(id, name, normalized_name_key, name_repair_required, is_active, revision) "
            "VALUES (1, 'Full-time', 'full-time', 0, 1, 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO courses "
            "(id, name, normalized_name_key, name_repair_required, total_units, min_session_units, max_session_units, "
            "cohort_id, study_type_id, current_semester_id, is_active, revision) "
            "VALUES (1, 'Lifecycle Course', 'lifecycle-course', 0, 4, 2, 2, 1, 1, 1, 1, 1)"
        )
    )
    connection.execute(
        text(
            "INSERT INTO draft_schedules "
            "(id, course_id, semester_id, revision, selected_time_window_id, status, created_at, "
            "course_name_snapshot, course_total_units_snapshot, course_min_session_units_snapshot, "
            "course_max_session_units_snapshot, cohort_id_snapshot, cohort_name_snapshot, cohort_size_snapshot, "
            "study_type_id_snapshot, study_type_name_snapshot, semester_name_snapshot, semester_start_date_snapshot, semester_end_date_snapshot) "
            "VALUES (1, 1, 1, 1, NULL, 'generated', CURRENT_TIMESTAMP, 'Lifecycle Course', 4, 2, 2, 1, 'Cohort', 20, 1, 'Full-time', 'Fall', '2026-09-01', '2026-12-20')"
        )
    )
    connection.execute(
        text(
            "INSERT INTO exam_sessions "
            "(id, course_id, semester_id, cohort_id, lecturer_id, room_id, exam_date, start_time, end_time, source, revision, "
            "configuration_identifier, configuration_revision, duration_minutes, exam_type, required_capacity, "
            "recommended_start_date, recommended_end_date, recommendation_was_overridden, final_teaching_date, "
            "final_teaching_end_time, final_teaching_session_id_snapshot, course_name_snapshot, semester_name_snapshot, "
            "cohort_name_snapshot, lecturer_name_snapshot, lecturer_reference_snapshot, room_name_snapshot, room_reference_snapshot) "
            "VALUES (1, 1, 2, 1, 1, 1, '2027-06-10', '08:00:00', '09:00:00', 'manual', 1, "
            "'EXAM-1', 1, 60, 'Written', 20, '2027-06-01', '2027-06-20', 0, '2027-05-30', '10:00:00', 99, "
            "'Lifecycle Course', 'Spring', 'Cohort', 'Lecturer', 'L-1', 'Room', 'R-1')"
        )
    )


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
