"""upgrade_ai_report_cache_for_production

Revision ID: g1h2i3j4k5l6
Revises: e5f6g7h8i9j0k
Create Date: 2026-08-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, Sequence[str], None] = 'e5f6g7h8i9j0k'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if ai_report_cache table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'ai_report_cache' not in tables:
        # Table doesn't exist, create it with new schema
        op.create_table(
            'ai_report_cache',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('report_type', sa.String(length=20), nullable=False),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('analytics_hash', sa.String(length=64), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('prompt_version', sa.String(length=20), nullable=False),
            sa.Column('raw_llm_response', sa.Text(), nullable=False),
            sa.Column('parsed_summary', sa.JSON(), nullable=False),
            sa.Column('cache_metadata', sa.JSON(), nullable=False),
            sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index(op.f('ix_ai_report_cache_id'), 'ai_report_cache', ['id'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_user_id'), 'ai_report_cache', ['user_id'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_report_type'), 'ai_report_cache', ['report_type'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_start_date'), 'ai_report_cache', ['start_date'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_end_date'), 'ai_report_cache', ['end_date'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_analytics_hash'), 'ai_report_cache', ['analytics_hash'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_expires_at'), 'ai_report_cache', ['expires_at'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_provider'), 'ai_report_cache', ['provider'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_model'), 'ai_report_cache', ['model'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_prompt_version'), 'ai_report_cache', ['prompt_version'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_created_at'), 'ai_report_cache', ['created_at'], unique=False)
        op.create_index(op.f('ix_ai_report_cache_updated_at'), 'ai_report_cache', ['updated_at'], unique=False)
        
        # Create composite index for efficient cache lookup
        op.create_index(
            'idx_ai_cache_lookup',
            'ai_report_cache',
            ['user_id', 'report_type', 'start_date', 'end_date', 'analytics_hash', 'provider', 'model', 'prompt_version'],
            unique=True
        )
        
        # Create index for provider/model/version queries
        op.create_index('idx_ai_cache_version', 'ai_report_cache', ['provider', 'model', 'prompt_version'], unique=False)
    else:
        # Table exists, upgrade it
        # Drop old composite index if it exists
        indexes = inspector.get_indexes('ai_report_cache')
        index_names = [idx['name'] for idx in indexes]
        
        if 'idx_ai_cache_lookup' in index_names:
            op.drop_index('idx_ai_cache_lookup', table_name='ai_report_cache')
        
        # Check if summary_json column exists before dropping it
        columns = [col['name'] for col in inspector.get_columns('ai_report_cache')]
        
        # Add new columns for cache versioning if they don't exist
        if 'provider' not in columns:
            op.add_column('ai_report_cache', sa.Column('provider', sa.String(length=50), nullable=False, server_default='gemini'))
        if 'model' not in columns:
            op.add_column('ai_report_cache', sa.Column('model', sa.String(length=100), nullable=False, server_default='gemini-flash-latest'))
        if 'prompt_version' not in columns:
            op.add_column('ai_report_cache', sa.Column('prompt_version', sa.String(length=20), nullable=False, server_default='1.0'))
        
        # Add new columns for structured storage if they don't exist
        if 'raw_llm_response' not in columns:
            op.add_column('ai_report_cache', sa.Column('raw_llm_response', sa.Text(), nullable=False, server_default=''))
        if 'cache_metadata' not in columns:
            op.add_column('ai_report_cache', sa.Column('cache_metadata', sa.JSON(), nullable=False, server_default='{}'))
        
        # Drop old summary_json column if it exists
        if 'summary_json' in columns:
            op.drop_column('ai_report_cache', 'summary_json')
        
        # Add parsed_summary column if it doesn't exist
        if 'parsed_summary' not in columns:
            op.add_column('ai_report_cache', sa.Column('parsed_summary', sa.JSON(), nullable=False, server_default='{}'))
        
        # Add TimestampMixin columns if they don't exist
        if 'created_at' not in columns:
            op.add_column('ai_report_cache', sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
        if 'updated_at' not in columns:
            op.add_column('ai_report_cache', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))
        
        # Create indexes for new columns if they don't exist
        if 'ix_ai_report_cache_provider' not in index_names:
            op.create_index(op.f('ix_ai_report_cache_provider'), 'ai_report_cache', ['provider'], unique=False)
        if 'ix_ai_report_cache_model' not in index_names:
            op.create_index(op.f('ix_ai_report_cache_model'), 'ai_report_cache', ['model'], unique=False)
        if 'ix_ai_report_cache_prompt_version' not in index_names:
            op.create_index(op.f('ix_ai_report_cache_prompt_version'), 'ai_report_cache', ['prompt_version'], unique=False)
        if 'ix_ai_report_cache_created_at' not in index_names:
            op.create_index(op.f('ix_ai_report_cache_created_at'), 'ai_report_cache', ['created_at'], unique=False)
        if 'ix_ai_report_cache_updated_at' not in index_names:
            op.create_index(op.f('ix_ai_report_cache_updated_at'), 'ai_report_cache', ['updated_at'], unique=False)
        
        # Create new composite index with versioning fields if it doesn't exist
        if 'idx_ai_cache_lookup' not in index_names:
            op.create_index(
                'idx_ai_cache_lookup',
                'ai_report_cache',
                ['user_id', 'report_type', 'start_date', 'end_date', 'analytics_hash', 'provider', 'model', 'prompt_version'],
                unique=True
            )
        
        # Create index for provider/model/version queries if it doesn't exist
        if 'idx_ai_cache_version' not in index_names:
            op.create_index('idx_ai_cache_version', 'ai_report_cache', ['provider', 'model', 'prompt_version'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'ai_report_cache' not in tables:
        # Table doesn't exist, nothing to downgrade
        return
    
    indexes = inspector.get_indexes('ai_report_cache')
    index_names = [idx['name'] for idx in indexes]
    
    # Drop new indexes if they exist
    if 'idx_ai_cache_version' in index_names:
        op.drop_index('idx_ai_cache_version', table_name='ai_report_cache')
    if 'idx_ai_cache_lookup' in index_names:
        op.drop_index('idx_ai_cache_lookup', table_name='ai_report_cache')
    if 'ix_ai_report_cache_prompt_version' in index_names:
        op.drop_index(op.f('ix_ai_report_cache_prompt_version'), table_name='ai_report_cache')
    if 'ix_ai_report_cache_model' in index_names:
        op.drop_index(op.f('ix_ai_report_cache_model'), table_name='ai_report_cache')
    if 'ix_ai_report_cache_provider' in index_names:
        op.drop_index(op.f('ix_ai_report_cache_provider'), table_name='ai_report_cache')
    
    columns = [col['name'] for col in inspector.get_columns('ai_report_cache')]
    
    # Drop new columns if they exist
    if 'parsed_summary' in columns:
        op.drop_column('ai_report_cache', 'parsed_summary')
    if 'cache_metadata' in columns:
        op.drop_column('ai_report_cache', 'cache_metadata')
    if 'raw_llm_response' in columns:
        op.drop_column('ai_report_cache', 'raw_llm_response')
    if 'prompt_version' in columns:
        op.drop_column('ai_report_cache', 'prompt_version')
    if 'model' in columns:
        op.drop_column('ai_report_cache', 'model')
    if 'provider' in columns:
        op.drop_column('ai_report_cache', 'provider')
    
    # Restore old summary_json column if it doesn't exist
    if 'summary_json' not in columns:
        op.add_column('ai_report_cache', sa.Column('summary_json', sa.JSON(), nullable=False, server_default='{}'))
    
    # Restore old composite index if it doesn't exist
    if 'idx_ai_cache_lookup' not in index_names:
        op.create_index(
            'idx_ai_cache_lookup',
            'ai_report_cache',
            ['user_id', 'report_type', 'start_date', 'end_date', 'analytics_hash'],
            unique=True
        )
