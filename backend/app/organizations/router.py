from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.dependencies import get_first_party_user
from app.authz.permissions import MembershipRole, Permission
from app.db.session import get_async_db_session
from app.organizations.dependencies import require_membership
from app.organizations.models import Membership
from app.organizations.schemas import (
    MembershipRead,
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.organizations.service import create_with_owner, list_for_user, list_members, rename
from app.pagination import ListParams, OffsetPage
from app.users.models import User

organizations_router = APIRouter(prefix="/organizations", tags=["organizations"])


@organizations_router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> OrganizationRead:
    """Create an organization; the caller becomes its first owner."""
    organization = await create_with_owner(session, owner=user, name=payload.name)
    return OrganizationRead.for_member(organization, role=MembershipRole.OWNER)


@organizations_router.get("", response_model=OffsetPage[OrganizationRead])
async def list_organizations(
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[ListParams, Query()],
) -> OffsetPage[OrganizationRead]:
    """List the organizations the current user belongs to."""
    memberships, total = await list_for_user(session, user=user, params=params)

    return OffsetPage(
        items=[OrganizationRead.for_member(m.organization, role=m.role) for m in memberships],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@organizations_router.get("/{organization_id}", response_model=OrganizationRead)
async def read_organization(
    membership: Annotated[Membership, Depends(require_membership(Permission.ORGANIZATION_READ))],
) -> OrganizationRead:
    """Return one organization the caller belongs to."""
    return OrganizationRead.for_member(membership.organization, role=membership.role)


@organizations_router.patch("/{organization_id}", response_model=OrganizationRead)
async def update_organization(
    payload: OrganizationUpdate,
    membership: Annotated[Membership, Depends(require_membership(Permission.ORGANIZATION_UPDATE))],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> OrganizationRead:
    """Rename an organization. Every member can read it; only an owner can change it."""
    organization = await rename(session, organization=membership.organization, name=payload.name)
    return OrganizationRead.for_member(organization, role=membership.role)


@organizations_router.get("/{organization_id}/members", response_model=OffsetPage[MembershipRead])
async def list_organization_members(
    membership: Annotated[Membership, Depends(require_membership(Permission.ORGANIZATION_READ))],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[ListParams, Query()],
) -> OffsetPage[MembershipRead]:
    """List the members of an organization the caller belongs to."""
    members, total = await list_members(
        session,
        organization_id=membership.organization_id,
        params=params,
    )

    return OffsetPage(
        items=list(members),
        total=total,
        limit=params.limit,
        offset=params.offset,
    )
