import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class Verdict(StrEnum):
    """Where an attempt ended up once the judge had read it."""

    CANDIDATE = "candidate"
    PUBLISHED = "published"
    REJECTED = "rejected"


class Generation(BaseModel):
    """One attempt at a component: its code, its screenshot and its scores.

    An attempt is owned by the **task** that produced it, not by the component
    it may become: a rejected attempt still exists on its own, and the component
    is only created at commit. ``component_id`` is filled in then, on every
    attempt of the task, so an item can show its whole history.

    Rejected attempts are kept, not hidden: "we tried and it was not good
    enough" is part of the product's claim.
    """

    __tablename__ = "generations"

    __table_args__ = (
        # One attempt number per task: the attempt's real owner. Component ids
        # are assigned later and in bulk, so they cannot carry this invariant.
        UniqueConstraint("task_id", "attempt_no", name="uq_generations_task_attempt"),
        CheckConstraint("verdict IN ('candidate', 'published', 'rejected')", name="verdict_valid"),
        CheckConstraint("attempt_no >= 1", name="attempt_positive"),
    )

    # Nullable: seeding plants components with their attempts and no task behind
    # them. SET NULL rather than CASCADE, so deleting a task never erases the
    # record of a published piece.
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"), index=True
    )
    # NULL while the task runs; set at commit, on every attempt of the task.
    component_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("components.id", ondelete="CASCADE"), index=True
    )
    attempt_no: Mapped[int]
    code: Mapped[str]
    # Cloudinary public id of the render. Nullable until the upload succeeds.
    screenshot_path: Mapped[str | None]
    scores: Mapped[dict | None] = mapped_column(JSONB)
    verdict: Mapped[str] = mapped_column(default=Verdict.CANDIDATE)
    rubric_version: Mapped[str | None]
    model: Mapped[str | None]
    langfuse_trace_id: Mapped[str | None]
