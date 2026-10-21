"""Add the manual user ban.

Revision ID: a4e8b1c7d920
Revises: f2a7c9d4b610
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4e8b1c7d920"
down_revision: str | Sequence[str] | None = "f2a7c9d4b610"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("banned_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("banned_by", sa.UUID(as_uuid=True), nullable=True))
    op.add_column("users", sa.Column("ban_reason", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_users_banned_by_users",
        "users",
        "users",
        ["banned_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_banned_at", "users", ["banned_at"])


def downgrade() -> None:
    op.drop_index("ix_users_banned_at", table_name="users")
    op.drop_constraint("fk_users_banned_by_users", "users", type_="foreignkey")
    op.drop_column("users", "ban_reason")
    op.drop_column("users", "banned_by")
    op.drop_column("users", "banned_at")
