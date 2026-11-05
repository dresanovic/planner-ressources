"""Add optional course session-size preference and initialize existing courses."""
import sqlalchemy as sa
from alembic import op

revision = "0012_preferred_session_units"
down_revision = "0011_optimization_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("preferred_session_units", sa.Float(), nullable=True))
    op.execute(sa.text("UPDATE courses SET preferred_session_units = (min_session_units + max_session_units) / 2.0"))


def downgrade() -> None:
    op.drop_column("courses", "preferred_session_units")
