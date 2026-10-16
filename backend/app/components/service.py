"""Read side of the vault. Public: anyone may browse, search and read a block."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import Component
from app.pagination import ListParams


async def list_components(
    session: AsyncSession,
    *,
    params: ListParams,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
) -> tuple[Sequence[Component], int]:
    """Return a page of blocks, optionally filtered by category or free text."""
    order_by = params.order_by(
        {
            "created_at": Component.created_at,
            "title": Component.title,
            "slug": Component.slug,
        },
        default="-created_at",
        tiebreaker=Component.id,
    )

    base = select(Component).where(Component.deleted_at.is_(None))

    if category_id is not None:
        base = base.where(Component.category_id == category_id)

    if search:
        pattern = f"%{search}%"
        base = base.where(or_(Component.title.ilike(pattern), Component.description.ilike(pattern)))

    components = await session.scalars(
        base.order_by(*order_by).limit(params.limit).offset(params.offset)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    return components.all(), total or 0


async def get_component(session: AsyncSession, *, component_id: uuid.UUID) -> Component | None:
    return await session.scalar(
        select(Component).where(Component.id == component_id, Component.deleted_at.is_(None))
    )


async def get_component_by_slug(session: AsyncSession, *, slug: str) -> Component | None:
    return await session.scalar(
        select(Component).where(Component.slug == slug, Component.deleted_at.is_(None))
    )
