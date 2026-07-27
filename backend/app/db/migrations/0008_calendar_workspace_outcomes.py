"""retain revision-scoped planning outcomes for the calendar workspace

Revision ID: 0008_calendar_workspace_outcomes
Revises: 0007_versioned_schedule_lifecycle
Create Date: 2026-07-23
"""

import sqlalchemy as sa
from alembic import op

revision = "0008_calendar_workspace_outcomes"
down_revision = "0007_versioned_schedule_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "planning_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "schedule_revision_id",
            sa.Integer(),
            sa.ForeignKey("schedule_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            sa.Integer(),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_kind", sa.String(40), nullable=False),
        sa.Column("classification", sa.String(30), nullable=False),
        sa.Column("source_status", sa.String(100), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint(
            "schedule_revision_id",
            "course_id",
            "operation_kind",
            name="uq_planning_outcome_revision_course_kind",
        ),
        sa.CheckConstraint(
            "operation_kind IN ('single_course_generation', 'multi_course_generation', "
            "'semester_optimization', 'exam_generation')",
            name="ck_planning_outcome_operation_kind",
        ),
        sa.CheckConstraint(
            "classification IN ('successful', 'failed', 'stale', 'unchanged', 'skipped')",
            name="ck_planning_outcome_classification",
        ),
    )
    op.create_index(
        "ix_planning_outcomes_revision",
        "planning_outcomes",
        ["schedule_revision_id"],
    )
    op.create_index(
        "ix_planning_outcomes_course",
        "planning_outcomes",
        ["course_id"],
    )


def downgrade() -> None:
    op.drop_table("planning_outcomes")
