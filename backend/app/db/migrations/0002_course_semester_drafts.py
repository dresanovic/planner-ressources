"""add course-semester draft identity and optimistic revisions

Revision ID: 0002_course_semester_drafts
Revises: 0001_create_planning_tables
Create Date: 2026-07-13
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_course_semester_drafts"
down_revision = "0001_create_planning_tables"
branch_labels = None
depends_on = None


NAMING_CONVENTION = {"uq": "uq_%(table_name)s_%(column_0_name)s"}


def upgrade() -> None:
    with op.batch_alter_table(
        "draft_schedules", recreate="always", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.add_column(
            sa.Column("revision", sa.Integer(), nullable=False, server_default="1")
        )
        batch_op.drop_constraint("uq_draft_schedules_course_id", type_="unique")
        batch_op.create_unique_constraint(
            "uq_draft_schedule_course_semester", ["course_id", "semester_id"]
        )
    with op.batch_alter_table("generation_constraint_sets", recreate="always") as batch_op:
        batch_op.add_column(
            sa.Column("revision", sa.Integer(), nullable=False, server_default="1")
        )


def downgrade() -> None:
    with op.batch_alter_table("generation_constraint_sets", recreate="always") as batch_op:
        batch_op.drop_column("revision")
    with op.batch_alter_table(
        "draft_schedules", recreate="always", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_constraint("uq_draft_schedule_course_semester", type_="unique")
        batch_op.create_unique_constraint("uq_draft_schedules_course_id", ["course_id"])
        batch_op.drop_column("revision")
