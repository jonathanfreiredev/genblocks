import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.pagination import ListParams


class ComponentListQuery(ListParams):
    """Everything the block list accepts as query parameters, in one model.

    The filters live here rather than as separate parameters because FastAPI
    stops expanding a query model the moment a sibling query parameter appears,
    and would then ask for the model itself as a single ``params`` field.
    """

    category_id: uuid.UUID | None = None
    search: str | None = None


class ComponentSummary(BaseModel):
    """What a gallery card needs: no code, no spec, just enough to browse."""

    id: uuid.UUID
    slug: str
    title: str
    description: str
    category_id: uuid.UUID
    created_at: datetime
    # The gallery shows the maker under the thumbnail, and the maker is a user,
    # not a field on the block. Both are filled by the router, not by the ORM row.
    author: str | None = None
    # The picture the block was published from. The card is a thumbnail, so the
    # list needs the render without loading the attempt it lives on.
    screenshot_path: str | None = None
    # The catalogue's own crop of the same attempt, at card width. Null for blocks
    # published before it existed; the card falls back to the render.
    thumbnail_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ComponentRead(ComponentSummary):
    """A whole block, for the item view and for an agent that wants to reuse it."""

    files: dict
    entry: str
    dependencies: dict | None
    delivery_prompt: str
    spec: dict | None
    provenance: dict | None
    winning_generation_id: uuid.UUID | None
    created_by: uuid.UUID | None
    license: str
    # Whether the item page has a built page to run. The document itself is a
    # separate read: this answer is four columns, that one is a few hundred
    # kilobytes.
    has_preview: bool = False
