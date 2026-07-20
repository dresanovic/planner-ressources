"""add conflict-aware exam scheduling

Revision ID: 0006_conflict_aware_exam_scheduling
Revises: 0005_institution_holidays
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_conflict_aware_exam_scheduling"
down_revision = "0005_institution_holidays"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_exam_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("identifier", sa.String(200), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("recommended_start_override", sa.Date(), nullable=True),
        sa.Column("recommended_end_override", sa.Date(), nullable=True),
        sa.Column("required_capacity", sa.Integer(), nullable=True),
        sa.Column("exam_type", sa.String(200), nullable=True),
        sa.Column("responsible_lecturer_id", sa.Integer(), sa.ForeignKey("lecturers.id"), nullable=True),
        sa.Column("configuration_consumed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("course_id", "semester_id", name="uq_course_exam_configuration_course_semester"),
        sa.CheckConstraint("duration_minutes IS NULL OR duration_minutes > 0", name="ck_exam_configuration_duration_positive"),
        sa.CheckConstraint("required_capacity IS NULL OR required_capacity > 0", name="ck_exam_configuration_capacity_positive"),
        sa.CheckConstraint("revision > 0", name="ck_exam_configuration_revision_positive"),
        sa.CheckConstraint("(recommended_start_override IS NULL AND recommended_end_override IS NULL) OR (recommended_start_override IS NOT NULL AND recommended_end_override IS NOT NULL AND recommended_end_override >= recommended_start_override)", name="ck_exam_configuration_recommendation_pair"),
    )
    op.create_table(
        "exam_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("cohort_id", sa.Integer(), sa.ForeignKey("cohorts.id"), nullable=False),
        sa.Column("lecturer_id", sa.Integer(), sa.ForeignKey("lecturers.id"), nullable=False),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("configuration_identifier", sa.String(200), nullable=False),
        sa.Column("configuration_revision", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("exam_type", sa.String(200), nullable=False),
        sa.Column("required_capacity", sa.Integer(), nullable=False),
        sa.Column("recommended_start_date", sa.Date(), nullable=False),
        sa.Column("recommended_end_date", sa.Date(), nullable=False),
        sa.Column("recommendation_was_overridden", sa.Boolean(), nullable=False),
        sa.Column("final_teaching_date", sa.Date(), nullable=False),
        sa.Column("final_teaching_end_time", sa.Time(), nullable=False),
        sa.Column("final_teaching_session_id_snapshot", sa.Integer(), nullable=False),
        sa.Column("course_name_snapshot", sa.String(200), nullable=False),
        sa.Column("semester_name_snapshot", sa.String(200), nullable=False),
        sa.Column("cohort_name_snapshot", sa.String(200), nullable=False),
        sa.Column("lecturer_name_snapshot", sa.String(200), nullable=False),
        sa.Column("lecturer_reference_snapshot", sa.String(100), nullable=False),
        sa.Column("room_name_snapshot", sa.String(200), nullable=False),
        sa.Column("room_reference_snapshot", sa.String(100), nullable=False),
        sa.CheckConstraint("duration_minutes > 0", name="ck_exam_session_duration_positive"),
        sa.CheckConstraint("required_capacity > 0", name="ck_exam_session_capacity_positive"),
        sa.CheckConstraint("revision > 0", name="ck_exam_session_revision_positive"),
        sa.CheckConstraint("end_time > start_time", name="ck_exam_session_interval"),
        sa.CheckConstraint("source IN ('generated', 'manual')", name="ck_exam_session_source"),
    )
    op.create_index("ix_exam_session_course_semester_date", "exam_sessions", ["course_id", "semester_id", "exam_date"])
    op.create_index("ix_exam_session_lecturer_occupancy", "exam_sessions", ["semester_id", "exam_date", "lecturer_id"])
    op.create_index("ix_exam_session_room_occupancy", "exam_sessions", ["semester_id", "exam_date", "room_id"])
    op.create_index("ix_exam_session_cohort_occupancy", "exam_sessions", ["semester_id", "exam_date", "cohort_id"])


def downgrade() -> None:
    op.drop_table("exam_sessions")
    op.drop_table("course_exam_configurations")
