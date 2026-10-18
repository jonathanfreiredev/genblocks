"""Read side of what a task produced."""

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
    """Return what a task produced, oldest first.

    By ``task_id`` while a task runs (the artifact has no component yet), or by
    ``component_id`` once it is published. A list for one row, because the shape
    of the table is what a run makes — one artifact today, and the same call if a
    run ever makes several.
    """
    statement = select(Generation).where(Generation.deleted_at.is_(None))

    if component_id is not None:
        statement = statement.where(Generation.component_id == component_id)

    if task_id is not None:
        statement = statement.where(Generation.task_id == task_id)

    order_by = (Generation.created_at, Generation.attempt_no)

    return (await session.scalars(statement.order_by(*order_by))).all()
