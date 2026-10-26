import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from app import urls
from app.generations.schemas import GenerationRead
from app.pagination import ListParams
from app.tasks.models import TaskStatus

# A brief is a sentence or a paragraph, not a character and not an essay. The
# bounds live here because both doors take the same type: the API expands it into
# its body schema and the MCP tool into its argument schema, so the two cannot
# come to disagree about what a brief is.
BRIEF_MIN_LENGTH = 10
BRIEF_MAX_LENGTH = 2000

Brief = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=BRIEF_MIN_LENGTH,
        max_length=BRIEF_MAX_LENGTH,
    ),
]


class TaskCreate(BaseModel):
    """What a caller supplies to queue a component task: what they want built."""

    brief: Brief


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
    image_id: uuid.UUID | None = None
    image_width: int | None = None
    image_height: int | None = None
    image_category_id: uuid.UUID | None = None
    created_at: datetime
    finished_at: datetime | None
    error: str | None
    langfuse_trace_id: str | None
    # True when the brief had already been built: the task never ran.
    cached: bool = False
    steps: list[TaskStepRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    # Where the owner follows it. Present from the moment it is queued, when
    # there is no render yet: the page shows the checklist, and the result once
    # there is one.
    @computed_field
    @property
    def task_url(self) -> str:
        """The task's own page on the site."""
        return urls.task_page_url(self.id)


class TaskDetailRead(TaskRead):
    """A task in full: its checklist, plus the attempts it has produced so far."""

    generations: list[GenerationRead] = Field(default_factory=list)
