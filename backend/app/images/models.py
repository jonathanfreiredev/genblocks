import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.components.models import DEFAULT_LICENSE
from app.db.models import BaseModel


class Image(BaseModel):
    """A generated image in the stock library.

    The bytes live in Cloudinary; this row keeps the prompt that produced them,
    their dimensions and their taxonomy, so the library can be browsed and
    reused without touching the CDN.
    """

    __tablename__ = "images"

    prompt: Mapped[str]
    # Cloudinary public id. Unique: it is the asset's identity in the CDN, so two
    # rows must never point at the same object.
    path: Mapped[str] = mapped_column(unique=True, index=True)
    width: Mapped[int]
    height: Mapped[int]
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    license: Mapped[str] = mapped_column(default=DEFAULT_LICENSE)

    # The same generation panel a component shows: what made it, how it scored,
    # and the trace to replay. The rubric for images is shorter, but the shape
    # matches, so one view renders both.
    model: Mapped[str | None]
    scores: Mapped[dict | None] = mapped_column(JSONB)
    rubric_version: Mapped[str | None]
    langfuse_trace_id: Mapped[str | None]
