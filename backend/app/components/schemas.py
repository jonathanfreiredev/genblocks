import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
