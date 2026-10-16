"""Read side of a block's attempt history."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.generations.models import Generation


async def list_generations(
    session: AsyncSession,
    *,
    component_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
) -> Sequence[Generation]:
    """Return attempts, oldest first.

    By ``task_id`` while a task runs (the attempts have no component yet), or by
    ``component_id`` once it is published, to show an item's whole history.

    Ordered by ``created_at`` before ``attempt_no``: a block can have more than
    one producing task, and attempt numbers restart at one per task, so ordering
    by the number alone would interleave two tasks' attempts. The timestamp puts
    them back in the order they were made; the number breaks ties within a task
    (seeded attempts are written in one transaction and share a timestamp).
    """
    statement = select(Generation).where(Generation.deleted_at.is_(None))

    if component_id is not None:
        statement = statement.where(Generation.component_id == component_id)

    if task_id is not None:
        statement = statement.where(Generation.task_id == task_id)

    order_by = (Generation.created_at, Generation.attempt_no)

    return (await session.scalars(statement.order_by(*order_by))).all()
