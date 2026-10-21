import uuid

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None
    is_banned: bool = False
    # Configured operator, not a database role. Computed at the edge so a
    # client can hide the report queue without a second request.
    is_admin: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    # Email changes go through Supabase (they trigger a confirmation email), so
    # the profile endpoint only edits local, domain-owned fields.
    full_name: str | None = None
