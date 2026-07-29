"""add accountless lecturer review links, feedback, and misuse state

Revision ID: 0009_lecturer_token_review
Revises: 0008_calendar_workspace_outcomes
Create Date: 2026-07-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0009_lecturer_token_review"
down_revision = "0008_calendar_workspace_outcomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lecturer_review_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "schedule_revision_id",
            sa.Integer(),
            sa.ForeignKey("schedule_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lecturer_id",
            sa.Integer(),
            sa.ForeignKey("lecturers.id"),
            nullable=False,
        ),
        sa.Column("intended_lecturer_name", sa.String(200), nullable=False),
        sa.Column("secret_digest", sa.String(64), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="active",
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_reason", sa.String(30), nullable=True),
        sa.Column(
            "replaced_by_id",
            sa.Integer(),
            sa.ForeignKey("lecturer_review_links.id"),
            nullable=True,
        ),
        sa.Column(
            "access_blocked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "secret_digest",
            name="uq_lecturer_review_links_secret_digest",
        ),
        sa.CheckConstraint(
            "length(secret_digest) = 64",
            name="ck_lecturer_review_links_digest_length",
        ),
        sa.CheckConstraint(
            "duration_days IN (1, 2, 3)",
            name="ck_lecturer_review_links_duration",
        ),
        sa.CheckConstraint(
            "expires_at > issued_at",
            name="ck_lecturer_review_links_expiry",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'expired', 'revoked', 'replaced', 'revision_ended')",
            name="ck_lecturer_review_links_status",
        ),
        sa.CheckConstraint(
            "end_reason IS NULL OR end_reason IN "
            "('expired', 'revoked', 'replaced', 'abandoned', 'superseded')",
            name="ck_lecturer_review_links_end_reason",
        ),
        sa.CheckConstraint(
            "(status = 'active' AND ended_at IS NULL AND end_reason IS NULL "
            "AND replaced_by_id IS NULL) OR "
            "(status = 'expired' AND ended_at IS NOT NULL "
            "AND end_reason = 'expired' AND replaced_by_id IS NULL) OR "
            "(status = 'revoked' AND ended_at IS NOT NULL "
            "AND end_reason = 'revoked' AND replaced_by_id IS NULL) OR "
            "(status = 'replaced' AND ended_at IS NOT NULL "
            "AND end_reason = 'replaced' AND replaced_by_id IS NOT NULL) OR "
            "(status = 'revision_ended' AND ended_at IS NOT NULL "
            "AND end_reason IN ('abandoned', 'superseded') "
            "AND replaced_by_id IS NULL)",
            name="ck_lecturer_review_links_end_state",
        ),
    )
    op.create_index(
        "uq_lecturer_review_link_active_pair",
        "lecturer_review_links",
        ["schedule_revision_id", "lecturer_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ix_lecturer_review_links_revision_lecturer",
        "lecturer_review_links",
        ["schedule_revision_id", "lecturer_id", "issued_at"],
    )
    op.create_index(
        "ix_lecturer_review_links_status_expiry",
        "lecturer_review_links",
        ["status", "expires_at"],
    )

    op.create_table(
        "lecturer_review_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "review_link_id",
            sa.Integer(),
            sa.ForeignKey("lecturer_review_links.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("session_kind", sa.String(20), nullable=True),
        sa.Column("source_session_id", sa.Integer(), nullable=True),
        sa.Column("comment_text", sa.Text(), nullable=True),
        sa.Column(
            "session_context",
            sa.JSON(none_as_null=True),
            nullable=True,
        ),
        sa.Column("client_submission_id", sa.String(36), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "review_link_id",
            "client_submission_id",
            name="uq_lecturer_review_feedback_submission",
        ),
        sa.CheckConstraint(
            "kind IN ('revision_comment', 'session_comment', 'impossible_session')",
            name="ck_lecturer_review_feedback_kind",
        ),
        sa.CheckConstraint(
            "session_kind IS NULL OR session_kind IN ('teaching', 'exam')",
            name="ck_lecturer_review_feedback_session_kind",
        ),
        sa.CheckConstraint(
            "length(client_submission_id) = 36",
            name="ck_lecturer_review_feedback_submission_id_length",
        ),
        sa.CheckConstraint(
            "length(request_fingerprint) = 64",
            name="ck_lecturer_review_feedback_fingerprint_length",
        ),
        sa.CheckConstraint(
            "(kind = 'revision_comment' "
            "AND session_kind IS NULL AND source_session_id IS NULL "
            "AND session_context IS NULL AND comment_text IS NOT NULL "
            "AND length(trim(comment_text)) BETWEEN 1 AND 2000) OR "
            "(kind = 'session_comment' "
            "AND session_kind IS NOT NULL AND source_session_id > 0 "
            "AND session_context IS NOT NULL AND comment_text IS NOT NULL "
            "AND length(trim(comment_text)) BETWEEN 1 AND 2000) OR "
            "(kind = 'impossible_session' "
            "AND session_kind IS NOT NULL AND source_session_id > 0 "
            "AND session_context IS NOT NULL "
            "AND (comment_text IS NULL "
            "OR length(trim(comment_text)) BETWEEN 1 AND 2000))",
            name="ck_lecturer_review_feedback_shape",
        ),
    )
    op.create_index(
        "ix_lecturer_review_feedback_link_submitted",
        "lecturer_review_feedback",
        ["review_link_id", "submitted_at"],
    )
    op.create_index(
        "ix_lecturer_review_feedback_session",
        "lecturer_review_feedback",
        ["review_link_id", "session_kind", "source_session_id"],
    )

    op.create_table(
        "lecturer_review_activity_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column(
            "review_link_id",
            sa.Integer(),
            sa.ForeignKey("lecturer_review_links.id"),
            nullable=True,
        ),
        sa.Column(
            "schedule_revision_id",
            sa.Integer(),
            sa.ForeignKey("schedule_revisions.id"),
            nullable=True,
        ),
        sa.Column(
            "lecturer_id",
            sa.Integer(),
            sa.ForeignKey("lecturers.id"),
            nullable=True,
        ),
        sa.Column(
            "feedback_id",
            sa.Integer(),
            sa.ForeignKey("lecturer_review_feedback.id"),
            nullable=True,
        ),
        sa.Column("reason_code", sa.String(40), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.CheckConstraint(
            "event_type IN ('link_issued', 'link_expired', 'link_revoked', "
            "'link_replaced', 'revision_ended', 'access_accepted', "
            "'access_rejected', 'feedback_accepted', 'feedback_rejected', "
            "'misuse_limit_activated')",
            name="ck_lecturer_review_activity_event_type",
        ),
        sa.CheckConstraint(
            "reason_code IS NULL OR reason_code IN "
            "('expired', 'revoked', 'replaced', 'abandoned', 'superseded', "
            "'malformed_secret', 'unknown_secret', 'source_limited', "
            "'view_limited', 'feedback_limited', 'out_of_scope', "
            "'stale_session', 'invalid_feedback', 'idempotent_replay')",
            name="ck_lecturer_review_activity_reason_code",
        ),
    )
    op.create_index(
        "ix_lecturer_review_activity_link_occurred",
        "lecturer_review_activity_events",
        ["review_link_id", "occurred_at"],
    )
    op.create_index(
        "ix_lecturer_review_activity_type_occurred",
        "lecturer_review_activity_events",
        ["event_type", "occurred_at"],
    )
    op.create_index(
        "uq_lecturer_review_activity_link_expired",
        "lecturer_review_activity_events",
        ["review_link_id"],
        unique=True,
        sqlite_where=sa.text(
            "event_type = 'link_expired' AND review_link_id IS NOT NULL"
        ),
    )

    op.create_table(
        "lecturer_review_invalid_source_states",
        sa.Column("source_fingerprint", sa.String(64), primary_key=True),
        sa.Column("attempt_timestamps", sa.JSON(), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_relevant_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(source_fingerprint) = 64",
            name="ck_lecturer_review_invalid_source_fingerprint_length",
        ),
        sa.CheckConstraint(
            "json_valid(attempt_timestamps) "
            "AND json_type(attempt_timestamps) = 'array' "
            "AND json_array_length(attempt_timestamps) <= 20",
            name="ck_lecturer_review_invalid_source_attempts",
        ),
    )
    op.create_index(
        "ix_lecturer_review_invalid_source_cleanup",
        "lecturer_review_invalid_source_states",
        ["last_relevant_at"],
    )


def downgrade() -> None:
    op.drop_table("lecturer_review_invalid_source_states")
    op.drop_table("lecturer_review_activity_events")
    op.drop_table("lecturer_review_feedback")
    op.drop_table("lecturer_review_links")
