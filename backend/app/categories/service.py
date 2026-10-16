"""Read side of the taxonomy. Public: anyone may list and read categories."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category


async def list_categories(session: AsyncSession, *, kind: str | None = None) -> Sequence[Category]:
    """Return the taxonomy, ordered so kinds and their types come together.

    The whole taxonomy is small and fixed, so it is returned unpaginated: a
    client renders it in one go.
    """
    statement = select(Category).where(Category.deleted_at.is_(None))
    if kind is not None:
        statement = statement.where(Category.kind == kind)

    statement = statement.order_by(Category.kind, Category.level, Category.name)
    return (await session.scalars(statement)).all()


async def get_category(session: AsyncSession, *, category_id: uuid.UUID) -> Category | None:
    return await session.scalar(
        select(Category).where(Category.id == category_id, Category.deleted_at.is_(None))
    )


async def get_category_by_slug(session: AsyncSession, *, slug: str) -> Category | None:
    return await session.scalar(
        select(Category).where(Category.slug == slug, Category.deleted_at.is_(None))
    )
