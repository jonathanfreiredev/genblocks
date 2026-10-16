"""Read side of background tasks.

A task belongs to the user who started it, so callers scope by ``created_by``;
the service does not assume a public audience the way the vault does.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.pagination import ListParams
from app.tasks.models import Task


async def get_task(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
    created_by: uuid.UUID | None = None,
) -> Task | None:
    """Return one task with its steps, which the checklist needs and lazy
    loading could not fetch outside the event loop.

    ``created_by`` is the ownership check, done here rather than at each door: a
    caller who is not the task's owner reads nothing, and cannot tell a task that
    is not theirs from one that does not exist.
    """
    statement = (
        select(Task)
        .options(selectinload(Task.steps))
        .where(Task.id == task_id, Task.deleted_at.is_(None))
    )

    if created_by is not None:
        statement = statement.where(Task.created_by == created_by)

    return await session.scalar(statement)


async def list_tasks(
    session: AsyncSession,
    *,
    params: ListParams,
    created_by: uuid.UUID | None = None,
    status: str | None = None,
) -> tuple[Sequence[Task], int]:
    """Return a page of tasks, scoped to their owner and optionally to a status."""
    order_by = params.order_by(
        {"created_at": Task.created_at, "status": Task.status},
        default="-created_at",
        tiebreaker=Task.id,
    )

    base = select(Task).where(Task.deleted_at.is_(None))

    if created_by is not None:
        base = base.where(Task.created_by == created_by)

    if status is not None:
        base = base.where(Task.status == status)

    tasks = await session.scalars(
        base.options(selectinload(Task.steps))
        .order_by(*order_by)
        .limit(params.limit)
        .offset(params.offset)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    return tasks.all(), total or 0
