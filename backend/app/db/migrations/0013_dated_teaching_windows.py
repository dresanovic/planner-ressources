"""Retain window identities/references while admitting exact-date opportunities."""
import sqlalchemy as sa
from alembic import op

revision = "0013_dated_teaching_windows"
down_revision = "0012_preferred_session_units"
branch_labels = None
depends_on = None


def upgrade():
    # Startup disables SQLite foreign keys outside the transaction. Batch copying
    # keeps all existing IDs and incoming references; never rename the source table.
    with op.batch_alter_table("study_type_time_windows", recreate="always") as batch:
        batch.add_column(sa.Column("kind", sa.String(10), nullable=False, server_default="weekly"))
        batch.add_column(sa.Column("date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("is_intensive", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch.alter_column("weekday", existing_type=sa.Integer(), nullable=True)
        batch.drop_constraint("uq_study_type_time_window_exact", type_="unique")
        batch.create_check_constraint("ck_time_window_kind", "kind IN ('weekly','dated')")
        batch.create_check_constraint("ck_time_window_shape", "(kind='weekly' AND weekday IS NOT NULL AND weekday BETWEEN 0 AND 6 AND date IS NULL AND is_intensive=0) OR (kind='dated' AND weekday IS NULL AND date IS NOT NULL AND length(date)=10 AND date(date,'+0 days') IS NOT NULL AND date(date,'+0 days')=date)")
        batch.create_check_constraint("ck_time_window_interval", "end_time > start_time")
        batch.create_check_constraint("ck_time_window_revision", "revision > 0")
        batch.create_check_constraint("ck_time_window_flags", "is_intensive IN (0,1) AND is_active IN (0,1)")
        batch.create_index("uq_time_window_weekly", ["study_type_id", "weekday", "start_time", "end_time"], unique=True, sqlite_where=sa.text("kind='weekly'"))
        batch.create_index("uq_time_window_dated", ["study_type_id", "date", "start_time", "end_time"], unique=True, sqlite_where=sa.text("kind='dated'"))
