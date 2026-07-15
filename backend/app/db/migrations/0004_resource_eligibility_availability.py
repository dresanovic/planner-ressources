"""add resource eligibility and availability

Revision ID: 0004_resource_eligibility_availability
Revises: 0003_academic_catalog_administration
Create Date: 2026-07-15
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_resource_eligibility_availability"
down_revision = "0003_academic_catalog_administration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    for table, prefix in (("lecturers", "LECT"), ("rooms", "ROOM")):
        op.add_column(table, sa.Column("reference_code", sa.String(length=100), nullable=True))
        op.add_column(
            table,
            sa.Column("normalized_reference_code", sa.String(length=100), nullable=True),
        )
        op.add_column(
            table,
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.add_column(
            table,
            sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        )
        rows = connection.execute(sa.text(f"SELECT id FROM {table} ORDER BY id")).all()
        for (resource_id,) in rows:
            code = f"{prefix}-{resource_id}"
            connection.execute(
                sa.text(
                    f"UPDATE {table} SET reference_code=:code, "
                    "normalized_reference_code=:normalized WHERE id=:id"
                ),
                {"code": code, "normalized": code.casefold(), "id": resource_id},
            )
        with op.batch_alter_table(table, recreate="always") as batch_op:
            batch_op.alter_column(
                "reference_code",
                existing_type=sa.String(100),
                nullable=False,
            )
            batch_op.alter_column(
                "normalized_reference_code",
                existing_type=sa.String(100),
                nullable=False,
            )
            batch_op.create_unique_constraint(
                f"uq_{table}_normalized_reference_code",
                ["normalized_reference_code"],
            )
            if table == "rooms":
                batch_op.create_check_constraint("ck_rooms_capacity_positive", "capacity > 0")

    op.create_table(
        "course_eligible_lecturers",
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "lecturer_id",
            sa.Integer(),
            sa.ForeignKey("lecturers.id"),
            primary_key=True,
        ),
    )
    op.create_table(
        "course_eligible_rooms",
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("rooms.id"),
            primary_key=True,
        ),
    )
    connection.execute(
        sa.text(
            "INSERT INTO course_eligible_lecturers (course_id, lecturer_id) "
            "SELECT id, lecturer_id FROM courses"
        )
    )
    connection.execute(
        sa.text(
            "INSERT INTO course_eligible_rooms (course_id, room_id) "
            "SELECT id, room_id FROM courses"
        )
    )

    op.create_table(
        "resource_unavailability_periods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lecturer_id",
            sa.Integer(),
            sa.ForeignKey("lecturers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "room_id",
            sa.Integer(),
            sa.ForeignKey("rooms.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint(
            "(lecturer_id IS NOT NULL AND room_id IS NULL) OR "
            "(lecturer_id IS NULL AND room_id IS NOT NULL)",
            name="ck_resource_unavailability_exactly_one_owner",
        ),
        sa.CheckConstraint(
            "kind IN ('recurring', 'dated')",
            name="ck_resource_unavailability_kind",
        ),
        sa.CheckConstraint(
            "(kind = 'recurring' AND start_date IS NULL AND end_date IS NULL AND end_time > start_time) OR "
            "(kind = 'dated' AND start_date IS NOT NULL AND end_date IS NOT NULL AND "
            "(end_date > start_date OR (end_date = start_date AND end_time > start_time)))",
            name="ck_resource_unavailability_shape",
        ),
        sa.CheckConstraint(
            "revision > 0",
            name="ck_resource_unavailability_revision_positive",
        ),
    )
    op.create_table(
        "resource_unavailability_weekdays",
        sa.Column(
            "period_id",
            sa.Integer(),
            sa.ForeignKey("resource_unavailability_periods.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("weekday", sa.Integer(), primary_key=True),
        sa.CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_resource_unavailability_weekday",
        ),
    )

    with op.batch_alter_table("courses", recreate="always") as batch_op:
        batch_op.drop_column("lecturer_id")
        batch_op.drop_column("room_id")


def downgrade() -> None:
    connection = op.get_bind()
    course_ids = set(connection.execute(sa.text("SELECT id FROM courses")).scalars())
    lecturer_by_course = dict(
        connection.execute(
            sa.text(
                "SELECT course_id, MIN(lecturer_id) FROM course_eligible_lecturers "
                "GROUP BY course_id"
            )
        ).all()
    )
    room_by_course = dict(
        connection.execute(
            sa.text(
                "SELECT course_id, MIN(room_id) FROM course_eligible_rooms "
                "GROUP BY course_id"
            )
        ).all()
    )
    missing_lecturer_ids = sorted(course_ids - lecturer_by_course.keys())
    missing_room_ids = sorted(course_ids - room_by_course.keys())
    if missing_lecturer_ids or missing_room_ids:
        details = []
        if missing_lecturer_ids:
            details.append(f"Courses without an eligible Lecturer: {missing_lecturer_ids}")
        if missing_room_ids:
            details.append(f"Courses without an eligible Room: {missing_room_ids}")
        raise RuntimeError(
            "FS-008 resource eligibility cannot be represented by the FS-007 schema. "
            + " ".join(details)
        )

    restore_foreign_keys = (
        connection.dialect.name == "sqlite"
        and connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    )
    if restore_foreign_keys:
        _set_sqlite_foreign_keys(connection, enabled=False)
    try:
        with op.batch_alter_table("courses", recreate="always") as batch_op:
            batch_op.add_column(sa.Column("lecturer_id", sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column("room_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_courses_lecturer_id_lecturers",
                "lecturers",
                ["lecturer_id"],
                ["id"],
            )
            batch_op.create_foreign_key(
                "fk_courses_room_id_rooms",
                "rooms",
                ["room_id"],
                ["id"],
            )
        for course_id in sorted(course_ids):
            connection.execute(
                sa.text(
                    "UPDATE courses SET lecturer_id=:lecturer_id, room_id=:room_id "
                    "WHERE id=:course_id"
                ),
                {
                    "course_id": course_id,
                    "lecturer_id": lecturer_by_course[course_id],
                    "room_id": room_by_course[course_id],
                },
            )
        with op.batch_alter_table("courses", recreate="always") as batch_op:
            batch_op.alter_column("lecturer_id", existing_type=sa.Integer(), nullable=False)
            batch_op.alter_column("room_id", existing_type=sa.Integer(), nullable=False)

        op.drop_table("resource_unavailability_weekdays")
        op.drop_table("resource_unavailability_periods")
        op.drop_table("course_eligible_rooms")
        op.drop_table("course_eligible_lecturers")
        for table in ("rooms", "lecturers"):
            with op.batch_alter_table(table, recreate="always") as batch_op:
                if table == "rooms":
                    batch_op.drop_constraint("ck_rooms_capacity_positive", type_="check")
                batch_op.drop_constraint(
                    f"uq_{table}_normalized_reference_code",
                    type_="unique",
                )
                batch_op.drop_column("revision")
                batch_op.drop_column("is_active")
                batch_op.drop_column("normalized_reference_code")
                batch_op.drop_column("reference_code")
    except Exception:
        if connection.in_transaction():
            connection.rollback()
        if restore_foreign_keys:
            _set_sqlite_foreign_keys(connection, enabled=True)
        raise
    else:
        if restore_foreign_keys:
            _set_sqlite_foreign_keys(connection, enabled=True)


def _set_sqlite_foreign_keys(connection, *, enabled: bool) -> None:
    if connection.in_transaction():
        connection.commit()
    connection.exec_driver_sql(f"PRAGMA foreign_keys={'ON' if enabled else 'OFF'}")
    connection.commit()
