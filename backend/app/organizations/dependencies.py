"""Resolving the organization in the path for the caller, with its permission."""

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.dependencies import get_first_party_user
from app.authz.permissions import Permission, require
from app.db.session import get_async_db_session
from app.organizations.models import Membership
from app.organizations.service import find_membership
from app.users.models import User

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")


def require_membership(permission: Permission) -> Callable[..., Awaitable[Membership]]:
    """Build the dependency an endpoint uses to reach an organization.

    It resolves the organization named in the path and enforces both rules, in
    order:

    - A caller who is not a member gets a 404, never a 403: the response must not
      tell an organization that exists apart from one that does not.
    - A member whose role does not grant ``permission`` gets a 403.

    Endpoints depend on this instead of resolving the organization themselves, so
    a new endpoint cannot reach one without naming the permission it needs.
    """

    async def dependency(
        organization_id: uuid.UUID,
        user: Annotated[User, Depends(get_first_party_user)],
        session: Annotated[AsyncSession, Depends(get_async_db_session)],
    ) -> Membership:
        membership = await find_membership(
            session, user_id=user.id, organization_id=organization_id
        )

        if membership is None:
            raise _NOT_FOUND

        require(permission, role=membership.role)
        return membership

    return dependency
