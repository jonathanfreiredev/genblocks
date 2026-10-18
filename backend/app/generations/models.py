import uuid
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class Verdict(StrEnum):
    """Where an attempt ended up.

    ``candidate`` is an attempt nobody has turned down yet: what an attempt is
    while its run is in flight. An attempt that was turned down is ``rejected`` —
    by the sandbox that would not build it or by the judge that scored it below
    its bar — and the one published is ``published``.
    """

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
    # The project this attempt produced, and its pictures' slots. Same shape as the
    # component's, kept on the attempt too: a rejected attempt that cannot be rebuilt
    # is a record of an opinion rather than of a block.
    files: Mapped[dict | None] = mapped_column(JSONB)
    # Cloudinary public id of the render. Nullable until the upload succeeds.
    screenshot_path: Mapped[str | None]
    # What the sandbox found: one entry per check, with its short detail. Null on
    # attempts that never reached the sandbox (Fase 7 writes it; the seed plants
    # rows from before there was one).
    checks: Mapped[dict | None] = mapped_column(JSONB)
    scores: Mapped[dict | None] = mapped_column(JSONB)
    verdict: Mapped[str] = mapped_column(default=Verdict.CANDIDATE)
    rubric_version: Mapped[str | None]
    model: Mapped[str | None]
    langfuse_trace_id: Mapped[str | None]
