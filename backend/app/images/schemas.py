import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.pagination import ListParams


class ImageListQuery(ListParams):
    """Everything the image list accepts as query parameters, in one model.

    Filters live here rather than as separate parameters: FastAPI stops expanding
    a query model as soon as a sibling query parameter exists.
    """

    category_id: uuid.UUID | None = None
    search: str | None = None


class ImageRead(BaseModel):
    """A stock image and its generation panel.

    ``path`` is the Cloudinary public id, not a full URL: the delivery host and
    the transform are the client's to choose. ``scores``, ``rubric_version`` and
    ``langfuse_trace_id`` are the same fields a component exposes, so one view
    renders the panel for both.
    """

    id: uuid.UUID
    prompt: str
    path: str
    width: int
    height: int
    category_id: uuid.UUID
    created_by: uuid.UUID | None
    # The maker's public name, resolved by the router; null for the house.
    author: str | None = None
    license: str
    model: str | None
    scores: dict | None
    rubric_version: str | None
    langfuse_trace_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
