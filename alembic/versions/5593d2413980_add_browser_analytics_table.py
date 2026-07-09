"""add_browser_analytics_table

Revision ID: 5593d2413980
Revises: c717939e787d
Create Date: 2026-07-09 19:44:22.024627

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5593d2413980'
down_revision: Union[str, Sequence[str], None] = 'c717939e787d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create website_category enum using raw SQL with IF NOT EXISTS
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE websitecategory AS ENUM (
                'DEVELOPMENT', 'EDUCATION', 'SOCIAL_MEDIA', 'ENTERTAINMENT',
                'PRODUCTIVITY', 'COMMUNICATION', 'AI_TOOL', 'NEWS', 'SEARCH_ENGINE',
                'SHOPPING', 'OTHER'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create productivity_classification enum using raw SQL with IF NOT EXISTS
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE productivityclassification AS ENUM (
                'PRODUCTIVE', 'NON_PRODUCTIVE', 'NEUTRAL'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Reference existing enums
    website_category_enum = postgresql.ENUM(name='websitecategory', create_type=False)
    productivity_enum = postgresql.ENUM(name='productivityclassification', create_type=False)
    
    # Create browser_activities table
    op.create_table(
        'browser_activities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('browser_name', sa.String(length=100), nullable=False),
        sa.Column('website_url', sa.String(length=2048), nullable=False),
        sa.Column('website_domain', sa.String(length=255), nullable=False),
        sa.Column('page_title', sa.String(length=500), nullable=True),
        sa.Column('website_category', website_category_enum, nullable=False),
        sa.Column('productivity_classification', productivity_enum, nullable=False),
        sa.Column('session_start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('session_end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_browser_activities_id'), 'browser_activities', ['id'], unique=False)
    op.create_index(op.f('ix_browser_activities_organization_id'), 'browser_activities', ['organization_id'], unique=False)
    op.create_index(op.f('ix_browser_activities_user_id'), 'browser_activities', ['user_id'], unique=False)
    op.create_index(op.f('ix_browser_activities_username'), 'browser_activities', ['username'], unique=False)
    op.create_index(op.f('ix_browser_activities_website_domain'), 'browser_activities', ['website_domain'], unique=False)
    op.create_index(op.f('ix_browser_activities_website_category'), 'browser_activities', ['website_category'], unique=False)
    op.create_index(op.f('ix_browser_activities_productivity_classification'), 'browser_activities', ['productivity_classification'], unique=False)
    op.create_index(op.f('ix_browser_activities_session_start_time'), 'browser_activities', ['session_start_time'], unique=False)
    op.create_index(op.f('ix_browser_activities_session_end_time'), 'browser_activities', ['session_end_time'], unique=False)
    op.create_index(op.f('ix_browser_activities_duration_seconds'), 'browser_activities', ['duration_seconds'], unique=False)
    
    # Create composite indexes for performance
    op.create_index('idx_org_user_time', 'browser_activities', ['organization_id', 'user_id', 'session_start_time'], unique=False)
    op.create_index('idx_org_category_time', 'browser_activities', ['organization_id', 'website_category', 'session_start_time'], unique=False)
    op.create_index('idx_org_productivity_time', 'browser_activities', ['organization_id', 'productivity_classification', 'session_start_time'], unique=False)
    op.create_index('idx_org_domain_time', 'browser_activities', ['organization_id', 'website_domain', 'session_start_time'], unique=False)
    op.create_index('idx_org_time_range', 'browser_activities', ['organization_id', 'session_start_time', 'session_end_time'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_org_time_range', table_name='browser_activities')
    op.drop_index('idx_org_domain_time', table_name='browser_activities')
    op.drop_index('idx_org_productivity_time', table_name='browser_activities')
    op.drop_index('idx_org_category_time', table_name='browser_activities')
    op.drop_index('idx_org_user_time', table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_duration_seconds'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_session_end_time'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_session_start_time'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_productivity_classification'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_website_category'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_website_domain'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_username'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_user_id'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_organization_id'), table_name='browser_activities')
    op.drop_index(op.f('ix_browser_activities_id'), table_name='browser_activities')
    
    # Drop table
    op.drop_table('browser_activities')
    
    # Drop enums
    postgresql.ENUM(name='productivityclassification').drop(op.get_bind())
    postgresql.ENUM(name='websitecategory').drop(op.get_bind())
