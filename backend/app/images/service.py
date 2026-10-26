"""Read side of the public image library."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.images.models import Image
from app.images.schemas import ImageRead
from app.pagination import ListParams
from app.users.service import display_names


async def list_images(
    session: AsyncSession,
    *,
    params: ListParams,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
) -> tuple[Sequence[Image], int]:
    """Return a page of images, optionally filtered by category or prompt text."""
    order_by = params.order_by(
        {"created_at": Image.created_at, "prompt": Image.prompt},
        default="-created_at",
        tiebreaker=Image.id,
    )

    base = select(Image).where(Image.deleted_at.is_(None))

    if category_id is not None:
        base = base.where(Image.category_id == category_id)

    if search:
        base = base.where(Image.prompt.ilike(f"%{search}%"))

    images = await session.scalars(
        base.order_by(*order_by).limit(params.limit).offset(params.offset)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    return images.all(), total or 0


async def get_image(session: AsyncSession, *, image_id: uuid.UUID) -> Image | None:
    return await session.scalar(
        select(Image).where(Image.id == image_id, Image.deleted_at.is_(None))
    )


async def get_image_by_slug(session: AsyncSession, *, slug: str) -> Image | None:
    return await session.scalar(select(Image).where(Image.slug == slug, Image.deleted_at.is_(None)))


async def by_ids(session: AsyncSession, *, ids: Sequence[uuid.UUID]) -> list[Image]:
    """The pictures with these ids, in the order they were asked for."""
    if not ids:
        return []

    found = await session.scalars(
        select(Image).where(Image.id.in_(ids), Image.deleted_at.is_(None))
    )
    by_id = {image.id: image for image in found}

    return [by_id[one] for one in ids if one in by_id]


async def reads(session: AsyncSession, images: Sequence[Image]) -> list[ImageRead]:
    """The read shape of a page of pictures, with each maker resolved.

    The author is a profile, not a column on the picture, so it is joined here
    once for the page rather than read per card. One door builds these shapes, so
    the API and the MCP server cannot disagree about what a picture carries.
    """
    names = await display_names(session, ids=[one.created_by for one in images])

    return [
        ImageRead.model_validate(image).model_copy(
            update={"author": names.get(image.created_by) if image.created_by else None}
        )
        for image in images
    ]


async def read(session: AsyncSession, image: Image) -> ImageRead:
    """One picture, in the same shape a list returns."""
    (found,) = await reads(session, [image])

    return found
