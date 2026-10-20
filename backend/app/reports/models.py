import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class ReportTarget(StrEnum):
    """The two public artifacts a report can point at."""

    COMPONENT = "component"
    IMAGE = "image"


class ReportReason(StrEnum):
    """Why somebody reported an artifact.

    Kept as a closed vocabulary rather than free text so the queue can be
    filtered and counted. ``details`` carries the part only a person can explain.
    """

    SEXUAL = "sexual"
    MINOR = "minor"
    VIOLENCE = "violence"
    HATE = "hate"
    HARASSMENT = "harassment"
    SELF_HARM = "self_harm"
    ILLEGAL = "illegal"
    MALWARE = "malware"
    PRIVACY = "privacy"
    REAL_PERSON = "real_person"
    BRAND = "brand"
    OTHER = "other"


class ReportStatus(StrEnum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Report(BaseModel):
    """One person's report about one public artifact.

    The target is one of two nullable foreign keys rather than a polymorphic
    ``target_id`` because the database can then enforce that exactly one is set
    and can follow the row when it is removed. A report outlives a takedown: the
    target is soft-deleted, so the review can still say what it acted on.
    """

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint(
            "(component_id IS NOT NULL) <> (image_id IS NOT NULL)",
            name="one_target",
        ),
        CheckConstraint(
            "reason IN ('sexual', 'minor', 'violence', 'hate', 'harassment', "
            "'self_harm', 'illegal', 'malware', 'privacy', 'real_person', "
            "'brand', 'other')",
            name="reason_valid",
        ),
        CheckConstraint(
            "status IN ('open', 'reviewing', 'resolved', 'dismissed')",
            name="status_valid",
        ),
    )

    component_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("components.id", ondelete="SET NULL"), index=True
    )
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("images.id", ondelete="SET NULL"), index=True
    )
    reason: Mapped[str]
    details: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(default=ReportStatus.OPEN)
    resolution: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None]
