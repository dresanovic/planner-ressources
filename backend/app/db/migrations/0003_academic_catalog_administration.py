"""add academic catalog administration and immutable schedule facts

Revision ID: 0003_academic_catalog_administration
Revises: 0002_course_semester_drafts
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_academic_catalog_administration"
down_revision = "0002_course_semester_drafts"
branch_labels = None
depends_on = None

NAMED_TABLES = ("semesters", "cohorts", "courses", "study_types")


def _normalize(value: str) -> str:
    return value.strip().casefold()


def upgrade() -> None:
    connection = op.get_bind()

    for table in (*NAMED_TABLES, "study_type_time_windows"):
        op.add_column(table, sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
        op.add_column(table, sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))

    for table in NAMED_TABLES:
        op.add_column(table, sa.Column("normalized_name", sa.String(length=200), nullable=True))
        op.add_column(table, sa.Column("normalized_name_key", sa.String(length=260), nullable=True))
        op.add_column(table, sa.Column("name_repair_required", sa.Boolean(), nullable=False, server_default=sa.false()))
        rows = connection.execute(sa.text(f"SELECT id, name FROM {table} ORDER BY id")).mappings().all()
        groups: dict[str, list[dict]] = {}
        for row in rows:
            groups.setdefault(_normalize(row["name"]), []).append(row)
        for canonical, group in groups.items():
            conflicted = len(group) > 1
            for row in group:
                key = f"{canonical}#legacy-{row['id']}" if conflicted else canonical
                connection.execute(
                    sa.text(
                        f"UPDATE {table} SET normalized_name=:normalized, normalized_name_key=:key, "
                        "name_repair_required=:repair WHERE id=:id"
                    ),
                    {
                        "normalized": None if conflicted else canonical,
                        "key": key,
                        "repair": conflicted,
                        "id": row["id"],
                    },
                )
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.alter_column("normalized_name_key", existing_type=sa.String(260), nullable=False)
            batch_op.create_unique_constraint(f"uq_{table}_normalized_name", ["normalized_name"])
            batch_op.create_unique_constraint(f"uq_{table}_normalized_name_key", ["normalized_name_key"])

    with op.batch_alter_table("study_type_time_windows", recreate="always") as batch_op:
        batch_op.create_unique_constraint(
            "uq_study_type_time_window_exact",
            ["study_type_id", "weekday", "start_time", "end_time"],
        )

    with op.batch_alter_table("courses", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("current_semester_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_courses_current_semester_id_semesters",
            "semesters",
            ["current_semester_id"],
            ["id"],
        )

    semester_ids = [row[0] for row in connection.execute(sa.text("SELECT id FROM semesters ORDER BY id"))]
    course_ids = [row[0] for row in connection.execute(sa.text("SELECT id FROM courses ORDER BY id"))]
    for course_id in course_ids:
        semester_id = connection.execute(
            sa.text(
                "SELECT semester_id FROM draft_schedules WHERE course_id=:course_id "
                "ORDER BY created_at DESC, id DESC LIMIT 1"
            ),
            {"course_id": course_id},
        ).scalar_one_or_none()
        if semester_id is None:
            semester_id = connection.execute(
                sa.text(
                    "SELECT semester_id FROM generation_constraint_sets WHERE course_id=:course_id "
                    "ORDER BY updated_at DESC, id DESC LIMIT 1"
                ),
                {"course_id": course_id},
            ).scalar_one_or_none()
        if semester_id is None and len(semester_ids) == 1:
            semester_id = semester_ids[0]
        if semester_id is not None:
            connection.execute(
                sa.text("UPDATE courses SET current_semester_id=:semester_id WHERE id=:course_id"),
                {"semester_id": semester_id, "course_id": course_id},
            )

    snapshot_columns = (
        sa.Column("course_name_snapshot", sa.String(length=200), nullable=True),
        sa.Column("course_total_units_snapshot", sa.Integer(), nullable=True),
        sa.Column("course_min_session_units_snapshot", sa.Integer(), nullable=True),
        sa.Column("course_max_session_units_snapshot", sa.Integer(), nullable=True),
        sa.Column("cohort_id_snapshot", sa.Integer(), nullable=True),
        sa.Column("cohort_name_snapshot", sa.String(length=200), nullable=True),
        sa.Column("cohort_size_snapshot", sa.Integer(), nullable=True),
        sa.Column("study_type_id_snapshot", sa.Integer(), nullable=True),
        sa.Column("study_type_name_snapshot", sa.String(length=200), nullable=True),
        sa.Column("semester_name_snapshot", sa.String(length=200), nullable=True),
        sa.Column("semester_start_date_snapshot", sa.Date(), nullable=True),
        sa.Column("semester_end_date_snapshot", sa.Date(), nullable=True),
    )
    for column in snapshot_columns:
        op.add_column("draft_schedules", column)

    drafts = connection.execute(
        sa.text(
            "SELECT d.id, c.name course_name, c.total_units, c.min_session_units, c.max_session_units, "
            "co.id cohort_id, co.name cohort_name, co.student_count, st.id study_type_id, st.name study_type_name, "
            "s.name semester_name, s.start_date, s.end_date "
            "FROM draft_schedules d JOIN courses c ON c.id=d.course_id "
            "JOIN cohorts co ON co.id=c.cohort_id JOIN study_types st ON st.id=c.study_type_id "
            "JOIN semesters s ON s.id=d.semester_id"
        )
    ).mappings().all()
    for row in drafts:
        connection.execute(
            sa.text(
                "UPDATE draft_schedules SET course_name_snapshot=:course_name, "
                "course_total_units_snapshot=:total_units, course_min_session_units_snapshot=:min_units, "
                "course_max_session_units_snapshot=:max_units, cohort_id_snapshot=:cohort_id, "
                "cohort_name_snapshot=:cohort_name, cohort_size_snapshot=:cohort_size, "
                "study_type_id_snapshot=:study_type_id, study_type_name_snapshot=:study_type_name, "
                "semester_name_snapshot=:semester_name, semester_start_date_snapshot=:start_date, "
                "semester_end_date_snapshot=:end_date WHERE id=:id"
            ),
            {
                "id": row["id"], "course_name": row["course_name"], "total_units": row["total_units"],
                "min_units": row["min_session_units"], "max_units": row["max_session_units"],
                "cohort_id": row["cohort_id"], "cohort_name": row["cohort_name"], "cohort_size": row["student_count"],
                "study_type_id": row["study_type_id"], "study_type_name": row["study_type_name"],
                "semester_name": row["semester_name"], "start_date": row["start_date"], "end_date": row["end_date"],
            },
        )
    with op.batch_alter_table("draft_schedules", recreate="always") as batch_op:
        for column in snapshot_columns:
            batch_op.alter_column(column.name, existing_type=column.type, nullable=False)


def downgrade() -> None:
    snapshot_names = (
        "semester_end_date_snapshot", "semester_start_date_snapshot", "semester_name_snapshot",
        "study_type_name_snapshot", "study_type_id_snapshot", "cohort_size_snapshot",
        "cohort_name_snapshot", "cohort_id_snapshot", "course_max_session_units_snapshot",
        "course_min_session_units_snapshot", "course_total_units_snapshot", "course_name_snapshot",
    )
    with op.batch_alter_table("draft_schedules", recreate="always") as batch_op:
        for name in snapshot_names:
            batch_op.drop_column(name)
    with op.batch_alter_table("courses", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_courses_current_semester_id_semesters", type_="foreignkey")
        batch_op.drop_column("current_semester_id")
    with op.batch_alter_table("study_type_time_windows", recreate="always") as batch_op:
        batch_op.drop_constraint("uq_study_type_time_window_exact", type_="unique")
    for table in reversed(NAMED_TABLES):
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.drop_constraint(f"uq_{table}_normalized_name", type_="unique")
            batch_op.drop_constraint(f"uq_{table}_normalized_name_key", type_="unique")
            batch_op.drop_column("name_repair_required")
            batch_op.drop_column("normalized_name_key")
            batch_op.drop_column("normalized_name")
    for table in (*NAMED_TABLES, "study_type_time_windows"):
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.drop_column("revision")
            batch_op.drop_column("is_active")
