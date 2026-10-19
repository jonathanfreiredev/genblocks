import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class BriefCache(BaseModel):
    """One brief, normalized, and the block that answered it.

    A row here is a fact: this text was built once, and the result is still in the
    registry. It is not a judgement of similarity — for that there is the guard —
    and it does not promise the block is the best answer, only that it is the same
    request.
    """

    __tablename__ = "brief_cache"

    key: Mapped[str] = mapped_column(unique=True, index=True)
    component_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("components.id", ondelete="CASCADE"), index=True
    )
