"""Allow the separate Standard Optimized identity, preserving existing receipts."""
import sqlalchemy as sa
from alembic import op

revision = '0016_standard_optimized'
down_revision = '0015_teaching_strategy_identity'
branch_labels = None
depends_on = None


def _replace_checks(algorithms, profiles, width):
    with op.batch_alter_table('optimization_operations') as batch:
        batch.drop_constraint('ck_optimization_algorithm', type_='check')
        batch.drop_constraint('ck_optimization_strategy_profile', type_='check')
        batch.alter_column('algorithm', type_=sa.String(width), existing_type=sa.String(16 if width == 32 else 32), existing_nullable=False)
        batch.create_check_constraint('ck_optimization_algorithm', f'algorithm IN ({algorithms})')
        batch.create_check_constraint('ck_optimization_strategy_profile', f'strategy_profile IN ({profiles})')


def upgrade():
    _replace_checks("'standard','cohort','lecturer','standard_optimized'",
        "'standard-v1','heuristic-v1','standard-optimized-v1'", 32)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT count(*) FROM optimization_operations WHERE algorithm='standard_optimized' OR strategy_profile='standard-optimized-v1'")).scalar():
        raise ValueError('Standard Optimized receipts must be retained; downgrade refused')
    _replace_checks("'standard','cohort','lecturer'", "'standard-v1','heuristic-v1'", 16)
