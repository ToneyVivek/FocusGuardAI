"""add_activity_events_table

Revision ID: f1g2h3i4j5k6
Revises: e5f6g7h8i9j0k
Create Date: 2026-07-22 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1g2h3i4j5k6'
down_revision: Union[str, Sequence[str], None] = 'e5f6g7h8i9j0k'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create activity_events table
    op.create_table(
        'activity_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('browser_name', sa.String(length=100), nullable=False),
        sa.Column('tab_id', sa.Integer(), nullable=True),
        sa.Column('window_id', sa.Integer(), nullable=True),
        sa.Column('website_url', sa.String(length=2048), nullable=True),
        sa.Column('website_domain', sa.String(length=255), nullable=True),
        sa.Column('page_title', sa.String(length=500), nullable=True),
        sa.Column('previous_url', sa.String(length=2048), nullable=True),
        sa.Column('previous_domain', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_activity_events_id'), 'activity_events', ['id'], unique=False)
    op.create_index(op.f('ix_activity_events_organization_id'), 'activity_events', ['organization_id'], unique=False)
    op.create_index(op.f('ix_activity_events_user_id'), 'activity_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_activity_events_event_id'), 'activity_events', ['event_id'], unique=False)
    op.create_index(op.f('ix_activity_events_event_type'), 'activity_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_activity_events_tab_id'), 'activity_events', ['tab_id'], unique=False)
    op.create_index(op.f('ix_activity_events_window_id'), 'activity_events', ['window_id'], unique=False)
    op.create_index(op.f('ix_activity_events_website_domain'), 'activity_events', ['website_domain'], unique=False)
    op.create_index(op.f('ix_activity_events_timestamp'), 'activity_events', ['timestamp'], unique=False)
    
    # Create composite indexes for efficient querying
    op.create_index('idx_activity_org_user_time', 'activity_events', ['organization_id', 'user_id', 'timestamp'], unique=False)
    op.create_index('idx_activity_org_type_time', 'activity_events', ['organization_id', 'event_type', 'timestamp'], unique=False)
    op.create_index('idx_activity_tab_time', 'activity_events', ['user_id', 'tab_id', 'timestamp'], unique=False)
    op.create_index('idx_activity_window_time', 'activity_events', ['user_id', 'window_id', 'timestamp'], unique=False)
    op.create_index('idx_activity_domain_time', 'activity_events', ['organization_id', 'website_domain', 'timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop composite indexes
    op.drop_index('idx_activity_domain_time', table_name='activity_events')
    op.drop_index('idx_activity_window_time', table_name='activity_events')
    op.drop_index('idx_activity_tab_time', table_name='activity_events')
    op.drop_index('idx_activity_org_type_time', table_name='activity_events')
    op.drop_index('idx_activity_org_user_time', table_name='activity_events')
    
    # Drop single-column indexes
    op.drop_index(op.f('ix_activity_events_timestamp'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_website_domain'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_window_id'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_tab_id'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_event_type'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_event_id'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_user_id'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_organization_id'), table_name='activity_events')
    op.drop_index(op.f('ix_activity_events_id'), table_name='activity_events')
    
    # Drop table
    op.drop_table('activity_events')
