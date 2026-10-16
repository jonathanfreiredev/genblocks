import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskStepRead(BaseModel):
    id: uuid.UUID
    index: int
    name: str
    status: str
    detail: dict | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    """A task with its checklist. ``steps`` is always eagerly loaded."""

    id: uuid.UUID
    kind: str
    status: str
    brief: str
    component_id: uuid.UUID | None
    created_at: datetime
    finished_at: datetime | None
    error: str | None
    steps: list[TaskStepRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
