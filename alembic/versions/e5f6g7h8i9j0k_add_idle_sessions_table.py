"""add_idle_sessions_table

Revision ID: e5f6g7h8i9j0k
Revises: d4e5f6g7h8i9
Create Date: 2026-07-15 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0k'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create idle_sessions table
    op.create_table(
        'idle_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('idle_start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('idle_end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_idle_sessions_id'), 'idle_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_idle_sessions_organization_id'), 'idle_sessions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_idle_sessions_user_id'), 'idle_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_idle_sessions_idle_start_time'), 'idle_sessions', ['idle_start_time'], unique=False)
    op.create_index(op.f('ix_idle_sessions_idle_end_time'), 'idle_sessions', ['idle_end_time'], unique=False)
    
    # Create composite indexes for efficient querying
    op.create_index('idx_idle_sessions_user_time', 'idle_sessions', ['user_id', 'idle_start_time', 'idle_end_time'], unique=False)
    op.create_index('idx_idle_sessions_org_time', 'idle_sessions', ['organization_id', 'idle_start_time'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop composite indexes
    op.drop_index('idx_idle_sessions_org_time', table_name='idle_sessions')
    op.drop_index('idx_idle_sessions_user_time', table_name='idle_sessions')
    
    # Drop single-column indexes
    op.drop_index(op.f('ix_idle_sessions_idle_end_time'), table_name='idle_sessions')
    op.drop_index(op.f('ix_idle_sessions_idle_start_time'), table_name='idle_sessions')
    op.drop_index(op.f('ix_idle_sessions_user_id'), table_name='idle_sessions')
    op.drop_index(op.f('ix_idle_sessions_organization_id'), table_name='idle_sessions')
    op.drop_index(op.f('ix_idle_sessions_id'), table_name='idle_sessions')
    
    # Drop table
    op.drop_table('idle_sessions')
