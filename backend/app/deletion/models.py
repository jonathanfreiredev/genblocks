import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class DeletionAudit(BaseModel):
    """One operator deletion attempt, kept after the target row is gone.

    The target id is deliberately not a foreign key: the audit has to survive
    exactly the delete it records.
    """

    __tablename__ = "deletion_audit"

    kind: Mapped[str] = mapped_column(String(16), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    slug: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    paths: Mapped[list] = mapped_column(JSONB)
    result: Mapped[str] = mapped_column(String(16), index=True)
    error: Mapped[str | None] = mapped_column(Text)
