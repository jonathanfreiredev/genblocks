"""The task runner: claim a queued task, run it, write down what happened.

The four steps are the pipeline's shape — spec, harness, judge, commit — under
the names the checklist already uses: retrieving references, generating the
block, judging the attempt and publishing the block. Two of them are real now:
the block is written by a model and put through the sandbox (``app/harness``).
The spec and the judge are still stand-ins (``app.tasks.canned``); replacing one
replaces a body, not the lifecycle around it.

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
import re
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import DEFAULT_LICENSE, Component
from app.db.models import utcnow
from app.db.session import async_session_maker
from app.generations.models import Generation, Verdict
from app.generations.service import list_generations
from app.harness import generator, sandbox, screenshots
from app.harness.schemas import SandboxFile, SandboxResult
from app.settings import settings
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

# Where the generated block goes in the sandbox's project: the file the
# scaffold's entry point imports (``app/harness/scaffold/src/main.tsx``). The
# sandbox writes files wherever it is told, so this is the caller's half of that
# contract.
BLOCK_PATH = "src/Block.tsx"

# How much of a title becomes a slug, and how much of the task's id keeps it
# unique. A slug machine that checks the table arrives with the registry work.
SLUG_STEM_LIMIT = 48
SLUG_SUFFIX_LENGTH = 6

# How long the worker waits before looking for work again. Short: the queue is
# empty almost all the time, and a poll of one indexed count is cheaper than the
# machinery that would avoid it.
POLL_SECONDS = 0.5


class HarnessRefused(Exception):
    """The sandbox found something a run cannot publish past.

    Carries the sandbox's own words, because the task's error is where a reader
    ends up and "typecheck: src/Block.tsx(12,7): Property 'x' does not exist" is
    the answer they came for.
    """

    def __init__(self, result: SandboxResult) -> None:
        said = "; ".join(f"{check.name}: {check.detail or 'failed'}" for check in result.failures)
        super().__init__(f"The sandbox refused the attempt — {said}")


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
    """Write the first attempt and put it through the sandbox.

    One pass, always: the retry loop is Fase 8, and what decides between two
    attempts is the judge. The order is a reader's order — write it, check it,
    photograph it, keep the record — and what the sandbox proves is written on the
    attempt rather than only on the step, because the judge will read it there.

    Code that does not typecheck, does not bundle or renders nothing is not
    published: it fails the task with the sandbox's own words. The attempt stays
    behind either way, since "we tried and it did not hold up" is part of the
    claim the registry makes.
    """
    await _begin(session, step)

    code = await generator.write_component(brief=task.brief, category=spec.category_slug)
    found = await sandbox.check([SandboxFile(path=BLOCK_PATH, content=code)])
    stored = await _store(found, task=task, attempt_no=1)

    attempt = Generation(
        task_id=task.id,
        attempt_no=1,
        code=code,
        # A model wrote this, and the attempt credits it. The scores it will
        # carry are still the stand-in's (Fase 8), and those say so.
        model=settings.llm_model,
        screenshot_path=stored,
        checks=found.record(),
        verdict=Verdict.CANDIDATE,
    )
    session.add(attempt)
    # Committed before the sandbox's verdict is acted on: a refusal below reaches
    # the failure path, which rolls the session back, and the attempt has to
    # survive that.
    await session.commit()

    if found.blocked:
        raise HarnessRefused(found)

    await _finish(
        session,
        step,
        detail={"attempts": 1, "checks": _tally(found)},
    )
    return attempt


async def _store(result: SandboxResult, *, task: Task, attempt_no: int) -> str | None:
    """Put the render in Cloudinary and return its public id, if there is one.

    A run that never got as far as a page has nothing to store, and nothing is
    an honest answer here: the attempt's ``screenshot_path`` stays null and the
    UI says the asset is not there.
    """
    if result.screenshot is None:
        return None

    return await screenshots.store(
        result.screenshot,
        name=screenshots.public_id(task.id, attempt_no),
    )


def _tally(result: SandboxResult) -> str:
    """The checks as one line, for the checklist a reader follows."""
    return f"{sum(1 for check in result.checks if check.ok)}/{len(result.checks)}"


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

    The code published is the winning attempt's, verbatim: the block is a
    snapshot of what the judge approved, not a copy assembled from the spec.
    """
    await _begin(session, step)

    slug = slug_for(title=spec.title, task_id=task.id)
    component = Component(
        slug=slug,
        title=spec.title,
        description=spec.description,
        category_id=spec.category_id,
        code=attempt.code,
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

    await _finish(session, step, detail={"slug": slug})


def slug_for(*, title: str, task_id: uuid.UUID) -> str:
    """A block's slug: its title, and enough of the task to be unique.

    The unique index wants uniqueness and a reader wants to recognise the piece,
    so the title carries it and six characters of the task's id make it hold.
    Deduplicating against the table, and translating properly, belongs to the
    registry work that needs it.
    """
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:SLUG_STEM_LIMIT].strip("-")

    return f"{stem}-{task_id.hex[:SLUG_SUFFIX_LENGTH]}" if stem else f"block-{task_id.hex[:8]}"


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

    The step is looked up on its own rather than through ``task.steps``: that
    collection was read when the run started, before the checklist existed, and a
    session that does not expire on commit would hand back the empty list it was
    holding.
    """
    await session.rollback()

    task = await service.get_task(session, task_id=task_id)
    if task is None:  # pragma: no cover - the task was there when the run started
        return

    now = utcnow()
    step = await session.scalar(
        select(TaskStep).where(TaskStep.task_id == task_id, TaskStep.index == step_index)
    )
    if step is not None:
        step.status = StepStatus.FAILED
        step.finished_at = now

    task.status = TaskStatus.FAILED
    task.finished_at = now
    task.error = str(error) or type(error).__name__
    await session.commit()

    logger.info("task failed", task_id=str(task_id), step=step_index, error=task.error)
