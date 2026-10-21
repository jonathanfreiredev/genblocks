import uuid
from datetime import datetime

from pydantic import BaseModel

from app.components.schemas import ComponentListQuery, ComponentSummary
from app.images.schemas import ImageListQuery, ImageRead


class AdminComponentListQuery(ComponentListQuery):
    """The block list, with no review filter: every public row is visible."""


class AdminImageListQuery(ImageListQuery):
    """The image list, with no review filter: every public row is visible."""


class AdminComponentSummary(ComponentSummary):
    """A block as the operator sees it. The admin queue only deletes."""


class AdminImageRead(ImageRead):
    """A picture as the operator sees it. The admin queue only deletes."""


class AdminDeletionRead(BaseModel):
    """One deletion audit row, with the actor resolved for display."""

    id: uuid.UUID
    kind: str
    target_id: uuid.UUID
    slug: str
    title: str
    actor: str | None
    paths: list[str]
    result: str
    error: str | None
    created_at: datetime
