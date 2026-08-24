"""add named planner accounts, one-time access, sessions, and startup state

Revision ID: 0010_planner_authentication
Revises: 0009_lecturer_token_review
Create Date: 2026-08-24
"""

import sqlalchemy as sa
from alembic import op


revision = "0010_planner_authentication"
down_revision = "0009_lecturer_token_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "planner_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("login_name", sa.String(128), nullable=False),
        sa.Column("normalized_login_name", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_administrator", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("login_blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "normalized_login_name",
            name="uq_planner_accounts_normalized_login_name",
        ),
        sa.CheckConstraint(
            "length(login_name) BETWEEN 1 AND 128",
            name="ck_planner_accounts_login_name_length",
        ),
        sa.CheckConstraint(
            "length(display_name) BETWEEN 1 AND 200",
            name="ck_planner_accounts_display_name_length",
        ),
        sa.CheckConstraint(
            "is_administrator = 0 OR is_active = 1",
            name="ck_planner_accounts_active_administrator",
        ),
        sa.CheckConstraint(
            "failed_login_count >= 0",
            name="ck_planner_accounts_failed_login_count_nonnegative",
        ),
        sa.CheckConstraint(
            "revision > 0",
            name="ck_planner_accounts_revision_positive",
        ),
    )
    op.create_index(
        "uq_planner_accounts_single_administrator",
        "planner_accounts",
        ["is_administrator"],
        unique=True,
        sqlite_where=sa.text("is_administrator = 1"),
    )

    op.create_table(
        "planner_account_access",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("planner_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("secret_digest", sa.String(64), nullable=False),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", name="uq_planner_account_access_account_id"),
        sa.UniqueConstraint("secret_digest", name="uq_planner_account_access_secret_digest"),
        sa.CheckConstraint(
            "length(secret_digest) = 64",
            name="ck_planner_account_access_digest_length",
        ),
        sa.CheckConstraint(
            "purpose IN ('setup', 'reset', 'reactivation')",
            name="ck_planner_account_access_purpose",
        ),
        sa.CheckConstraint(
            "expires_at > issued_at",
            name="ck_planner_account_access_expiry",
        ),
    )

    op.create_table(
        "planner_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("planner_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("secret_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", name="uq_planner_sessions_account_id"),
        sa.UniqueConstraint("secret_digest", name="uq_planner_sessions_secret_digest"),
        sa.CheckConstraint(
            "length(secret_digest) = 64",
            name="ck_planner_sessions_digest_length",
        ),
        sa.CheckConstraint(
            "last_activity_at >= created_at",
            name="ck_planner_sessions_activity_sequence",
        ),
        sa.CheckConstraint(
            "absolute_expires_at > created_at",
            name="ck_planner_sessions_expiry",
        ),
    )

    op.create_table(
        "planner_startup_credentials",
        sa.Column("secret_digest", sa.String(64), primary_key=True),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(secret_digest) = 64",
            name="ck_planner_startup_credentials_digest_length",
        ),
        sa.CheckConstraint(
            "purpose IN ('bootstrap', 'recovery')",
            name="ck_planner_startup_credentials_purpose",
        ),
        sa.CheckConstraint(
            "state IN ('current', 'consumed', 'replaced')",
            name="ck_planner_startup_credentials_state",
        ),
        sa.CheckConstraint(
            "(state = 'current' AND retired_at IS NULL) OR "
            "(state IN ('consumed', 'replaced') AND retired_at IS NOT NULL)",
            name="ck_planner_startup_credentials_retirement",
        ),
    )
    op.create_index(
        "uq_planner_startup_credentials_current_purpose",
        "planner_startup_credentials",
        ["purpose"],
        unique=True,
        sqlite_where=sa.text("state = 'current'"),
    )


def downgrade() -> None:
    op.drop_table("planner_startup_credentials")
    op.drop_table("planner_sessions")
    op.drop_table("planner_account_access")
    op.drop_table("planner_accounts")
