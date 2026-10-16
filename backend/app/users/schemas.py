import uuid

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    # Email changes go through Supabase (they trigger a confirmation email), so
    # the profile endpoint only edits local, domain-owned fields.
    full_name: str | None = None
