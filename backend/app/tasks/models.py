import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models import BaseModel


class TaskKind(StrEnum):
    """What a background task is doing. One kind so far."""

    GENERATE_COMPONENT = "generate_component"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    # A task left ``running`` by a restart. Reconcile-on-boot flips it here so the
    # UI stops waiting on a worker that no longer exists.
    INTERRUPTED = "interrupted"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Task(BaseModel):
    """A unit of background work, and the source of truth for its progress.

    Postgres owns the state, not the worker's memory: the UI polls this row, and
    a restart tells "still running" apart from "orphaned" without a broker.
    """

    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint("kind IN ('generate_component')", name="kind_valid"),
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed', 'interrupted')",
            name="status_valid",
        ),
    )

    kind: Mapped[str] = mapped_column(default=TaskKind.GENERATE_COMPONENT, index=True)
    status: Mapped[str] = mapped_column(default=TaskStatus.PENDING, index=True)
    # The user's brief, verbatim: the task's input and its audit trail.
    brief: Mapped[str]
    # The block this task produced, once it has one.
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("components.id", ondelete="SET NULL"), index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    finished_at: Mapped[datetime | None]
    error: Mapped[str | None]
    langfuse_trace_id: Mapped[str | None]
    # True when the task never ran: the brief had already been built, and this row
    # is the receipt that points at the block which answered it. It spends no
    # quota and asks no model.
    cached: Mapped[bool] = mapped_column(default=False, server_default="false")

    # Ordering is by step number, and deleting a task takes its steps with it.
    steps: Mapped[list[TaskStep]] = relationship(
        back_populates="task",
        order_by="TaskStep.index",
        cascade="all, delete-orphan",
    )


class TaskStep(BaseModel):
    """One visible step of a task: a line in the checklist the UI renders."""

    __tablename__ = "task_steps"

    __table_args__ = (
        UniqueConstraint("task_id", "index", name="uq_task_steps_task_index"),
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')", name="status_valid"
        ),
        CheckConstraint("index >= 0", name="index_non_negative"),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    # Position in the checklist, unique within a task.
    index: Mapped[int]
    name: Mapped[str]
    status: Mapped[str] = mapped_column(default=StepStatus.PENDING)
    # Whatever the step wants to show: a counter, a check summary, a screenshot.
    detail: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]

    task: Mapped[Task] = relationship(back_populates="steps")
