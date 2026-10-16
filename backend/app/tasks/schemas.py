import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.generations.schemas import GenerationRead
from app.pagination import ListParams
from app.tasks.models import TaskStatus


class TaskListQuery(ListParams):
    """Everything the task list accepts as query parameters, in one model.

    The filter lives here rather than as a separate parameter because FastAPI
    stops expanding a query model the moment a sibling query parameter appears,
    and would then ask for the model itself as a single ``params`` field.
    """

    status: TaskStatus | None = None


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
    langfuse_trace_id: str | None
    steps: list[TaskStepRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TaskDetailRead(TaskRead):
    """A task in full: its checklist, plus the attempts it has produced so far."""

    generations: list[GenerationRead] = Field(default_factory=list)
