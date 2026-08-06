"""merge activity_events and ai_cache heads

Revision ID: 526e261a4535
Revises: f1g2h3i4j5k6, g1h2i3j4k5l6
Create Date: 2026-08-04 01:30:40.678693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '526e261a4535'
down_revision: Union[str, Sequence[str], None] = ('f1g2h3i4j5k6', 'g1h2i3j4k5l6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
