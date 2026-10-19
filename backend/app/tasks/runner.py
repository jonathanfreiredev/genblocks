"""The task runner: claim a queued task, run it, write down what happened.

The four steps are the pipeline's shape — spec, harness, judge, commit — under
the names the checklist already uses: retrieving references, generating the
block, judging the attempt and publishing the block. All four are real: the block
is written, built and looked at by an agent (``app.harness``), and what it is
worth is decided by a judge that did not write it (``app.judge``).

**One attempt, and a gate.** A run makes one attempt. The judge reads it once, at
the end, and is a **gate**: a block that does not clear every threshold is not
published, its attempt stays on the task with the judge's reasons on it, and the
task fails. The registry only holds blocks that passed — that is an invariant of
the product, not a promise (PLAN.md, decisions 30 and 31). Retrying is a person's
decision (``POST /v1/tasks``, with the brief in front of them), and the loop that
used to live here now lives inside the harness, where it can see the artifact.

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
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.briefs import service as briefs
from app.categories import service as categories_service
from app.components.models import DEFAULT_LICENSE, Component, ComponentAsset
from app.db.models import utcnow
from app.db.session import async_session_maker
from app.generations.models import Generation, Verdict
from app.generations.service import list_generations
from app.harness import agent as harness
from app.harness import checks, cloudinary
from app.harness.schemas import SandboxFile, SandboxResult
from app.images.models import Image
from app.judge import scoring as judge
from app.judge.schemas import Judged
from app.moderation import service as moderation
from app.settings import settings
from app.tasks import service
from app.tasks import spec as block_spec
from app.tasks.models import StepStatus, Task, TaskStatus, TaskStep
from app.vectors import service as vectors

logger = structlog.get_logger("app.tasks.runner")

STEP_NAMES = (
    "Retrieving references",
    "Generating the block",
    "Judging the attempt",
    "Publishing the block",
)

# The image taxonomy's kind. Pictures are filed under their own half of the
# taxonomy, which is why the harness is handed the types rather than inventing one.
PICTURE_KIND = "image"

# How much of a title becomes a slug, and how much of the task's id keeps it
# unique. A slug machine that checks the table arrives with the registry work.
SLUG_STEM_LIMIT = 48
SLUG_SUFFIX_LENGTH = 6

# How long the worker waits before looking for work again. Short: the queue is
# empty almost all the time, and a poll of one indexed count is cheaper than the
# machinery that would avoid it.
POLL_SECONDS = 0.5


class HarnessRefused(Exception):
    """A check found something a run cannot publish past.

    Carries the check's own words, because the task's error is where a reader ends
    up and "typecheck: src/Block.tsx(12,7): Property 'x' does not exist" is the
    answer they came for.
    """

    def __init__(self, result: SandboxResult) -> None:
        said = "; ".join(f"{check.name}: {check.detail or 'failed'}" for check in result.failures)
        super().__init__(f"The block was refused — {said}")


class ModerationRefused(Exception):
    """The block, once written, was refused before it could be judged.

    The reason is the moderator's own sentence: a reader of the failed task should
    learn what about the artifact did not pass, not just that something did.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"The block was refused by moderation — {reason}")


class JudgeRejected(Exception):
    """The judge scored the attempt under a bar, so nothing is published.

    Carries the judge's own reading — which dimensions missed, by how much, and
    why — because the task's error is where a reader lands and "visual 68, below
    75: the hierarchy is flat" is the answer they came for.
    """

    def __init__(self, judged: Judged) -> None:
        missed = "; ".join(
            f"{dimension} {judged.scores[dimension]}, below {judge.threshold_for(dimension)}: "
            f"{judged.notes[dimension]}"
            for dimension in judged.below
        )
        super().__init__(f"The judge did not publish it — {missed}. {judged.summary}")


class PictureUnfiled(Exception):
    """A picture came back for a type the library does not have."""


@dataclass(frozen=True)
class Made:
    """What the harness step produced: the attempt, and what it was built with."""

    attempt: Generation
    found: SandboxResult
    built: harness.Built
    # The pictures it asked for, already in the library and already scored.
    pictures: list[Image]


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
            made = await _build(session, task=task, step=steps[1], spec=spec)
            await _judge(
                session, step=steps[2], attempt=made.attempt, found=made.found, brief=task.brief
            )
            await _publish(session, task=task, step=steps[3], spec=spec, made=made)
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


async def _retrieve(session: AsyncSession, *, task: Task, step: TaskStep) -> block_spec.BlockSpec:
    """Decide what to build: the type it is filed under, and the copy.

    The type comes from the taxonomy, read by the model against the blocks the
    registry already holds (Fase 10). It is the first thing a run decides and the
    first place a model is asked anything other than the artifact itself.
    """
    await _begin(session, step)
    decided = await block_spec.build_spec(session, brief=task.brief)
    await _finish(session, step, detail={"category": decided.category_slug})
    return decided


async def _build(
    session: AsyncSession, *, task: Task, step: TaskStep, spec: block_spec.BlockSpec
) -> Made:
    """Build the block with the harness, and turn the result into an attempt.

    The order is a reader's order: build it, keep the pictures it asked for, check
    the project as it was left, store the render, write the attempt. The judge does
    not run here — it reads the attempt afterwards — and a refusal ends the run
    rather than sending it round again: the loop that fixes a broken build lives in
    the harness now, where it can see the artifact.
    """
    await _begin(session, step)

    picture_types = await _picture_categories(session)
    built = await harness.build(
        brief=task.brief,
        category=spec.category_slug,
        image_categories=list(picture_types),
        library=_picture_library(session, types=picture_types),
    )
    # Moderation before the pictures and the render: an artifact that will not be
    # published should not be photographed first. The brief was checked before the
    # task existed; this is the copy the block actually grew, which can differ.
    why = await moderation.refusal(_project_text(built.files))
    if why is not None:
        raise ModerationRefused(why)

    pictures = await _keep(session, task=task, built=built, types=picture_types)

    found = await checks.check(
        [SandboxFile(path=path, content=content) for path, content in sorted(built.files.items())]
    )
    stored = await _store(found, task=task)
    attempt = Generation(
        task_id=task.id,
        # One artifact per run: the number is the invariant the table enforces
        # rather than a counter of tries.
        attempt_no=1,
        # The project, and which file of it is the block. No copy of the entry
        # file beside it: the text lives in ``files`` and nowhere else.
        files=built.files,
        entry=harness.ENTRY,
        model=settings.llm_model,
        screenshot_path=stored,
        checks=found.record(),
        verdict=Verdict.REJECTED if found.blocked else Verdict.CANDIDATE,
    )
    session.add(attempt)
    # Committed before the refusal is acted on: a failure reaches the failure path,
    # which rolls the session back, and the attempt has to survive that.
    await session.commit()

    await _finish(
        session,
        step,
        detail={
            "checks": _tally(found),
            "files": len(built.files),
            "iterations": built.iterations,
            "skills": built.skills,
        },
    )

    if found.blocked:
        raise HarnessRefused(found)

    return Made(attempt=attempt, found=found, built=built, pictures=pictures)


async def _keep(
    session: AsyncSession,
    *,
    task: Task,
    built: harness.Built,
    types: dict[str, uuid.UUID],
) -> list[Image]:
    """File the pictures the harness asked for in the library, and score each one.

    They are kept whether or not the block is published: a stock image is an
    artifact of its own, it is what the library browses, and it is what a later
    run reuses instead of generating again (Fase 10).
    """
    pictures: list[Image] = []

    for placed in built.images:
        if placed.library_id is not None:
            # Already the library's: reused, not re-filed. It was scored when it
            # came in, and scoring it again would be a second opinion on the same
            # bytes.
            existing = await session.get(Image, placed.library_id)
            if existing is None:
                raise PictureUnfiled("The picture this block reused is no longer in the library.")
            pictures.append(existing)
            continue

        if placed.image is None:
            raise PictureUnfiled("A picture was placed with neither bytes nor a library id.")

        category_id = types.get(placed.category)
        if category_id is None:
            raise PictureUnfiled(
                f"The image library has no {placed.category!r} type to file a picture under."
            )

        judged = await judge.score_image(
            prompt=placed.image.prompt,
            image=placed.image.data,
            width=placed.image.width,
            height=placed.image.height,
            media_type=placed.image.media_type,
        )
        picture = Image(
            prompt=placed.image.prompt,
            path=placed.image.path,
            width=placed.image.width,
            height=placed.image.height,
            category_id=category_id,
            created_by=task.created_by,
            model=settings.image_model,
            scores=judged.scores,
            rubric_version=judged.version,
        )
        session.add(picture)
        pictures.append(picture)

    if pictures:
        await session.commit()

    # Remembered after the rows exist: a picture is the library's from the moment
    # it is filed, whether or not the block that asked for it is published.
    for placed, picture in zip(built.images, pictures, strict=True):
        if placed.library_id is not None:
            # A picture the library already had: it is remembered once, and this
            # run did not make it.
            continue

        remembered = await vectors.remember_image(
            image_id=picture.id,
            prompt=picture.prompt,
            picture=placed.image.data if placed.image else None,
            category=placed.category,
        )
        if not remembered:
            logger.warning("filed picture is not searchable", path=picture.path)

    return pictures


async def _picture_categories(session: AsyncSession) -> dict[str, uuid.UUID]:
    """The image half of the taxonomy, as slug → id.

    Read here rather than inside the harness so the harness never reaches for the
    database, and handed to the agent through its tool: a picture's type is the
    library's, not something a model invents.
    """
    categories = await categories_service.list_categories(session, kind=PICTURE_KIND)

    return {category.slug: category.id for category in categories}


async def _store(result: SandboxResult, *, task: Task) -> str | None:
    """Put the render in Cloudinary and return its public id, if there is one.

    A run that never got as far as a page has nothing to store, and nothing is
    an honest answer here: the attempt's ``screenshot_path`` stays null and the
    UI says the asset is not there.
    """
    if result.screenshot is None:
        return None

    return await cloudinary.store(
        result.screenshot,
        name=cloudinary.screenshot_id(task.id, 1),
    )


def _project_text(files: dict[str, str]) -> str:
    """The project as one text for the moderator: each path, then its contents."""
    return "\n\n".join(f"{path}\n{content}" for path, content in sorted(files.items()))


def _tally(result: SandboxResult) -> str:
    """The checks as one line, for the checklist a reader follows."""
    return f"{sum(1 for check in result.checks if check.ok)}/{len(result.checks)}"


async def _judge(
    session: AsyncSession,
    *,
    step: TaskStep,
    attempt: Generation,
    found: SandboxResult,
    brief: str,
) -> Judged:
    """Score the attempt once, and stop the run if it does not clear every bar.

    The judge reads the artifacts the harness left — the brief, the whole project,
    what the sandbox found, and the render — and never the attempt's own row: a
    judge reading a verdict it wrote earlier is not a second opinion (PLAN.md,
    decision 7). What it is *not* told is the thresholds: a judge that knows where
    the bar is scores to the bar.
    """
    await _begin(session, step)

    judged = await judge.score_component(
        brief=brief,
        files=attempt.files,
        found=found,
    )

    attempt.scores = judged.scores
    attempt.rubric_version = judged.version
    if not judged.passed:
        attempt.verdict = Verdict.REJECTED
    await session.commit()

    detail = {"weakest": _weakest(judged)}
    if judged.below:
        detail["below"] = ", ".join(judged.below)
    await _finish(session, step, detail=detail)

    if not judged.passed:
        raise JudgeRejected(judged)

    return judged


def _weakest(judged: Judged) -> str:
    """The dimension that decided the attempt, as the checklist's one number.

    The lowest score rather than the mean: a mean can look respectable on a run
    that failed a dimension, which is the one thing a line about a judgement must
    never do.
    """
    dimension = min(judged.scores, key=lambda name: judged.scores[name])

    return f"{dimension} {judged.scores[dimension]}"


async def _publish(
    session: AsyncSession,
    *,
    task: Task,
    step: TaskStep,
    spec: block_spec.BlockSpec,
    made: Made,
) -> None:
    """Commit: the block is created, and the task's attempts point at it.

    The block row goes in first without a winner, because the two tables point
    at each other and Postgres checks each reference as it is written.

    The project published is the winning attempt's, verbatim: the block is a
    snapshot of what the judge approved, not a copy assembled from the spec.
    """
    await _begin(session, step)

    slug = slug_for(title=spec.title, task_id=task.id)
    component = Component(
        slug=slug,
        title=spec.title,
        description=spec.description,
        category_id=spec.category_id,
        files=made.attempt.files,
        entry=made.attempt.entry,
        # What the sandbox read from the project itself: the install line a visitor
        # needs, and the only version of it that cannot be a model's guess.
        dependencies=made.found.dependencies,
        delivery_prompt=task.brief,
        spec=spec.spec,
        created_by=task.created_by,
        license=DEFAULT_LICENSE,
    )
    session.add(component)
    await session.flush()

    # Every attempt of the task points at the block — one row, and the shape is
    # the same whether a run makes one artifact or several (PLAN.md, decision 21).
    for also in await list_generations(session, task_id=task.id):
        also.component_id = component.id

    # The pictures, in the slots the block put them in: what a visitor needs to
    # know which assets came with the code (PLAN.md, decision 36).
    for placed, picture in zip(made.built.images, made.pictures, strict=True):
        session.add(
            ComponentAsset(component_id=component.id, image_id=picture.id, slot=placed.slot)
        )

    # The brief and the block it became, in the same transaction: a cache entry
    # that survives a publish which did not would answer with something that is
    # not there.
    await briefs.remember(session, brief=task.brief, component_id=component.id)

    made.attempt.verdict = Verdict.PUBLISHED
    component.winning_generation_id = made.attempt.id
    task.component_id = component.id
    task.status = TaskStatus.SUCCEEDED
    task.finished_at = utcnow()
    task.error = None

    await _finish(
        session,
        step,
        detail={
            "slug": slug,
            "files": len(made.attempt.files or {}),
            "pictures": len(made.pictures),
        },
    )

    # Remembered after the block is committed, and after the step is closed: the
    # registry is the truth and the index is a way to find it again, so a store
    # that is having a bad day costs a search result, not a published block.
    remembered = await vectors.remember_component(
        component_id=component.id,
        text=_remembered_as(component),
        screenshot=made.found.screenshot,
        slug=component.slug,
        category=spec.category_slug,
    )
    if not remembered:
        logger.warning("published block is not searchable", slug=component.slug)


def _picture_library(
    session: AsyncSession, *, types: dict[str, uuid.UUID]
) -> Callable[[str, str], Awaitable[harness.Reused | None]]:
    """The library as the harness asks it: a description and a type, a picture back.

    The nearest picture in the same type is reused when it is close enough that
    generating another would be paying twice for the same photograph
    (``settings.image_reuse_distance``). Retrieval failing is not a reason to stop
    a run, so anything that goes wrong here answers "nothing in the library" and
    the picture is made.

    The session is opened per call rather than held: the harness is a separate
    concern and must not be handed one to keep.
    """

    async def look(prompt: str, category: str) -> harness.Reused | None:
        category_id = types.get(category)
        if category_id is None:
            return None

        try:
            found = await vectors.find_images(prompt, limit=1, category=category)
        except Exception as broke:  # noqa: BLE001 - a search is not worth a failed run
            logger.warning("image library not searched", error=str(broke))
            return None

        if not found or found[0].distance > settings.image_reuse_distance:
            return None

        async with async_session_maker() as own:
            picture = await own.get(Image, found[0].id)

            if picture is None or picture.deleted_at is not None:
                return None

            return harness.Reused(
                id=picture.id,
                url=cloudinary.delivery_url(picture.path),
                width=picture.width,
                height=picture.height,
                prompt=picture.prompt,
            )

    return look


def _remembered_as(component: Component) -> str:
    """What a block is remembered as: what it is called, and what it was asked for.

    The brief is in it on purpose — it is the sentence a future brief will be
    compared with, and a block named "Proof sheet" does not say "hero" anywhere.
    """
    return f"{component.title}. {component.description}\n\n{component.delivery_prompt}"


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
    step the failure happened in — and a refusal or a rejection, which closes its
    own step before stopping the run, leaves no step failed at all: the work was
    done, and it is the task that is over.
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
