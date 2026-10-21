"""Keep the built page of a block, so the item view can run it.

Revision ID: 28fa54f5c045
Revises: b7c2d9e4f103
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "28fa54f5c045"
down_revision: str | Sequence[str] | None = "b7c2d9e4f103"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "component_previews",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        # One preview per block: the unique constraint is also the lookup index.
        sa.Column("component_id", sa.UUID(as_uuid=True), nullable=False),
        # The built page folded into one document, CSP and bridge included.
        sa.Column("html", sa.Text(), nullable=False),
        # Its size in UTF-8 bytes, so what a block costs is visible without
        # loading the document.
        sa.Column("bytes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name="fk_component_previews_component_id_components",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_component_previews"),
        sa.UniqueConstraint("component_id", name="uq_component_previews_component_id"),
    )


def downgrade() -> None:
    op.drop_table("component_previews")
