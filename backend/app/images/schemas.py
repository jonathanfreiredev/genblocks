import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.pagination import ListParams

IMAGE_PROMPT_MIN_LENGTH = 10
IMAGE_PROMPT_MAX_LENGTH = 2_000

ImagePrompt = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=IMAGE_PROMPT_MIN_LENGTH,
        max_length=IMAGE_PROMPT_MAX_LENGTH,
    ),
]


class ImageListQuery(ListParams):
    """Everything the image list accepts as query parameters, in one model.

    Filters live here rather than as separate parameters: FastAPI stops expanding
    a query model as soon as a sibling query parameter exists.
    """

    category_id: uuid.UUID | None = None
    search: str | None = Field(default=None, max_length=200)


class ImagePlanRequest(BaseModel):
    """What a caller wants generated: the scene, its size and its type."""

    prompt: ImagePrompt
    width: int = Field(ge=256, le=1536)
    height: int = Field(ge=256, le=1536)
    # The level-2 image category slug, e.g. ``photography``.
    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class ImagePlanRead(BaseModel):
    """The preflight answer for one standalone image prompt."""

    status: str
    prompt: str
    width: int
    height: int
    category: str
    reason: str
    suggested_prompt: str | None


class ImageRead(BaseModel):
    """A stock image and its generation panel.

    ``path`` is the Cloudinary public id, not a full URL: the delivery host and
    the transform are the client's to choose. ``scores``, ``rubric_version`` and
    ``langfuse_trace_id`` are the same fields a component exposes, so one view
    renders the panel for both.
    """

    id: uuid.UUID
    slug: str
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
    provenance: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
