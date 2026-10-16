import re
import unicodedata
import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.authz.permissions import MembershipRole
from app.organizations.models import Membership, Organization
from app.pagination import ListParams
from app.users.models import User


class OrganizationSlugConflict(Exception):
    """Raised when the generated slug is already taken by another organization.

    A domain error, not an HTTP one: the same service will be called by the MCP
    tools, which know nothing about HTTP. ``app/main.py`` translates it.
    """


async def create_with_owner(session: AsyncSession, *, owner: User, name: str) -> Organization:
    """Create an organization with its creator as the first owner.

    Both rows are written in one transaction: an organization nobody belongs to
    would be unreachable, because every read is gated on a membership.
    """
    organization = Organization(name=name, slug=await _unique_slug(session, _slugify(name)))
    session.add(organization)

    try:
        # Flush now so a slug taken by a concurrent request surfaces here, where
        # it can be reported, instead of later at COMMIT.
        await session.flush()
    except IntegrityError as error:
        await session.rollback()
        raise OrganizationSlugConflict(
            f"An organization named {name!r} already exists; try another name"
        ) from error

    session.add(
        Membership(user_id=owner.id, organization_id=organization.id, role=MembershipRole.OWNER)
    )
    await session.commit()
    await session.refresh(organization)
    return organization


async def rename(session: AsyncSession, *, organization: Organization, name: str) -> Organization:
    """Change an organization's name.

    The slug is assigned once, at creation, and stays put: it identifies the
    organization in URLs, so renaming must not break existing links.
    """
    organization.name = name
    await session.commit()
    await session.refresh(organization)
    return organization


async def list_for_user(
    session: AsyncSession, *, user: User, params: ListParams
) -> tuple[Sequence[Membership], int]:
    """Return a page of the user's memberships, each with its organization loaded.

    The membership is the starting point because it carries the caller's role.
    Filtering on ``Membership.user_id`` is what enforces tenancy: a user can only
    ever see organizations they belong to.
    """
    order_by = params.order_by(
        {
            "created_at": Organization.created_at,
            "name": Organization.name,
            "slug": Organization.slug,
        },
        default="created_at",
        tiebreaker=Membership.id,
    )

    base = (
        select(Membership)
        .join(Organization, Membership.organization_id == Organization.id)
        .where(Membership.user_id == user.id, Membership.deleted_at.is_(None))
    )

    memberships = await session.scalars(
        base.options(selectinload(Membership.organization))
        .order_by(*order_by)
        .limit(params.limit)
        .offset(params.offset)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    return memberships.all(), total or 0


async def list_members(
    session: AsyncSession,
    *,
    organization_id: uuid.UUID,
    params: ListParams,
) -> tuple[Sequence[Membership], int]:
    """Return a page of the members of one organization."""
    order_by = params.order_by(
        {"created_at": Membership.created_at, "role": Membership.role},
        default="created_at",
        tiebreaker=Membership.id,
    )

    base = select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.deleted_at.is_(None),
    )

    members = await session.scalars(
        base.options(selectinload(Membership.user))
        .order_by(*order_by)
        .limit(params.limit)
        .offset(params.offset)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    return members.all(), total or 0


async def find_membership(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> Membership | None:
    """Return the user's membership of an organization, if there is one.

    The organization is loaded eagerly because the caller needs it and lazy
    loading would fail outside the event loop.
    """
    return await session.scalar(
        select(Membership)
        .options(selectinload(Membership.organization))
        .where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
            Membership.deleted_at.is_(None),
        )
    )


def _slugify(value: str) -> str:
    """Reduce a display name to a URL-safe slug.

    Accents are decomposed and dropped, so "Café Ñandú" becomes "cafe-nandu".
    """
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    # A name made only of characters the pattern rejects still needs a slug.
    return slug or "organization"


async def _unique_slug(session: AsyncSession, base: str) -> str:
    """Return ``base``, or the first free ``base-2``, ``base-3``... variant.

    Two requests can pass this check at the same time and collide at INSERT; the
    unique index on ``organizations.slug`` is the backstop, and the collision
    surfaces as an ``OrganizationSlugConflict``.
    """
    slug = base
    suffix = 2
    while True:
        taken = await session.scalar(select(Organization.id).where(Organization.slug == slug))
        if taken is None:
            return slug
        slug = f"{base}-{suffix}"
        suffix += 1
