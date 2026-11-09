"""Add informational course totals without changing the units used by planning."""
import sqlalchemy as sa
from alembic import op

revision = "0014_course_overall_units"
down_revision = "0013_dated_teaching_windows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("overall_units", sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE courses SET overall_units = total_units"))
    with op.batch_alter_table("courses") as batch:
        batch.alter_column("overall_units", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.drop_column("courses", "overall_units")
