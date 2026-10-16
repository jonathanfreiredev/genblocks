"""The task runner: claim a queued task, run it, write down what happened.

The four steps are the pipeline's shape — spec, harness, judge, commit — under
the names the checklist already uses: retrieving references, generating the
block, judging the attempt and publishing the block. What stands behind each
phase today is canned (``app.tasks.canned``); replacing it replaces a body, not
the lifecycle around it.

**Postgres is both the queue and the source of truth.** A worker claims work by
updating a ``pending`` row under ``FOR UPDATE SKIP LOCKED``, in the same
transaction as the status change, so two workers can never take the same task
and no separate broker can disagree with the table the UI reads. A process that
dies mid-run leaves its task ``running``, which is what makes the restart easy
to read: the next boot reconciles it (``app.tasks.service``), and nothing about
the task has to be recovered from memory.

A task nobody claimed and a task claimed by a worker that is gone are therefore
two different rows, told apart without any heartbeats.
"""

import asyncio
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import DEFAULT_LICENSE, Component
from app.db.models import utcnow
from app.db.session import async_session_maker
from app.generations.models import Generation, Verdict
from app.generations.service import list_generations
from app.tasks import canned, service
from app.tasks.models import StepStatus, Task, TaskStatus, TaskStep

logger = structlog.get_logger("app.tasks.runner")

# The checklist every run writes, in order. Written up front rather than as the
# work happens: a reader should see what is still to come, not only what is done.
# Moderation prepends itself here when it lands (Fase 11).
STEP_NAMES = (
    "Retrieving references",
    "Generating the block",
    "Judging the attempt",
    "Publishing the block",
)

# How long the worker waits before looking for work again. Short: the queue is
# empty almost all the time, and a poll of one indexed count is cheaper than the
# machinery that would avoid it.
POLL_SECONDS = 0.5


async def claim_next_task() -> uuid.UUID | None:
    """Take the oldest queued task and mark it running, or return ``None``.

    The row lock and the status change share one transaction on purpose: a lock
    released without the row having moved is a task two workers can both walk
    away with.
    """
    async with async_session_maker() as session:
        task = await session.scalar(
            select(Task)
            .where(Task.status == TaskStatus.PENDING, Task.deleted_at.is_(None))
            .order_by(Task.created_at, Task.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if task is None:
            return None

        task.status = TaskStatus.RUNNING
        await session.commit()
        return task.id


async def run_task(task_id: uuid.UUID) -> None:
    """Run one claimed task to its end, writing every step as it happens.

    Each phase commits before the next one starts, so a caller polling the task
    watches the checklist fill in instead of seeing it appear all at once. A
    failure is recorded on the task and returns normally: the row is the report,
    and a worker that raised here would take the next task down with it.
    """
    async with async_session_maker() as session:
        task = await service.get_task(session, task_id=task_id)
        if task is None:
            # Deleted between the claim and the run; nothing to report.
            return

        steps = await _open_checklist(session, task_id=task.id)
        # Which step the run is on, so a failure can be attributed to it.
        step_index = 0

        try:
            spec = await _retrieve(session, task=task, step=steps[step_index])

            step_index = 1
            attempt = await _generate(session, task=task, step=steps[step_index], spec=spec)

            step_index = 2
            await _judge(session, step=steps[step_index], attempt=attempt)

            step_index = 3
            await _publish(session, task=task, step=steps[step_index], attempt=attempt, spec=spec)
        except Exception as error:  # noqa: BLE001 - the task row is where this is kept
            await _fail(session, task_id=task.id, step_index=step_index, error=error)


async def run_worker(stop: asyncio.Event, *, poll_seconds: float = POLL_SECONDS) -> None:
    """Consume queued tasks until ``stop`` is set.

    Cancelling this is a clean enough way to stop: whatever was in flight stays
    ``running`` and the next boot reconciles it. That is the same path a crash
    takes, which is why it does not need one of its own.
    """
    while not stop.is_set():
        task_id = await claim_next_task()
        if task_id is None:
            await asyncio.sleep(poll_seconds)
            continue

        try:
            await run_task(task_id)
        except Exception:  # noqa: BLE001 - one bad task must not end the worker
            logger.exception("task crashed", task_id=str(task_id))


async def _open_checklist(session: AsyncSession, *, task_id: uuid.UUID) -> list[TaskStep]:
    """Write the whole checklist as pending and return it in order."""
    steps = [
        TaskStep(task_id=task_id, index=index, name=name) for index, name in enumerate(STEP_NAMES)
    ]
    session.add_all(steps)
    await session.commit()
    return steps


async def _retrieve(session: AsyncSession, *, task: Task, step: TaskStep) -> canned.CannedSpec:
    """Decide what to build. Retrieval of references arrives with RAG (Fase 10)."""
    await _begin(session, step)
    spec = await canned.build_spec(session, brief=task.brief)
    await _finish(session, step, detail={"category": spec.category_slug})
    return spec


async def _generate(
    session: AsyncSession, *, task: Task, step: TaskStep, spec: canned.CannedSpec
) -> Generation:
    """Write the first attempt. One pass, always: the retry loop is Fase 8."""
    await _begin(session, step)

    attempt = Generation(
        task_id=task.id,
        attempt_no=1,
        code=spec.code,
        # No model produced this code, and the attempt says so rather than
        # borrowing the name of one that did not run.
        model=None,
        verdict=Verdict.CANDIDATE,
    )
    session.add(attempt)

    await _finish(session, step, detail={"attempts": 1})
    return attempt


async def _judge(session: AsyncSession, *, step: TaskStep, attempt: Generation) -> None:
    """Score the attempt. The canned judge passes everything it is shown."""
    await _begin(session, step)

    attempt.scores = dict(canned.SCORES)
    attempt.rubric_version = canned.VERSION
    attempt.verdict = Verdict.PUBLISHED

    await _finish(
        session,
        step,
        detail={"verdict": Verdict.PUBLISHED, "score": canned.headline_score(canned.SCORES)},
    )


async def _publish(
    session: AsyncSession,
    *,
    task: Task,
    step: TaskStep,
    attempt: Generation,
    spec: canned.CannedSpec,
) -> None:
    """Commit: the block is created, and the task's attempts point at it.

    The block row goes in first without a winner, because the two tables point
    at each other and Postgres checks each reference as it is written.
    """
    await _begin(session, step)

    component = Component(
        # Readable enough to find in a list, and unique without a slug machine:
        # two runs of the same brief must not collide on the unique index.
        slug=f"canned-{task.id.hex[:8]}",
        title=spec.title,
        description=spec.description,
        category_id=spec.category_id,
        code=spec.code,
        delivery_prompt=task.brief,
        spec=spec.spec,
        created_by=task.created_by,
        license=DEFAULT_LICENSE,
    )
    session.add(component)
    await session.flush()

    # Every attempt of the task points at the block, not only the winner, so the
    # item can show its whole history after publication (PLAN.md, decision 21).
    for made in await list_generations(session, task_id=task.id):
        made.component_id = component.id

    component.winning_generation_id = attempt.id
    task.component_id = component.id
    task.status = TaskStatus.SUCCEEDED
    task.finished_at = utcnow()
    task.error = None

    await _finish(session, step, detail={"slug": component.slug})


async def _begin(session: AsyncSession, step: TaskStep) -> None:
    """Mark a step as running, and make that visible before the work starts."""
    step.status = StepStatus.RUNNING
    step.started_at = utcnow()
    await session.commit()


async def _finish(session: AsyncSession, step: TaskStep, *, detail: dict) -> None:
    """Mark a step as done, with whatever it has to say for itself."""
    step.status = StepStatus.SUCCEEDED
    step.finished_at = utcnow()
    step.detail = detail
    await session.commit()


async def _fail(
    session: AsyncSession, *, task_id: uuid.UUID, step_index: int, error: Exception
) -> None:
    """Record a failure on the task, whatever state the session is in.

    The rollback comes first because a failure can be the database's: the row
    that reports it has to be written on a session that still works. Re-reading
    the task afterwards is the price of that rollback, which expires what the
    run was holding.
    """
    await session.rollback()

    task = await service.get_task(session, task_id=task_id)
    if task is None:  # pragma: no cover - the task was there when the run started
        return

    now = utcnow()
    step = next((step for step in task.steps if step.index == step_index), None)
    if step is not None:
        step.status = StepStatus.FAILED
        step.finished_at = now

    task.status = TaskStatus.FAILED
    task.finished_at = now
    task.error = str(error) or type(error).__name__
    await session.commit()

    logger.info("task failed", task_id=str(task_id), step=step_index, error=task.error)
