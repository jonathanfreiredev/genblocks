import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


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
    # the profile endpoint only edits local, domain-owned fields. The name is
    # shown publicly on every item, so it is bounded rather than an essay.
    full_name: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, max_length=120),
        ]
        | None
    ) = None
