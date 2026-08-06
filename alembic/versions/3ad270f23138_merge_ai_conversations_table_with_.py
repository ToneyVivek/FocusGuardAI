"""merge ai conversations table with previous heads

Revision ID: 3ad270f23138
Revises: 526e261a4535, h1i2j3k4l5m6
Create Date: 2026-08-04 02:14:50.307011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ad270f23138'
down_revision: Union[str, Sequence[str], None] = ('526e261a4535', 'h1i2j3k4l5m6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
