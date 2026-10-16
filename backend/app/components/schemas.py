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

    model_config = ConfigDict(from_attributes=True)


class ComponentRead(ComponentSummary):
    """A whole block, for the item view and for an agent that wants to reuse it."""

    code: str
    delivery_prompt: str
    spec: dict | None
    winning_generation_id: uuid.UUID | None
    created_by: uuid.UUID | None
    license: str
