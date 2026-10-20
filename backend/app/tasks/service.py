"""Both sides of background tasks: queueing them and reading them back.

A task belongs to the user who started it, so callers scope by ``created_by``;
the service does not assume a public audience the way the vault does.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.briefs import service as briefs
from app.components.models import Component
from app.db.models import utcnow
from app.moderation import service as moderation
from app.pagination import ListParams
from app.tasks import limits
from app.tasks.models import StepStatus, Task, TaskStatus, TaskStep

# What the UI is told about a task a restart cut in half. Worded for a reader,
# because that is where it ends up.
INTERRUPTED_ERROR = "The worker restarted while this task was running, so it stopped."


async def create_task(session: AsyncSession, *, brief: str, created_by: uuid.UUID) -> Task:
    """Queue a task and return it.

    Queueing is the whole of it: the row is the queue. Whatever picks it up
    claims it (``app.tasks.runner``), so this writes and commits nothing else.
    """
    task = Task(brief=brief, created_by=created_by)
    session.add(task)
    await session.commit()

    # Read the empty checklist off the table before handing the task back: a
    # relationship nobody has loaded cannot be loaded later, outside the event
    # loop, and the response carries it.
    await session.refresh(task, ["steps"])
    return task


async def enqueue_task(
    session: AsyncSession, *, brief: str, created_by: uuid.UUID, fresh: bool = False
) -> Task:
    """The door a person comes through: what we already have, then what it costs.

    The order is the cost model. A brief the registry has answered is returned
    without spending the month's quota, a safety call or a run — that is what makes
    a repeat free. Then the quota, which is a count, before the moderator, which is
    a call. That early count is only a courtesy to an exhausted month; the count
    that decides happens after the moderator and under the user's lock, in the same
    transaction as the insert. Otherwise two requests can leave here with the same
    last block.

    ``create_task`` stays the row primitive: the seed files its tasks without
    spending anybody's month, and so does a test.

    ``fresh`` is somebody who has seen what the registry has and wants their own
    anyway: the cache is skipped, and the run is paid for like any other.
    """
    answered = None if fresh else await briefs.find(session, brief=brief)
    if answered is not None:
        return await _answered(session, brief=brief, created_by=created_by, component=answered)

    await limits.admitted(session, user_id=created_by)

    # End the read's transaction before the network call; the reservation below
    # opens the one that matters.
    await session.commit()

    why = await moderation.refusal(brief)
    if why is not None:
        raise moderation.BriefRejected(why)

    # From here to the commit inside ``create_task`` is the atomic section: no
    # external call, no second door.
    await limits.reserve(session, user_id=created_by)
    return await create_task(session, brief=brief, created_by=created_by)


# What the one step of a cached task is called. The checklist is still a checklist:
# a reader sees what happened, and what happened is a lookup.
ANSWERED_STEP = "Found in the registry"


async def _answered(
    session: AsyncSession, *, brief: str, created_by: uuid.UUID, component: Component
) -> Task:
    """The receipt for a brief that was built before it was asked again.

    A task rather than a bare block because the UI follows tasks: the dialog opens,
    polls, and closes on the same contract whether the block took ten minutes or
    was found in a table. The difference is the status it starts in and the step
    that says why.
    """
    now = utcnow()
    task = Task(
        brief=brief,
        created_by=created_by,
        status=TaskStatus.SUCCEEDED,
        component_id=component.id,
        finished_at=now,
        cached=True,
    )
    session.add(task)
    await session.flush()

    session.add(
        TaskStep(
            task_id=task.id,
            index=0,
            name=ANSWERED_STEP,
            status=StepStatus.SUCCEEDED,
            started_at=now,
            finished_at=now,
        )
    )
    await session.commit()
    await session.refresh(task, ["steps"])

    return task


async def interrupt_orphaned_tasks(session: AsyncSession) -> int:
    """Close the tasks a previous process left running, and say how many.

    Only a boot can tell "still running" from "orphaned": this is called from the
    process that owns the worker, before it starts claiming, so a task found
    running here belongs to a worker that no longer exists.

    The steps that were mid-flight are failed with it. Leaving one ``running``
    would have the checklist claim work is still happening on a task that has
    already stopped.
    """
    tasks = (
        await session.scalars(
            select(Task)
            .options(selectinload(Task.steps))
            .where(Task.status == TaskStatus.RUNNING, Task.deleted_at.is_(None))
        )
    ).all()
    if not tasks:
        return 0

    now = utcnow()
    for task in tasks:
        task.status = TaskStatus.INTERRUPTED
        task.finished_at = now
        task.error = INTERRUPTED_ERROR

        for step in task.steps:
            if step.status == StepStatus.RUNNING:
                step.status = StepStatus.FAILED
                step.finished_at = now

    await session.commit()
    return len(tasks)


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
