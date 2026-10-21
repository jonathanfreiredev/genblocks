"""Hard deletion of public artifacts.

The vault has a soft-delete column for the normal read filter, but an operator
removing an item wants the row and the CDN asset gone. This service is the one
place that does both, and it deliberately keeps the two artifacts independent:
deleting a picture leaves its blocks standing, and deleting a block leaves the
pictures it reused in the library.

The order is hide → purge → delete. If Cloudinary fails, the row stays hidden
instead of publicly serving an asset we could not remove, and the operator can
retry. Cloudinary's ``not found`` answer is treated as success so a retry can
finish a partially completed deletion.
"""

import uuid
from dataclasses import dataclass

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import Component
from app.db.models import utcnow
from app.deletion.models import DeletionAudit
from app.generations.models import Generation
from app.harness import cloudinary
from app.images.models import Image
from app.settings import settings
from app.vectors import service as vectors
from app.vectors.client import COMPONENTS, IMAGES

logger = structlog.get_logger("app.deletion")


class DeletionFailed(Exception):
    """The row is hidden, but one or more CDN assets could not be removed."""


@dataclass(frozen=True)
class DeletedItem:
    """What was removed, for the caller's log and confirmation."""

    kind: str
    id: uuid.UUID
    slug: str
    title: str
    paths: tuple[str, ...]


async def delete_component(
    session: AsyncSession, *, component_id: uuid.UUID, actor_id: uuid.UUID | None = None
) -> DeletedItem | None:
    """Permanently remove a block, its renders and its derived database rows."""
    component = await session.scalar(select(Component).where(Component.id == component_id))
    if component is None:
        return None

    renders = await session.execute(
        select(Generation.screenshot_path, Generation.thumbnail_path).where(
            Generation.component_id == component.id,
            or_(
                Generation.screenshot_path.is_not(None),
                Generation.thumbnail_path.is_not(None),
            ),
        )
    )
    paths = tuple(
        path for screenshot, thumbnail in renders.all() for path in (screenshot, thumbnail) if path
    )
    item = DeletedItem(
        kind="component",
        id=component.id,
        slug=component.slug,
        title=component.title,
        paths=paths,
    )

    await _hide(session, component)
    try:
        await _purge(item)
    except DeletionFailed as failed:
        await _audit(session, item=item, actor_id=actor_id, result="failed", error=str(failed))
        await session.commit()
        raise
    await session.delete(component)
    await _audit(session, item=item, actor_id=actor_id, result="deleted")
    await session.commit()
    await _forget(COMPONENTS, item.id)
    logger.info("component deleted", component_id=str(item.id), slug=item.slug)
    return item


async def delete_image(
    session: AsyncSession, *, image_id: uuid.UUID, actor_id: uuid.UUID | None = None
) -> DeletedItem | None:
    """Permanently remove a picture and its CDN asset, leaving blocks intact."""
    image = await session.scalar(select(Image).where(Image.id == image_id))
    if image is None:
        return None

    item = DeletedItem(
        kind="image",
        id=image.id,
        slug=image.slug,
        title=image.prompt,
        paths=(image.path,),
    )

    await _hide(session, image)
    try:
        await _purge(item)
    except DeletionFailed as failed:
        await _audit(session, item=item, actor_id=actor_id, result="failed", error=str(failed))
        await session.commit()
        raise
    await session.delete(image)
    await _audit(session, item=item, actor_id=actor_id, result="deleted")
    await session.commit()
    await _forget(IMAGES, item.id)
    logger.info("image deleted", image_id=str(item.id), slug=item.slug)
    return item


async def _hide(session: AsyncSession, target: Component | Image) -> None:
    """Take the public row out of every read path before touching the CDN."""
    if target.deleted_at is None:
        target.deleted_at = utcnow()
        await session.commit()


async def _purge(item: DeletedItem) -> None:
    """Delete the item's Cloudinary objects, or refuse to pretend it worked."""
    paths = tuple(dict.fromkeys(path for path in item.paths if path))
    if not paths:
        return

    if not cloudinary.is_configured():
        if settings.env == "production":
            raise DeletionFailed(
                "Cloudinary is not configured, so the public asset cannot be removed."
            )
        logger.warning(
            "cloudinary is not configured; deleting database rows only",
            kind=item.kind,
            item_id=str(item.id),
        )
        return

    failed: list[str] = []
    for path in paths:
        try:
            await cloudinary.destroy(path, invalidate=True)
        except Exception as broke:  # noqa: BLE001 - report every failed path
            logger.warning("cloudinary asset not deleted", path=path, error=str(broke))
            failed.append(path)

    if failed:
        raise DeletionFailed(
            "The item is hidden, but these Cloudinary assets could not be removed: "
            + ", ".join(failed)
        )


async def _forget(collection: str, item_id: uuid.UUID) -> None:
    """A deleted row must not come back through retrieval."""
    await vectors.forget(collection, ids=[item_id])


async def _audit(
    session: AsyncSession,
    *,
    item: DeletedItem,
    actor_id: uuid.UUID | None,
    result: str,
    error: str | None = None,
) -> None:
    """Add the audit row to the transaction that changes the target."""
    session.add(
        DeletionAudit(
            kind=item.kind,
            target_id=item.id,
            slug=item.slug,
            title=item.title,
            actor_id=actor_id,
            paths=list(item.paths),
            result=result,
            error=error,
        )
    )
