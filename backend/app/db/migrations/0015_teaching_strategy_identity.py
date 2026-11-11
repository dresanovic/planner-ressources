"""Capture teaching strategy identity without rewriting historical saved JSON."""
import sqlalchemy as sa
from alembic import op

revision = '0015_teaching_strategy_identity'
down_revision = '0014_course_overall_units'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('optimization_operations') as batch:
        batch.add_column(sa.Column('algorithm', sa.String(16), nullable=False, server_default='standard'))
        batch.add_column(sa.Column('strategy_profile', sa.String(32), nullable=False, server_default='standard-v1'))
        batch.add_column(sa.Column('strategy_settings', sa.JSON(), nullable=False,
            server_default=sa.text("'{\"version\":\"legacy-standard-v1\"}'")))
        batch.create_check_constraint('ck_optimization_algorithm', "algorithm IN ('standard','cohort','lecturer')")
        batch.create_check_constraint('ck_optimization_strategy_profile', "strategy_profile IN ('standard-v1','heuristic-v1')")
        batch.create_check_constraint('ck_optimization_strategy_settings', "json_valid(strategy_settings) AND json_type(strategy_settings) = 'object'")


def downgrade():
    with op.batch_alter_table('optimization_operations') as batch:
        for name in ('algorithm', 'strategy_profile', 'strategy_settings'):
            batch.drop_constraint('ck_optimization_' + name, type_='check')
        for name in ('strategy_settings', 'strategy_profile', 'algorithm'):
            batch.drop_column(name)
