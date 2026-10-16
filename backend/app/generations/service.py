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
    """
    statement = select(Generation).where(Generation.deleted_at.is_(None))

    if component_id is not None:
        statement = statement.where(Generation.component_id == component_id)

    if task_id is not None:
        statement = statement.where(Generation.task_id == task_id)

    return (await session.scalars(statement.order_by(Generation.attempt_no))).all()
