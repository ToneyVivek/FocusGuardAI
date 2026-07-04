"""Hardening migration: drop refresh tokens, add tenant indexes

Revision ID: a1b2c3d4e5f6
Revises: cc45e579e6ee
Create Date: 2026-07-02 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "cc45e579e6ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove unused refresh token table (auth simplified to access tokens only)
    with op.batch_alter_table("user_refresh_tokens", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_refresh_tokens_token"))
        batch_op.drop_index(batch_op.f("ix_user_refresh_tokens_id"))
    op.drop_table("user_refresh_tokens")

    # Tenant and analytics query indexes
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_users_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_users_org_active",
            ["organization_id", "is_deleted"],
            unique=False,
        )

    with op.batch_alter_table("invitations", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_invitations_organization_id"),
            ["organization_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_invitations_org_email_used",
            ["organization_id", "email", "is_used"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("invitations", schema=None) as batch_op:
        batch_op.drop_index("ix_invitations_org_email_used")
        batch_op.drop_index(batch_op.f("ix_invitations_organization_id"))

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_org_active")
        batch_op.drop_index(batch_op.f("ix_users_organization_id"))

    op.create_table(
        "user_refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("user_refresh_tokens", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_refresh_tokens_id"), ["id"], unique=False)
        batch_op.create_index(batch_op.f("ix_user_refresh_tokens_token"), ["token"], unique=True)
