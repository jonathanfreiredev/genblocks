import uuid

from pydantic import BaseModel, ConfigDict


class CategoryRead(BaseModel):
    """A taxonomy node as the API and the MCP tools expose it.

    ``parent_id`` and ``level`` are part of the payload so a client can rebuild
    the tree without a second request.
    """

    id: uuid.UUID
    parent_id: uuid.UUID | None
    kind: str
    slug: str
    name: str
    level: int

    model_config = ConfigDict(from_attributes=True)
