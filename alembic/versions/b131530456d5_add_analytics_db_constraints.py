"""add_analytics_db_constraints

Revision ID: b131530456d5
Revises: 122f49227b55
Create Date: 2026-07-10 18:06:25.969043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b131530456d5'
down_revision: Union[str, Sequence[str], None] = '122f49227b55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add check constraint for duration_seconds > 0
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE browser_activities 
        ADD CONSTRAINT chk_duration_positive 
        CHECK (duration_seconds > 0)
    """))
    
    # Add unique constraint for duplicate prevention (idempotency)
    op.create_index(
        'idx_unique_session',
        'browser_activities',
        ['user_id', 'website_domain', 'session_start_time', 'session_end_time'],
        unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraint
    op.drop_index('idx_unique_session', table_name='browser_activities')
    
    # Drop check constraint
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE browser_activities 
        DROP CONSTRAINT IF EXISTS chk_duration_positive
    """))
