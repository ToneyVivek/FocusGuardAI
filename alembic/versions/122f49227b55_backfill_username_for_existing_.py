"""backfill_username_for_existing_activities

Revision ID: 122f49227b55
Revises: 11d0f3eb3cfd
Create Date: 2026-07-09 20:35:05.534464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '122f49227b55'
down_revision: Union[str, Sequence[str], None] = '11d0f3eb3cfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Backfill username for existing browser_activities records by joining with users table."""
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        UPDATE browser_activities
        SET username = users.full_name
        FROM users
        WHERE browser_activities.user_id = users.id
          AND browser_activities.username IS NULL
          AND users.is_deleted = FALSE
    """))
    
    conn.execute(sa.text("""
        UPDATE browser_activities
        SET username = users.email
        FROM users
        WHERE browser_activities.user_id = users.id
          AND browser_activities.username IS NULL
    """))
    
    conn.execute(sa.text("""
        UPDATE browser_activities
        SET username = 'Unknown User'
        WHERE username IS NULL
    """))


def downgrade() -> None:
    """Downgrade schema."""
    pass