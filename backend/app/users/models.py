import uuid

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
