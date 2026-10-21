"""Review gates and hard-delete snapshots.

Revision ID: 8b1f4c2d9a01
Revises: 30aff5369e47
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8b1f4c2d9a01"
down_revision: str | Sequence[str] | None = "30aff5369e47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Generated work starts hidden. Existing rows were already public, so they
    # keep their current visibility.
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

    op.execute("UPDATE components SET reviewed_at = created_at")
    op.execute("UPDATE images SET reviewed_at = created_at")

    # Reports keep what they acted on after the target row is gone. The old
    # foreign-key-only design cannot represent that state.
    op.add_column("reports", sa.Column("target_kind", sa.String(length=16)))
    op.add_column("reports", sa.Column("target_id", sa.UUID(as_uuid=True)))
    op.add_column("reports", sa.Column("target_slug", sa.String(length=255)))
    op.add_column("reports", sa.Column("target_title", sa.Text()))

    op.execute(
        """
        UPDATE reports
        SET target_kind = CASE
                WHEN component_id IS NOT NULL THEN 'component'
                ELSE 'image'
            END,
            target_id = COALESCE(component_id, image_id)
        """
    )
    op.execute(
        """
        UPDATE reports AS r
        SET target_slug = c.slug, target_title = c.title
        FROM components AS c
        WHERE r.component_id = c.id
        """
    )
    op.execute(
        """
        UPDATE reports AS r
        SET target_slug = i.slug, target_title = i.prompt
        FROM images AS i
        WHERE r.image_id = i.id
        """
    )

    op.alter_column("reports", "target_kind", nullable=False)
    op.alter_column("reports", "target_id", nullable=False)
    op.drop_constraint("one_target", "reports", type_="check")
    op.create_index("ix_reports_target_kind", "reports", ["target_kind"])


def downgrade() -> None:
    op.drop_index("ix_reports_target_kind", table_name="reports")
    op.create_check_constraint(
        "one_target",
        "reports",
        "(component_id IS NOT NULL) <> (image_id IS NOT NULL)",
    )
    op.drop_column("reports", "target_title")
    op.drop_column("reports", "target_slug")
    op.drop_column("reports", "target_id")
    op.drop_column("reports", "target_kind")

    op.drop_index("ix_images_reviewed_at", table_name="images")
    op.drop_constraint("fk_images_reviewed_by_users", "images", type_="foreignkey")
    op.drop_column("images", "reviewed_by")
    op.drop_column("images", "reviewed_at")

    op.drop_index("ix_components_reviewed_at", table_name="components")
    op.drop_constraint("fk_components_reviewed_by_users", "components", type_="foreignkey")
    op.drop_column("components", "reviewed_by")
    op.drop_column("components", "reviewed_at")
