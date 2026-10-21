import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class ReportTarget(StrEnum):
    """The artifact a report points at.

    New reports target a component. The image member remains so reports written
    before the public image catalogue was removed keep their snapshot.
    """

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
    ``target_id`` because the database can follow the row while it exists. A
    report outlives its target: hard deletion sets the foreign keys to null and
    the snapshot columns keep the kind, id, slug and title the operator acted on.
    """

    __tablename__ = "reports"
    __table_args__ = (
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
    # The target as it was when the report was written. These survive a hard
    # delete, which the nullable foreign keys above cannot.
    target_kind: Mapped[str] = mapped_column(String(16), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    target_slug: Mapped[str | None] = mapped_column(String(255))
    target_title: Mapped[str | None] = mapped_column(Text)
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
