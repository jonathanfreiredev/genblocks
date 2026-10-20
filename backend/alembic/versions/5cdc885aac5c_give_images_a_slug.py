"""give images a slug

Revision ID: 5cdc885aac5c
Revises: d18b9f8ce2ea
Create Date: 2026-10-20 07:56:31.744441

A picture needs an address a person can read. Existing rows are named from the
asset path when it is descriptive and from the prompt otherwise; the seed writes
its own keys, so a fresh dataset keeps the same slugs.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.images.slug import image_slug

# revision identifiers, used by Alembic.
revision: str = "5cdc885aac5c"
down_revision: str | Sequence[str] | None = "d18b9f8ce2ea"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the image slug, name what is already filed, then make it required."""
    op.add_column("images", sa.Column("slug", sa.String(), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, prompt, path FROM images")).fetchall()
    used: set[str] = set()

    for image_id, prompt, path in rows:
        slug = image_slug(prompt=prompt, path=path)
        base = slug
        suffix = 2
        while slug in used:
            slug = f"{base}-{suffix}"
            suffix += 1
        used.add(slug)
        connection.execute(
            sa.text("UPDATE images SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": image_id},
        )

    op.alter_column("images", "slug", existing_type=sa.String(), nullable=False)
    op.create_index(op.f("ix_images_slug"), "images", ["slug"], unique=True)


def downgrade() -> None:
    """Drop the slug; the asset path still names the picture."""
    op.drop_index(op.f("ix_images_slug"), table_name="images")
    op.drop_column("images", "slug")
