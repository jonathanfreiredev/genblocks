"""make every block a project with an entry file

A block stops carrying its text twice. ``code`` was always the entry file of
``files`` copied beside it, so it is folded into the project and replaced by
``entry``: a path saying which file the block is.

The order matters. ``entry`` is added nullable, every row is filled in — a row
that never had ``files`` gets one holding its old ``code`` — and only then do the
columns become NOT NULL and ``code`` go. The reverse does the same backwards, so a
downgrade does not empty a column either.

Revision ID: d29bec2788b9
Revises: fa7231b54bac
Create Date: 2026-10-19 09:41:41.521975

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d29bec2788b9"
down_revision: str | Sequence[str] | None = "fa7231b54bac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The path the harness has always written the block to (``app.harness.agent``).
# Spelled out here rather than imported: a migration is a record of what the
# schema was at one moment, and must not change when the code moves on.
ENTRY = "src/Block.tsx"


def upgrade() -> None:
    """Upgrade schema."""
    for table in ("components", "generations"):
        op.add_column(table, sa.Column("entry", sa.String(), nullable=True))

        # A row from before projects: its one file is what ``code`` holds.
        op.execute(
            f"""
            UPDATE {table}
            SET files = jsonb_build_object('{ENTRY}', code)
            WHERE files IS NULL
            """
        )
        op.execute(f"UPDATE {table} SET entry = '{ENTRY}' WHERE entry IS NULL")

        op.alter_column(
            table,
            "files",
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        )
        op.alter_column(table, "entry", existing_type=sa.String(), nullable=False)
        op.drop_column(table, "code")


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("components", "generations"):
        op.add_column(table, sa.Column("code", sa.VARCHAR(), nullable=True))

        # Back to one text per row: the entry file's, which is what ``code``
        # meant when it existed.
        op.execute(
            f"""
            UPDATE {table}
            SET code = COALESCE(files ->> '{ENTRY}', '')
            """
        )

        op.alter_column(table, "code", existing_type=sa.VARCHAR(), nullable=False)
        op.alter_column(
            table, "files", existing_type=postgresql.JSONB(astext_type=sa.Text()), nullable=True
        )
        op.drop_column(table, "entry")
