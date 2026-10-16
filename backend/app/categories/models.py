import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class CategoryKind(StrEnum):
    """The top taxonomy level. Every category tree belongs to exactly one kind."""

    COMPONENT = "component"
    IMAGE = "image"


class Category(BaseModel):
    """A node of the two-level taxonomy.

    Level 1 is a kind root ("Components", "Images"); level 2 is a type ("Hero",
    "Illustration"). ``parent_id`` and ``level`` are what the two levels use, and
    a third level needs no migration (see PLAN.md).
    """

    __tablename__ = "categories"

    __table_args__ = (
        # Validated in the database too, so a manual query cannot create a kind
        # the application does not know about.
        CheckConstraint("kind IN ('component', 'image')", name="kind_valid"),
        CheckConstraint("level >= 1", name="level_positive"),
    )

    kind: Mapped[str] = mapped_column(index=True)
    # URL-safe identifier, so a category can be addressed by slug. Unique across
    # kinds on purpose: slugs are the public handle, and one namespace keeps
    # those URLs unambiguous.
    slug: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    level: Mapped[int] = mapped_column(default=1)
    # Self-referential so the tree can gain a third level without a migration.
    # Indexed on its own: "the children of a category" is a tree query.
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True
    )
