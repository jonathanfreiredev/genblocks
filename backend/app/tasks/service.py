"""Both sides of background tasks: queueing them and reading them back.

A task belongs to the user who started it, so callers scope by ``created_by``;
the service does not assume a public audience the way the vault does.
"""

import uuid
from collections.abc import Sequence
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.briefs import service as briefs
from app.components.models import Component
from app.components.planning import ImageConfirmationRequired, plan
from app.db.models import utcnow
from app.images.planning import (
    ImagePlan,
    ImagePromptRejected,
    ImageSuggestionRequired,
    plan_image,
)
from app.moderation import service as moderation
from app.pagination import ListParams
from app.tasks import limits
from app.tasks.models import StepStatus, Task, TaskKind, TaskStatus, TaskStep

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


async def create_image_task(
    session: AsyncSession,
    *,
    prompt: str,
    width: int,
    height: int,
    category_id: uuid.UUID,
    created_by: uuid.UUID,
) -> Task:
    """Queue one standalone image task, with the inputs the worker needs."""
    task = Task(
        kind=TaskKind.GENERATE_IMAGE,
        brief=prompt,
        image_width=width,
        image_height=height,
        image_category_id=category_id,
        created_by=created_by,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task, ["steps"])
    return task


async def _wake_worker() -> None:
    """Wake the queue's worker, when this deployment has one.

    The import lives here rather than at the top of the module because the Modal
    SDK costs a couple of hundred milliseconds to import and only these two doors
    need it. The MCP reads the catalogue far more often than it queues work, so
    this keeps its process free of the SDK until an agent actually asks for
    something.
    """
    from app.tasks.trigger import wake_worker

    await wake_worker()


async def enqueue_image_task(
    session: AsyncSession,
    *,
    prompt: str,
    width: int,
    height: int,
    category: str,
    created_by: uuid.UUID,
) -> Task:
    """The door for a standalone image: quota, policy, then a queued task."""
    await limits.admitted(session, user_id=created_by)
    await session.commit()

    plan: ImagePlan = await plan_image(
        session, prompt=prompt, width=width, height=height, category=category
    )
    if not plan.ready:
        if plan.needs_confirmation and plan.suggested_prompt is not None:
            raise ImageSuggestionRequired(plan)
        raise ImagePromptRejected(plan)

    if plan.category_id is None:  # pragma: no cover - a ready plan always has one
        raise ImagePromptRejected(plan)

    await limits.reserve(session, user_id=created_by)
    task = await create_image_task(
        session,
        prompt=plan.prompt,
        width=plan.width,
        height=plan.height,
        category_id=plan.category_id,
        created_by=created_by,
    )
    # The row is committed by now, so waking a worker can only ever find work to
    # do. Never the other way round: nothing is woken before there is a row.
    await _wake_worker()
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
    # The brief has already produced a public block. That answer stays free; the
    # policy was applied when it was first built.
    answered = None if fresh else await briefs.find(session, brief=brief)
    if answered is not None:
        return await _answered(session, brief=brief, created_by=created_by, component=answered)

    await limits.admitted(session, user_id=created_by)

    # End the read's transaction before the network calls; the reservation below
    # opens the one that matters.
    await session.commit()

    decision = await plan(brief)
    if not decision.ready:
        if decision.needs_confirmation and decision.proposed_brief is not None:
            raise ImageConfirmationRequired(
                reason=decision.reason,
                proposed_brief=decision.proposed_brief,
            )
        raise moderation.BriefRejected(decision.reason)

    # From here to the commit inside ``create_task`` is the atomic section: no
    # external call, no second door.
    await limits.reserve(session, user_id=created_by)
    task = await create_task(session, brief=brief, created_by=created_by)
    # The row is committed by now, so waking a worker can only ever find work to
    # do. Never the other way round: nothing is woken before there is a row.
    await _wake_worker()
    return task


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


async def interrupt_orphaned_tasks(
    session: AsyncSession, *, older_than_seconds: int | None = None
) -> int:
    """Close the tasks a process left running, and say how many.

    Without a cutoff, every running task is taken to be orphaned. That is what a
    process which owns the queue on its own can assume: the API in development
    reconciles before it claims, so a task found running there belongs to a
    worker that no longer exists.

    With ``older_than_seconds``, only tasks that have been running at least that
    long are touched. That is what the deployed worker needs, because its runs
    overlap: the schedule fires every minute and one run can last for minutes,
    so a task being worked on right now looks exactly like one a dead run
    abandoned. Age is the only thing that separates them, and the cutoff has to
    stay longer than a run's own timeout or it would interrupt live work.

    ``updated_at`` is the clock it reads. The claim writes the row and nothing
    writes it again until the run is over, so it stands for "running since"; the
    comparison happens in the database so both sides share one clock.

    The steps that were mid-flight are failed with it. Leaving one ``running``
    would have the checklist claim work is still happening on a task that has
    already stopped.
    """
    query = (
        select(Task)
        .options(selectinload(Task.steps))
        .where(Task.status == TaskStatus.RUNNING, Task.deleted_at.is_(None))
    )
    if older_than_seconds is not None:
        query = query.where(Task.updated_at < func.now() - timedelta(seconds=older_than_seconds))

    tasks = (await session.scalars(query)).all()
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
