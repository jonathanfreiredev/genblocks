"""Read side of the vault. Public: anyone may browse, search and read a block."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import Component, ComponentPreview
from app.generations.models import Generation
from app.pagination import ListParams
from app.settings import settings
from app.vectors import service as vectors


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


async def recent_in_category(
    session: AsyncSession, *, category_id: uuid.UUID, limit: int
) -> Sequence[Component]:
    """The newest published blocks of one type, for deciding what not to repeat."""
    blocks = await session.scalars(
        select(Component)
        .where(Component.deleted_at.is_(None), Component.category_id == category_id)
        .order_by(Component.created_at.desc())
        .limit(limit)
    )

    return blocks.all()


async def get_component_by_slug(session: AsyncSession, *, slug: str) -> Component | None:
    return await session.scalar(
        select(Component).where(Component.slug == slug, Component.deleted_at.is_(None))
    )


async def get_preview(session: AsyncSession, *, component_id: uuid.UUID) -> ComponentPreview | None:
    """The block's interactive build, if it has one and the block is still here.

    The join is the check that matters: a block removed from the vault stops
    answering with its document in the same request, so a takedown does not leave
    a preview reachable by the id somebody already has.
    """
    return await session.scalar(
        select(ComponentPreview)
        .join(Component, Component.id == ComponentPreview.component_id)
        .where(
            ComponentPreview.component_id == component_id,
            ComponentPreview.deleted_at.is_(None),
            Component.deleted_at.is_(None),
        )
    )


async def has_preview(session: AsyncSession, *, component_id: uuid.UUID) -> bool:
    """Whether the item page has something to run, without loading the document."""
    found = await session.scalar(
        select(ComponentPreview.id)
        .join(Component, Component.id == ComponentPreview.component_id)
        .where(
            ComponentPreview.component_id == component_id,
            ComponentPreview.deleted_at.is_(None),
            Component.deleted_at.is_(None),
        )
    )

    return found is not None


async def by_ids(session: AsyncSession, *, ids: Sequence[uuid.UUID]) -> list[Component]:
    """The blocks with these ids, in the order they were asked for.

    Retrieval answers with ids and distances; this turns the ids into rows without
    losing that order, which is the only thing ranking means.
    """
    if not ids:
        return []

    found = await session.scalars(
        select(Component).where(Component.id.in_(ids), Component.deleted_at.is_(None))
    )
    by_id = {component.id: component for component in found}

    return [by_id[one] for one in ids if one in by_id]


@dataclass(frozen=True)
class Render:
    """The two pictures of one attempt: the judge's page and the card's crop."""

    screenshot: str | None
    thumbnail: str | None


async def renders(session: AsyncSession, *, ids: Sequence[uuid.UUID]) -> dict[uuid.UUID, Render]:
    """The pictures each block was published with, by block id.

    A card in a conversation shows the block the way the vault does: its picture,
    not its title. The render lives on the attempt, so this is the one join. The
    thumbnail is the same attempt at card width; it is null for blocks published
    before it existed, and the card falls back to the render.
    """
    if not ids:
        return {}

    found = await session.execute(
        select(
            Component.id,
            Generation.screenshot_path,
            Generation.thumbnail_path,
        )
        .join(Generation, Generation.id == Component.winning_generation_id)
        .where(Component.id.in_(ids))
    )

    return {
        component_id: Render(screenshot=screenshot, thumbnail=thumbnail)
        for component_id, screenshot, thumbnail in found.all()
    }


async def already_built(session: AsyncSession, *, brief: str) -> tuple[Component, float] | None:
    """The block this brief already is, when the registry is close enough to say so.

    Duplicate checking is retrieval's second question: the first is "what does this
    resemble", and this one is "is it the same thing". The bar lives in settings
    because it is calibration, and it is measured — a brief that repeats a block
    lands near the bottom of the distance scale, and everything else further up.

    A bar is not a verdict: the caller decides what to do with the match, and the
    conversation can override it once the person has seen what already exists.
    """
    matches = await vectors.find_components(brief, limit=1)
    if not matches or matches[0].distance > settings.duplicate_distance:
        return None

    found = await by_ids(session, ids=[matches[0].id])

    return (found[0], matches[0].distance) if found else None
