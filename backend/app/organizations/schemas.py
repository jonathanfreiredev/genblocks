import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.organizations.models import Organization
from app.users.schemas import UserRead

# Long enough for a real name, short enough to keep a list readable.
MAX_NAME_LENGTH = 120


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)


class OrganizationUpdate(BaseModel):
    """Fields a member may change. The slug is assigned at creation and is stable."""

    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)


class OrganizationRead(BaseModel):
    """An organization as seen by one of its members.

    ``role`` is the caller's own role, so a client can tell whether it may
    administer the organization without asking a second time.
    """

    id: uuid.UUID
    name: str
    slug: str
    role: str
    created_at: datetime

    @classmethod
    def for_member(cls, organization: Organization, *, role: str) -> OrganizationRead:
        """Present an organization together with the caller's role in it."""
        return cls(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
            role=role,
            created_at=organization.created_at,
        )


class MembershipRead(BaseModel):
    id: uuid.UUID
    role: str
    created_at: datetime
    user: UserRead

    model_config = ConfigDict(from_attributes=True)
