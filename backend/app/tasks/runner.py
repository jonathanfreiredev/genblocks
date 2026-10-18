"""The task runner: claim a queued task, run it, write down what happened.

The four steps are the pipeline's shape — spec, harness, judge, commit — under
the names the checklist already uses: retrieving references, generating the
block, judging the attempt and publishing the block. All four are real: the block
is written by a model and put through the sandbox (``app/harness``), and what it
is worth is decided by a judge that did not write it (``app.judge``).

**The loop.** A run gets at most ``settings.max_attempts`` attempts at one brief.
The first attempt that clears every threshold is the one published; if none does,
the attempt that came closest is published anyway (PLAN.md, decision 6), because
a block with visible weak numbers is a better answer than a task that failed and
published nothing. A retry is told what was wrong with the attempt before it, in
the words of whoever turned it down, because a second roll of the same dice does
not pay for a second sandbox run. Every attempt stays on the record, refusals
included: the history of a block is the claim.

**The checklist grows.** The steps of the first attempt are written when the run
starts, so a reader watches what is still to come. A retry inserts its own pair
in front of the publish step, which moves down: a checklist is read in order and
the publishing line belongs last, and two attempts sharing one row would have to
say "generating" while the judge was already reading. An attempt the sandbox
refused closes its judging row all the same — with the sandbox's own words
instead of a score, because a row left queued for ever is a worse answer than one
that names who turned it down.

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
from app.judge import scoring as judge
from app.judge.schemas import Judged
from app.settings import settings
from app.tasks import canned, service
from app.tasks.models import StepStatus, Task, TaskStatus, TaskStep

logger = structlog.get_logger("app.tasks.runner")

RETRIEVE_STEP = "Retrieving references"
GENERATE_STEP = "Generating the block"
JUDGE_STEP = "Judging the attempt"
PUBLISH_STEP = "Publishing the block"

# The checklist every run writes, in order. Written up front rather than as the
# work happens: a reader should see what is still to come, not only what is done.
# These four steps are the first attempt's; a retry appends its own (see
# ``_step``). Moderation prepends itself here when it lands (Fase 11).
STEP_NAMES = (RETRIEVE_STEP, GENERATE_STEP, JUDGE_STEP, PUBLISH_STEP)

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

    def __init__(self, result: SandboxResult, *, attempts: int = 1) -> None:
        said = "; ".join(f"{check.name}: {check.detail or 'failed'}" for check in result.failures)
        every = "every attempt" if attempts > 1 else "the attempt"
        super().__init__(f"The sandbox refused {every} — {said}")


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

        try:
            spec = await _retrieve(session, task=task, step=steps[0])
            attempt = await _run_attempts(session, task=task, spec=spec, steps=steps)
            # The publish step is the one the checklist closed with, moved down by
            # every retry that inserted itself in front of it.
            await _publish(session, task=task, step=steps[-1], attempt=attempt, spec=spec)
        except Exception as error:  # noqa: BLE001 - the task row is where this is kept
            await _fail(session, task_id=task.id, error=error)


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


async def _run_attempts(
    session: AsyncSession,
    *,
    task: Task,
    spec: canned.CannedSpec,
    steps: list[TaskStep],
) -> Generation:
    """Try one brief up to the allowed number of attempts, and pick what to publish.

    Returns the first attempt that cleared every threshold, or — when none did —
    the one that came closest, which is published with its weak numbers showing
    (PLAN.md, decision 6). Raises :class:`HarnessRefused` when no attempt got as
    far as being judged: a run in which the sandbox turned down everything has
    nothing to publish, and its own words are the error.
    """
    # The checklist opens with the first attempt's pair and closes with publishing.
    generating, judging = steps[1], steps[2]
    publish = steps[-1]

    attempts: list[Generation] = []
    last_result: SandboxResult | None = None
    feedback: str | None = None

    for attempt_no in range(1, settings.max_attempts + 1):
        generating = await _step(
            session,
            opening=generating if attempt_no == 1 else None,
            publish=publish,
            name=GENERATE_STEP,
            attempt_no=attempt_no,
        )

        attempt, found = await _generate(
            session,
            task=task,
            step=generating,
            spec=spec,
            attempt_no=attempt_no,
            feedback=feedback,
        )
        attempts.append(attempt)
        last_result = found

        judging = await _step(
            session,
            opening=judging if attempt_no == 1 else None,
            publish=publish,
            name=JUDGE_STEP,
            attempt_no=attempt_no,
        )

        if found.blocked:
            # Refused before the judge read it, and the step is closed either way:
            # the checklist was opened with it, and an attempt has to say what
            # became of it rather than leave a row queued for ever. The retry is
            # worth making here more than anywhere else — code that does not build
            # is code that can be fixed, and the sandbox said what was wrong.
            await _finish(
                session,
                judging,
                detail={"attempt": attempt_no, "refused": _refused(found)},
            )
            feedback = _refused_feedback(found)
            continue

        judged = await _judge(
            session,
            step=judging,
            attempt=attempt,
            brief=task.brief,
            found=found,
            attempt_no=attempt_no,
        )
        if judged.passed:
            return attempt

        feedback = _judge_feedback(judged)

    if last_result is None or not any(one.scores for one in attempts):
        raise HarnessRefused(last_result or SandboxResult(), attempts=len(attempts))

    # Nothing cleared the bar, so the closest one goes out: the registry's claim
    # is that the numbers are visible, not that every block is good.
    return max(attempts, key=lambda one: judge.margin(one.scores or {}))


async def _step(
    session: AsyncSession,
    *,
    opening: TaskStep | None,
    publish: TaskStep,
    name: str,
    attempt_no: int,
) -> TaskStep:
    """The step this work runs in, written if the checklist does not have it.

    The checklist opens with one attempt's steps, so the first attempt uses what
    is already there. A retry's step is inserted in front of the publish step,
    which moves down by one: the checklist is read in order and the publishing
    line belongs last, so the alternative — one generating row reused by both
    attempts — would have to say "generating" while the judge was already reading.
    """
    if opening is not None:
        return opening

    step = TaskStep(
        task_id=publish.task_id,
        index=publish.index,
        name=step_name(name, attempt_no),
    )
    publish.index += 1
    session.add(step)
    await session.commit()
    return step


def step_name(name: str, attempt_no: int) -> str:
    """A step's name on a retry, which has to say that it is one.

    Two rows with the same name would read as one step that happened twice by
    accident rather than as a second attempt.
    """
    return name if attempt_no == 1 else f"{name} (attempt {attempt_no})"


async def _generate(
    session: AsyncSession,
    *,
    task: Task,
    step: TaskStep,
    spec: canned.CannedSpec,
    attempt_no: int,
    feedback: str | None,
) -> tuple[Generation, SandboxResult]:
    """Write one attempt and put it through the sandbox.

    The order is a reader's order — write it, check it, photograph it, keep the
    record — and what the sandbox proves is written on the attempt rather than
    only on the step, because the judge reads it there.

    Whether a refusal ends the run is not decided here: an attempt the sandbox
    turns down is one a retry can still fix, and only the loop knows whether
    there is one left.
    """
    await _begin(session, step)

    code = await generator.write_component(
        brief=task.brief,
        category=spec.category_slug,
        feedback=feedback,
    )

    found = await sandbox.check([SandboxFile(path=BLOCK_PATH, content=code)])
    stored = await _store(found, task=task, attempt_no=attempt_no)

    attempt = Generation(
        task_id=task.id,
        attempt_no=attempt_no,
        code=code,
        # A model wrote this, and the attempt credits it. The judge runs on the
        # same model as a separate agent; what it scored is in ``scores``.
        model=settings.llm_model,
        screenshot_path=stored,
        checks=found.record(),
        # Refused is decided, judged is not yet: an attempt nobody has read is a
        # candidate, and it stops being one the moment either turn-down lands.
        verdict=Verdict.REJECTED if found.blocked else Verdict.CANDIDATE,
    )
    session.add(attempt)
    # Committed before the refusal is acted on: a failure reaches the failure
    # path, which rolls the session back, and the attempt has to survive that.
    await session.commit()

    await _finish(session, step, detail={"attempt": attempt_no, "checks": _tally(found)})
    return attempt, found


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


async def _judge(
    session: AsyncSession,
    *,
    step: TaskStep,
    attempt: Generation,
    brief: str,
    found: SandboxResult,
    attempt_no: int,
) -> Judged:
    """Score one attempt, and say whether it clears every bar.

    The judge reads the artifacts the sandbox left — the brief it was written
    from, the code, what the sandbox found, and the render — and never the
    attempt's own row: a judge reading a verdict it wrote earlier is not a second
    opinion (PLAN.md, decision 7).
    """
    await _begin(session, step)

    judged = await judge.score_component(brief=brief, code=attempt.code, found=found)

    attempt.scores = judged.scores
    attempt.rubric_version = judged.version
    if not judged.passed:
        attempt.verdict = Verdict.REJECTED
    await session.commit()

    detail = {"attempt": attempt_no, "weakest": _weakest(judged)}
    if judged.below:
        detail["below"] = ", ".join(judged.below)
    await _finish(session, step, detail=detail)
    return judged


def _weakest(judged: Judged) -> str:
    """The dimension that decided the attempt, as the checklist's one number.

    The lowest score rather than the mean, and for the same reason the attempt
    ledger is written that way (``frontend/lib/vault/rubric.ts``): a mean can
    look respectable on an attempt that failed a dimension, which is the one
    thing a line about a judgement must never do.
    """
    dimension = min(judged.scores, key=lambda name: judged.scores[name])

    return f"{dimension} {judged.scores[dimension]}"


def _judge_feedback(judged: Judged) -> str:
    """What the judge found, in the words the next attempt is told about it."""
    said = [
        f"- {dimension} ({judged.scores[dimension]}, below {judge.threshold_for(dimension)}): "
        f"{judged.notes[dimension]}"
        for dimension in judged.below
    ]

    return "\n".join([*said, f"The judge's own summary: {judged.summary}"])


def _refused(found: SandboxResult) -> str:
    """Which checks turned the attempt down, as one line for the checklist."""
    return ", ".join(check.name for check in found.failures)


def _refused_feedback(found: SandboxResult) -> str:
    """What the sandbox refused, in the words the next attempt is told about it."""
    return "\n".join(f"- {check.name}: {check.detail or 'failed'}" for check in found.failures)


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

    # The winner wears the verdict now: it may be an attempt that was rejected on
    # its way here and is still the best the run produced.
    attempt.verdict = Verdict.PUBLISHED
    component.winning_generation_id = attempt.id
    task.component_id = component.id
    task.status = TaskStatus.SUCCEEDED
    task.finished_at = utcnow()
    task.error = None

    await _finish(session, step, detail={"slug": slug, "attempt": attempt.attempt_no})


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


async def _fail(session: AsyncSession, *, task_id: uuid.UUID, error: Exception) -> None:
    """Record a failure on the task, whatever state the session is in.

    The rollback comes first because a failure can be the database's: the row
    that reports it has to be written on a session that still works. Re-reading
    the task afterwards is the price of that rollback, which expires what the
    run was holding.

    The step that failed is the one still open. A run works through one step at
    a time and closes each before opening the next, so the ``running`` row is the
    step the failure happened in — and reading it back off the table is what
    saves a retry's steps from having to be numbered by hand across a rollback.
    """
    await session.rollback()

    task = await service.get_task(session, task_id=task_id)
    if task is None:  # pragma: no cover - the task was there when the run started
        return

    now = utcnow()
    step = await session.scalar(
        select(TaskStep).where(
            TaskStep.task_id == task_id,
            TaskStep.status == StepStatus.RUNNING,
        )
    )
    if step is not None:
        step.status = StepStatus.FAILED
        step.finished_at = now

    task.status = TaskStatus.FAILED
    task.finished_at = now
    task.error = str(error) or type(error).__name__
    await session.commit()

    logger.info("task failed", task_id=str(task_id), error=task.error)
