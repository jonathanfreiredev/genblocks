"""Remove the review gate and add the simple deletion audit.

Revision ID: f2a7c9d4b610
Revises: 8b1f4c2d9a01
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f2a7c9d4b610"
down_revision: str | Sequence[str] | None = "8b1f4c2d9a01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The product publishes after moderation; there is no approval queue.
    op.drop_index("ix_components_reviewed_at", table_name="components")
    op.drop_constraint("fk_components_reviewed_by_users", "components", type_="foreignkey")
    op.drop_column("components", "reviewed_by")
    op.drop_column("components", "reviewed_at")

    op.drop_index("ix_images_reviewed_at", table_name="images")
    op.drop_constraint("fk_images_reviewed_by_users", "images", type_="foreignkey")
    op.drop_column("images", "reviewed_by")
    op.drop_column("images", "reviewed_at")

    op.create_table(
        "deletion_audit",
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("paths", postgresql.JSONB(), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
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
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deletion_audit_kind", "deletion_audit", ["kind"])
    op.create_index("ix_deletion_audit_target_id", "deletion_audit", ["target_id"])
    op.create_index("ix_deletion_audit_actor_id", "deletion_audit", ["actor_id"])
    op.create_index("ix_deletion_audit_result", "deletion_audit", ["result"])


def downgrade() -> None:
    op.drop_index("ix_deletion_audit_result", table_name="deletion_audit")
    op.drop_index("ix_deletion_audit_actor_id", table_name="deletion_audit")
    op.drop_index("ix_deletion_audit_target_id", table_name="deletion_audit")
    op.drop_index("ix_deletion_audit_kind", table_name="deletion_audit")
    op.drop_table("deletion_audit")

    op.add_column("images", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.add_column("images", sa.Column("reviewed_by", sa.UUID(as_uuid=True)))
    op.create_foreign_key(
        "fk_images_reviewed_by_users",
        "images",
        "users",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_images_reviewed_at", "images", ["reviewed_at"])
    op.execute("UPDATE images SET reviewed_at = created_at")

    op.add_column("components", sa.Column("reviewed_at", sa.DateTime(timezone=True)))
    op.add_column("components", sa.Column("reviewed_by", sa.UUID(as_uuid=True)))
    op.create_foreign_key(
        "fk_components_reviewed_by_users",
        "components",
        "users",
        ["reviewed_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_components_reviewed_at", "components", ["reviewed_at"])
    op.execute("UPDATE components SET reviewed_at = created_at")
