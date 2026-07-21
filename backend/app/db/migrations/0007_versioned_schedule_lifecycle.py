"""add versioned schedule review and publication lifecycle

Revision ID: 0007_versioned_schedule_lifecycle
Revises: 0006_conflict_aware_exam_scheduling
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_versioned_schedule_lifecycle"
down_revision = "0006_conflict_aware_exam_scheduling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedule_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column(
            "origin_revision_id",
            sa.Integer(),
            sa.ForeignKey("schedule_revisions.id"),
            nullable=True,
        ),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("snapshot_schema_version", sa.Integer(), nullable=True),
        sa.Column("snapshot_document", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.Column(
            "state_changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.UniqueConstraint(
            "semester_id", "revision_number", name="uq_schedule_revision_number"
        ),
        sa.CheckConstraint(
            "revision_number > 0", name="ck_schedule_revision_number_positive"
        ),
        sa.CheckConstraint("row_version > 0", name="ck_schedule_revision_version_positive"),
        sa.CheckConstraint(
            "state IN ('draft', 'ready_for_review', 'published', 'superseded', 'abandoned')",
            name="ck_schedule_revision_state",
        ),
        sa.CheckConstraint(
            "(state IN ('draft', 'ready_for_review') AND published_at IS NULL) OR "
            "(state IN ('published', 'superseded') AND published_at IS NOT NULL "
            "AND snapshot_schema_version IS NOT NULL AND snapshot_document IS NOT NULL) OR "
            "(state = 'abandoned' AND published_at IS NULL "
            "AND snapshot_schema_version IS NOT NULL AND snapshot_document IS NOT NULL)",
            name="ck_schedule_revision_state_content",
        ),
    )
    op.create_index(
        "uq_schedule_revision_active_working",
        "schedule_revisions",
        ["semester_id"],
        unique=True,
        sqlite_where=sa.text("state IN ('draft', 'ready_for_review')"),
    )
    op.create_index(
        "uq_schedule_revision_current_publication",
        "schedule_revisions",
        ["semester_id"],
        unique=True,
        sqlite_where=sa.text("state = 'published'"),
    )
    op.create_table(
        "schedule_revision_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column(
            "schedule_revision_id",
            sa.Integer(),
            sa.ForeignKey("schedule_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("from_state", sa.String(30), nullable=True),
        sa.Column("to_state", sa.String(30), nullable=False),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.UniqueConstraint(
            "semester_id", "event_sequence", name="uq_schedule_revision_event_sequence"
        ),
        sa.CheckConstraint(
            "event_sequence > 0", name="ck_schedule_revision_event_sequence_positive"
        ),
        sa.CheckConstraint(
            "event_type IN ('created', 'marked_ready', 'returned_to_draft', 'published', "
            "'superseded', 'abandoned', 'restored')",
            name="ck_schedule_revision_event_type",
        ),
        sa.CheckConstraint(
            "to_state IN ('draft', 'ready_for_review', 'published', 'superseded', 'abandoned')",
            name="ck_schedule_revision_event_to_state",
        ),
        sa.CheckConstraint(
            "from_state IS NULL OR from_state IN "
            "('draft', 'ready_for_review', 'published', 'superseded', 'abandoned')",
            name="ck_schedule_revision_event_from_state",
        ),
        sa.CheckConstraint(
            "(event_type = 'created' AND from_state IS NULL) OR "
            "(event_type <> 'created' AND from_state IS NOT NULL)",
            name="ck_schedule_revision_event_created_source",
        ),
    )
    op.create_index(
        "ix_schedule_revision_events_revision",
        "schedule_revision_events",
        ["schedule_revision_id"],
    )

    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO schedule_revisions "
            "(semester_id, revision_number, state, row_version, created_at, state_changed_at, updated_at) "
            "SELECT semester_id, 1, 'draft', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP "
            "FROM ("
            "SELECT semester_id FROM draft_schedules "
            "UNION SELECT semester_id FROM exam_sessions"
            ") populated_semesters ORDER BY semester_id"
        )
    )
    connection.execute(
        sa.text(
            "INSERT INTO schedule_revision_events "
            "(semester_id, schedule_revision_id, event_sequence, event_type, from_state, to_state, occurred_at) "
            "SELECT semester_id, id, 1, 'created', NULL, 'draft', created_at "
            "FROM schedule_revisions ORDER BY semester_id"
        )
    )


def downgrade() -> None:
    connection = op.get_bind()
    unrepresentable = connection.execute(
        sa.text(
            "SELECT r.id FROM schedule_revisions r "
            "WHERE r.state <> 'draft' OR r.revision_number <> 1 OR r.row_version <> 1 "
            "OR r.origin_revision_id IS NOT NULL OR r.snapshot_document IS NOT NULL "
            "OR NOT EXISTS ("
            "  SELECT 1 FROM draft_schedules d WHERE d.semester_id = r.semester_id "
            "  UNION SELECT 1 FROM exam_sessions e WHERE e.semester_id = r.semester_id"
            ") OR (SELECT COUNT(*) FROM schedule_revision_events ev "
            "      WHERE ev.schedule_revision_id = r.id) <> 1 "
            "OR EXISTS (SELECT 1 FROM schedule_revision_events ev "
            "           WHERE ev.schedule_revision_id = r.id "
            "           AND (ev.event_sequence <> 1 OR ev.event_type <> 'created' "
            "                OR ev.from_state IS NOT NULL OR ev.to_state <> 'draft')) "
            "LIMIT 1"
        )
    ).first()
    multiple = connection.execute(
        sa.text(
            "SELECT semester_id FROM schedule_revisions "
            "GROUP BY semester_id HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if unrepresentable is not None or multiple is not None:
        raise RuntimeError(
            "Versioned schedule lifecycle history cannot be represented by the FS-012 schema; "
            "downgrade refused to preserve revision data."
        )

    op.drop_table("schedule_revision_events")
    op.drop_table("schedule_revisions")
