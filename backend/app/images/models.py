import uuid
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.components.models import DEFAULT_LICENSE
from app.db.models import BaseModel
from app.images.slug import image_slug


def _default_slug(context: Any) -> str:
    """The slug for a row that did not set one, from the prompt and path it has."""
    values = context.get_current_parameters()

    return image_slug(prompt=values.get("prompt") or "", path=values.get("path") or "")


class Image(BaseModel):
    """A generated image in the stock library.

    The bytes live in Cloudinary; this row keeps the prompt that produced them,
    their dimensions and their taxonomy, so the library can be browsed and
    reused without touching the CDN.
    """

    __tablename__ = "images"

    prompt: Mapped[str]
    # What a link says: a scene, not a uuid. Unique, so one address names one
    # picture.
    slug: Mapped[str] = mapped_column(unique=True, index=True, default=_default_slug)
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
    # The generated-media provenance record: model, prompt hash and the IPTC
    # digital source type. It travels with the row because the re-encoded bytes
    # deliberately carry no metadata at all.
    provenance: Mapped[dict | None] = mapped_column(JSONB)
