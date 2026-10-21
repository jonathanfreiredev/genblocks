import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import BaseModel


class User(BaseModel):
    """The application's user profile.

    Credentials, email verification and sessions live in Supabase Auth. This
    table only stores domain data, linked to Supabase by ``supabase_user_id``
    (the token's ``sub`` claim). Use ``id`` for your own relations.
    """

    __tablename__ = "users"

    supabase_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    # Mirror of a Supabase-owned value, so it is indexed but not unique: Supabase
    # enforces uniqueness per project, and a user can be removed out of band,
    # which would otherwise leave an orphan row blocking a later signup.
    email: Mapped[str | None] = mapped_column(index=True, default=None)
    full_name: Mapped[str | None] = mapped_column(default=None)

    # A manual operator ban. Supabase is also told to refuse a new login; this
    # column is what stops an access token that was issued before the ban.
    banned_at: Mapped[datetime | None] = mapped_column(index=True, default=None)
    banned_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    ban_reason: Mapped[str | None] = mapped_column(Text, default=None)

    @property
    def is_banned(self) -> bool:
        return self.banned_at is not None
