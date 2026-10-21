"""Let a task generate a standalone image.

Revision ID: b7c2d9e4f103
Revises: a4e8b1c7d920
Create Date: 2026-10-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c2d9e4f103"
down_revision: str | Sequence[str] | None = "a4e8b1c7d920"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("kind_valid", "tasks", type_="check")
    op.create_check_constraint(
        "kind_valid",
        "tasks",
        "kind IN ('generate_component', 'generate_image')",
    )

    op.add_column("tasks", sa.Column("image_id", sa.UUID(as_uuid=True), nullable=True))
    op.add_column("tasks", sa.Column("image_width", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("image_height", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("image_category_id", sa.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_tasks_image_id_images",
        "tasks",
        "images",
        ["image_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_tasks_image_category_id_categories",
        "tasks",
        "categories",
        ["image_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_tasks_image_id", "tasks", ["image_id"])
    op.create_index("ix_tasks_image_category_id", "tasks", ["image_category_id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_image_category_id", table_name="tasks")
    op.drop_index("ix_tasks_image_id", table_name="tasks")
    op.drop_constraint("fk_tasks_image_category_id_categories", "tasks", type_="foreignkey")
    op.drop_constraint("fk_tasks_image_id_images", "tasks", type_="foreignkey")
    op.drop_column("tasks", "image_category_id")
    op.drop_column("tasks", "image_height")
    op.drop_column("tasks", "image_width")
    op.drop_column("tasks", "image_id")

    op.drop_constraint("kind_valid", "tasks", type_="check")
    op.create_check_constraint("kind_valid", "tasks", "kind IN ('generate_component')")
