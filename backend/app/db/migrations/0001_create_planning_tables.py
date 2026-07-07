"""create planning tables

Revision ID: 0001_create_planning_tables
Revises:
Create Date: 2026-07-06
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_planning_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lecturers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    op.create_table(
        "cohorts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("student_count", sa.Integer(), nullable=False),
    )
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
    )
    op.create_table(
        "semesters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
    )
    op.create_table(
        "study_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
    )
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("total_units", sa.Integer(), nullable=False),
        sa.Column("min_session_units", sa.Integer(), nullable=False),
        sa.Column("max_session_units", sa.Integer(), nullable=False),
        sa.Column("lecturer_id", sa.Integer(), sa.ForeignKey("lecturers.id"), nullable=False),
        sa.Column("cohort_id", sa.Integer(), sa.ForeignKey("cohorts.id"), nullable=False),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("study_type_id", sa.Integer(), sa.ForeignKey("study_types.id"), nullable=False),
    )
    op.create_table(
        "study_type_time_windows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("study_type_id", sa.Integer(), sa.ForeignKey("study_types.id"), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )
    op.create_table(
        "draft_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False, unique=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column(
            "selected_time_window_id",
            sa.Integer(),
            sa.ForeignKey("study_type_time_windows.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "draft_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("draft_schedule_id", sa.Integer(), sa.ForeignKey("draft_schedules.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("lecturer_id", sa.Integer(), sa.ForeignKey("lecturers.id"), nullable=False),
        sa.Column("cohort_id", sa.Integer(), sa.ForeignKey("cohorts.id"), nullable=False),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("time_window_id", sa.Integer(), sa.ForeignKey("study_type_time_windows.id"), nullable=False),
        sa.UniqueConstraint("draft_schedule_id", "date", name="uq_draft_session_day"),
    )


def downgrade() -> None:
    for table_name in (
        "draft_sessions",
        "draft_schedules",
        "study_type_time_windows",
        "courses",
        "study_types",
        "semesters",
        "rooms",
        "cohorts",
        "lecturers",
    ):
        op.drop_table(table_name)
