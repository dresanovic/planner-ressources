"""add institution holidays

Revision ID: 0005_institution_holidays
Revises: 0004_resource_eligibility_availability
Create Date: 2026-07-20
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_institution_holidays"
down_revision = "0004_resource_eligibility_availability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institution_holidays",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("date", name="uq_institution_holidays_date"),
        sa.CheckConstraint(
            "revision > 0",
            name="ck_institution_holidays_revision_positive",
        ),
    )


def downgrade() -> None:
    op.drop_table("institution_holidays")

