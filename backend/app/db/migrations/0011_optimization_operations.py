"""Add non-restorable optimization outcome receipts.

Revision ID: 0011_optimization_operations
Revises: 0010_planner_authentication
"""
import sqlalchemy as sa
from alembic import op

revision = "0011_optimization_operations"
down_revision = "0010_planner_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "optimization_operations",
        sa.Column("operation_id", sa.String(36), primary_key=True),
        sa.Column("owner_account_id", sa.Integer(), sa.ForeignKey("planner_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("originating_session_id", sa.Integer(), nullable=False),
        sa.Column("originating_session_secret_digest", sa.String(64), nullable=False),
        sa.Column("context_secret_digest", sa.String(64), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("schedule_revision_id", sa.Integer(), sa.ForeignKey("schedule_revisions.id"), nullable=False),
        sa.Column("selected_course_ids", sa.JSON(), nullable=False),
        sa.Column("budget_seconds", sa.Integer(), nullable=False),
        sa.Column("captured_ceiling_seconds", sa.Integer(), nullable=False),
        sa.Column("policy_fingerprint", sa.String(64), nullable=False),
        sa.Column("phase", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("elapsed_milliseconds", sa.Integer(), nullable=False),
        sa.Column("budget_exhausted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("terminal_code", sa.String(80), nullable=True),
        sa.Column("saved_result", sa.JSON(none_as_null=True), nullable=True),
        sa.CheckConstraint("budget_seconds > 0 AND captured_ceiling_seconds >= budget_seconds", name="ck_optimization_budget"),
        sa.CheckConstraint("elapsed_milliseconds >= 0", name="ck_optimization_elapsed"),
        sa.CheckConstraint("originating_session_id > 0", name="ck_optimization_session"),
        sa.CheckConstraint("phase IN ('preparing','optimizing','checking','ready_to_save','awaiting_decision','saving','saved','cancelled','timeout_no_candidate','failed','stale','interrupted')", name="ck_optimization_phase"),
        sa.CheckConstraint("(phase = 'saved' AND saved_result IS NOT NULL) OR (phase != 'saved' AND saved_result IS NULL)", name="ck_optimization_saved_result"),
        sa.CheckConstraint("phase NOT IN ('failed','stale','interrupted','timeout_no_candidate') OR terminal_code IS NOT NULL", name="ck_optimization_terminal_code"),
        sa.CheckConstraint("(phase IN ('saved','cancelled','timeout_no_candidate','failed','stale','interrupted') AND finished_at IS NOT NULL) OR (phase NOT IN ('saved','cancelled','timeout_no_candidate','failed','stale','interrupted') AND finished_at IS NULL)", name="ck_optimization_finished"),
        sa.CheckConstraint("length(operation_id) = 36 AND substr(operation_id,15,1) = '4'", name="ck_optimization_uuid"),
        *(
            sa.CheckConstraint(f"length({column}) = 64 AND {column} NOT GLOB '*[^0-9a-f]*'", name=f"ck_optimization_{column}")
            for column in ("originating_session_secret_digest", "context_secret_digest", "request_fingerprint", "policy_fingerprint")
        ),
    )


def downgrade() -> None:
    op.drop_table("optimization_operations")
