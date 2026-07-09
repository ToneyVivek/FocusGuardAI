"""add_username_to_browser_activities

Revision ID: 11d0f3eb3cfd
Revises: 5593d2413980
Create Date: 2026-07-09 20:28:09.351127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11d0f3eb3cfd'
down_revision: Union[str, Sequence[str], None] = '5593d2413980'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add username column to browser_activities table
    op.add_column('browser_activities', sa.Column('username', sa.String(length=255), nullable=True))
    # Create index on username for reporting queries
    op.create_index(op.f('ix_browser_activities_username'), 'browser_activities', ['username'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index and column
    op.drop_index(op.f('ix_browser_activities_username'), table_name='browser_activities')
    op.drop_column('browser_activities', 'username')
