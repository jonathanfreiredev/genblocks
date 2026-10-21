import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GenerationRead(BaseModel):
    """What a task produced, as the task view and the item view read it."""

    id: uuid.UUID
    task_id: uuid.UUID | None
    component_id: uuid.UUID | None
    attempt_no: int
    files: dict
    entry: str
    screenshot_path: str | None
    thumbnail_path: str | None
    checks: dict | None
    scores: dict | None
    verdict: str
    rubric_version: str | None
    model: str | None
    langfuse_trace_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
