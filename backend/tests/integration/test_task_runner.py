"""The task runner, driven the way a worker drives it.

What a run leaves behind *is* the product's claim: a checklist that says what
happened, an attempt that keeps its own scores, and a block that only exists
because both of the above went through. These tests read those rows back from
the database rather than from the objects the run was holding.
"""

import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.components.models import Component
from app.db.models import utcnow
from app.generations.models import Generation, Verdict
from app.harness import generator, sandbox, screenshots
from app.harness.schemas import SandboxCheck, SandboxFile, SandboxResult
from app.settings import settings
from app.tasks import canned, runner
from app.tasks.models import StepStatus, Task, TaskStatus, TaskStep
from app.tasks.service import (
    INTERRUPTED_ERROR,
    create_task,
    get_task,
    interrupt_orphaned_tasks,
)
from app.users.models import User
from tests.helpers import create_category

pytestmark = pytest.mark.anyio

BRIEF = "A pricing page for a developer tool"

# What the generator writes, in a test: one block, and the same one every time.
CODE = "export default function Block() {\n  return <section>Pricing</section>;\n}\n"

# What the sandbox finds on a run that went well. One entry per check it makes,
# in the order it makes them.
FINDINGS = (
    SandboxCheck(name="typecheck", ok=True),
    SandboxCheck(name="lint", ok=True),
    SandboxCheck(name="build", ok=True),
    SandboxCheck(name="render", ok=True),
    SandboxCheck(name="layout:desktop", ok=True),
    SandboxCheck(name="layout:tablet", ok=True),
    SandboxCheck(name="layout:phone", ok=True),
    SandboxCheck(name="accessibility", ok=True),
)

PNG = b"\x89PNG\r\n\x1a\n"

# How long a test waits on the worker before calling it stuck. Generous: the
# worker polls every hundredth of a second and the run itself never leaves the
# process, so anything near this is a real hang rather than a slow machine.
WAIT_SECONDS = 10.0


class Harness:
    """What the runner asked the harness for, and what it was answered.

    A real run writes with a model, builds in a container and uploads to a
    cloud. A test that did any of those would be testing somebody else's uptime
    and this machine's network. What is real here is everything the runner does
    with the answers.
    """

    def __init__(self) -> None:
        self.asked: list[tuple[str, str]] = []
        self.checked: list[list[SandboxFile]] = []
        self.uploaded: list[str] = []
        self.answer = SandboxResult(checks=list(FINDINGS), screenshot=PNG)

    def fails(self, *names: str) -> None:
        """Make the named checks fail, the way the sandbox would report it."""
        refused = set(names)
        self.answer = SandboxResult(
            checks=[
                SandboxCheck(
                    name=check.name,
                    ok=check.name not in refused,
                    detail=f"{check.name} did not pass" if check.name in refused else None,
                )
                for check in FINDINGS
            ],
            screenshot=self.answer.screenshot,
        )

    def unrendered(self) -> None:
        """A run that never got as far as a page, so there is nothing to keep."""
        self.answer = SandboxResult(checks=list(FINDINGS))


@pytest.fixture
def harness(monkeypatch) -> Harness:
    """The three ends of the harness, answered without leaving the process."""
    harness = Harness()

    async def write_component(*, brief: str, category: str) -> str:
        harness.asked.append((brief, category))
        return CODE

    async def check(files: list[SandboxFile]) -> SandboxResult:
        harness.checked.append(files)
        return harness.answer

    async def store(png: bytes, *, name: str) -> str:
        harness.uploaded.append(name)
        return name

    monkeypatch.setattr(generator, "write_component", write_component)
    monkeypatch.setattr(sandbox, "check", check)
    monkeypatch.setattr(screenshots, "store", store)
    return harness


@pytest.fixture
def runner_session(monkeypatch, db_session: AsyncSession) -> AsyncSession:
    """Point the runner at the test database, with a session of its own.

    Not the test's session: the runner commits its own work while the test reads
    the table, and one session cannot do both without the two tripping over each
    other.
    """

    @contextlib.asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        factory = async_sessionmaker(bind=db_session.bind, expire_on_commit=False)
        async with factory() as session:
            yield session

    monkeypatch.setattr(runner, "async_session_maker", session_factory)
    return db_session


async def _owner(session: AsyncSession, email: str = "maker@example.com") -> User:
    """A user row to own the task, which is what ``created_by`` demands."""
    user = User(supabase_user_id=uuid.uuid4(), email=email)
    session.add(user)
    await session.commit()
    return user


async def _queued(session: AsyncSession, owner: User, *, brief: str = BRIEF) -> Task:
    """Queue a task and return it with the columns the server filled in."""
    task = await create_task(session, brief=brief, created_by=owner.id)
    await session.refresh(task)
    return task


async def _wait_for(session: AsyncSession, task_id: uuid.UUID, status: str) -> None:
    """Wait until the task reads as ``status`` in the database.

    Every turn ends the read transaction: a session that keeps one open answers
    from the snapshot it started with and would never see the worker commit.
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + WAIT_SECONDS

    while True:
        await session.commit()
        current = await session.scalar(select(Task.status).where(Task.id == task_id))
        if current == status:
            return

        if loop.time() > deadline:
            raise AssertionError(f"The task never reached {status!r} (last: {current!r}).")

        await asyncio.sleep(0.02)


async def test_a_queued_task_runs_towards_a_published_block(runner_session, harness):
    category = await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    category_id = category.id
    owner = await _owner(runner_session)

    task = await _queued(runner_session, owner)
    task_id = task.id
    owner_id = owner.id
    assert task.status == TaskStatus.PENDING

    assert await runner.claim_next_task() == task_id

    await runner.run_task(task_id)
    # Read the run's work back from the table: what the test was holding is the
    # task as it was before the worker touched it.
    runner_session.expire_all()

    slug = runner.slug_for(title=canned.title_for(BRIEF), task_id=task_id)
    ran = await get_task(runner_session, task_id=task_id)
    assert ran is not None
    assert ran.status == TaskStatus.SUCCEEDED
    assert ran.error is None
    assert ran.finished_at is not None

    # The checklist is the one the plan describes, every step closed.
    assert [step.name for step in ran.steps] == list(runner.STEP_NAMES)
    assert [step.status for step in ran.steps] == [StepStatus.SUCCEEDED] * len(runner.STEP_NAMES)
    assert all(step.started_at and step.finished_at for step in ran.steps)
    assert ran.steps[0].detail == {"category": canned.CATEGORY_SLUG}
    assert ran.steps[1].detail == {"attempts": 1, "checks": "8/8"}
    assert ran.steps[3].detail == {"slug": slug}

    # The generator was asked for this brief and this type, and the sandbox was
    # handed the block at the path the scaffold imports.
    assert harness.asked == [(BRIEF, canned.CATEGORY_SLUG)]
    assert [sent.path for sent in harness.checked[0]] == [runner.BLOCK_PATH]
    assert harness.checked[0][0].content == CODE

    attempt = await runner_session.scalar(select(Generation).where(Generation.task_id == task_id))
    assert attempt is not None
    assert attempt.attempt_no == 1
    assert attempt.verdict == Verdict.PUBLISHED
    assert attempt.scores == canned.SCORES
    assert attempt.rubric_version == canned.VERSION

    # A model wrote this code and the attempt says which one; what the sandbox
    # found is kept on the attempt, and the render is uploaded under the tree the
    # screenshots module owns.
    assert attempt.code == CODE
    assert attempt.model == settings.llm_model
    assert attempt.screenshot_path == screenshots.public_id(task_id, 1)
    assert harness.uploaded == [screenshots.public_id(task_id, 1)]
    assert attempt.checks is not None
    assert attempt.checks["blocked"] is False
    assert (attempt.checks["passed"], attempt.checks["total"]) == (8, 8)
    assert [check["name"] for check in attempt.checks["checks"]] == [
        check.name for check in FINDINGS
    ]

    component = await runner_session.get(Component, ran.component_id)
    assert component is not None
    assert component.slug == slug
    assert component.category_id == category_id
    assert component.code == CODE
    assert component.delivery_prompt == BRIEF
    assert component.license == "MIT"
    assert component.created_by == owner_id
    assert component.winning_generation_id == attempt.id

    # The attempt points at the block it became, so the published item can still
    # show the history that produced it.
    assert attempt.component_id == component.id

    # Nothing is left queued behind it.
    assert await runner.claim_next_task() is None


async def test_code_the_sandbox_refuses_is_kept_as_an_attempt_and_fails_the_task(
    runner_session, harness
):
    """Code that does not typecheck is not a block, and it is still a record."""
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id
    harness.fails("typecheck")

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    failed = await get_task(runner_session, task_id=task_id)
    assert failed is not None
    assert failed.status == TaskStatus.FAILED
    assert failed.component_id is None
    assert "typecheck did not pass" in (failed.error or "")

    # The step that failed says so; the ones it never reached stay queued.
    assert [step.status for step in failed.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.FAILED,
        StepStatus.PENDING,
        StepStatus.PENDING,
    ]

    # The attempt survives the refusal, with the code and the reason on it.
    attempt = await runner_session.scalar(select(Generation).where(Generation.task_id == task_id))
    assert attempt is not None
    assert attempt.code == CODE
    assert attempt.verdict == Verdict.CANDIDATE
    assert attempt.component_id is None
    assert attempt.checks is not None
    assert attempt.checks["blocked"] is True

    assert await runner_session.scalar(select(Component)) is None


async def test_findings_that_are_not_fatal_are_evidence_not_a_gate(runner_session, harness):
    """A layout that breaks at 390px is worth knowing, and not worth refusing."""
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id
    harness.fails("layout:phone", "accessibility")

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    done = await get_task(runner_session, task_id=task_id)
    assert done is not None
    assert done.status == TaskStatus.SUCCEEDED
    assert done.steps[1].detail == {"attempts": 1, "checks": "6/8"}

    attempt = await runner_session.scalar(select(Generation).where(Generation.task_id == task_id))
    assert attempt is not None
    assert attempt.checks is not None
    assert attempt.checks["blocked"] is False
    assert [check["name"] for check in attempt.checks["checks"] if not check["ok"]] == [
        "layout:phone",
        "accessibility",
    ]


async def test_a_run_with_no_render_publishes_without_a_screenshot(runner_session, harness):
    """Nothing to photograph is not a failure: the attempt says the asset is not there."""
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id
    harness.unrendered()

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    done = await get_task(runner_session, task_id=task_id)
    assert done is not None
    assert done.status == TaskStatus.SUCCEEDED

    attempt = await runner_session.scalar(select(Generation).where(Generation.task_id == task_id))
    assert attempt is not None
    assert attempt.screenshot_path is None
    assert harness.uploaded == []


async def test_a_sandbox_that_never_answers_fails_the_task_with_its_words(
    runner_session, harness, monkeypatch
):
    async def refused(files: list[SandboxFile]) -> SandboxResult:
        raise sandbox.SandboxUnavailable("The sandbox did not answer within 900 seconds.")

    monkeypatch.setattr(sandbox, "check", refused)

    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    failed = await get_task(runner_session, task_id=task_id)
    assert failed is not None
    assert failed.status == TaskStatus.FAILED
    assert "within 900 seconds" in (failed.error or "")

    # No attempt: there is nothing to say about code nobody looked at.
    assert await runner_session.scalar(select(Generation)) is None


async def test_a_run_that_cannot_plan_fails_the_task_and_says_why(runner_session):
    """Without the taxonomy the spec has nothing to file the block under."""
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id
    await runner.claim_next_task()

    await runner.run_task(task_id)
    runner_session.expire_all()

    failed = await get_task(runner_session, task_id=task_id)
    assert failed is not None
    assert failed.status == TaskStatus.FAILED
    assert failed.component_id is None
    assert failed.finished_at is not None
    assert canned.CATEGORY_SLUG in (failed.error or "")

    # The step that failed says so; the ones it never reached stay queued.
    assert [step.status for step in failed.steps] == [
        StepStatus.FAILED,
        StepStatus.PENDING,
        StepStatus.PENDING,
        StepStatus.PENDING,
    ]

    # No block and no attempt: a run that planned nothing published nothing.
    assert await runner_session.scalar(select(Component)) is None
    assert await runner_session.scalar(select(Generation)) is None


async def test_the_claim_takes_the_oldest_task_first(runner_session):
    owner = await _owner(runner_session)
    older = await _queued(runner_session, owner, brief="The first brief")
    newer = await _queued(runner_session, owner, brief="The second brief")

    # Both were written in the same second, so the order is pinned here rather
    # than inherited from whenever the two rows happened to land.
    older.created_at = datetime(2020, 1, 1, tzinfo=UTC)
    newer.created_at = datetime(2021, 1, 1, tzinfo=UTC)
    await runner_session.commit()

    assert await runner.claim_next_task() == older.id
    assert await runner.claim_next_task() == newer.id
    assert await runner.claim_next_task() is None

    runner_session.expire_all()
    claimed = (await runner_session.scalars(select(Task).order_by(Task.created_at))).all()
    assert [task.status for task in claimed] == [TaskStatus.RUNNING, TaskStatus.RUNNING]


async def test_a_withdrawn_task_is_never_claimed(runner_session):
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner, brief="Withdrawn before it ran")
    task.deleted_at = utcnow()
    await runner_session.commit()

    assert await runner.claim_next_task() is None


async def test_a_restart_interrupts_the_task_it_was_running(runner_session):
    owner = await _owner(runner_session)
    running = await _queued(runner_session, owner, brief="Caught mid-flight")
    queued = await _queued(runner_session, owner, brief="Never started")
    running_id, queued_id = running.id, queued.id

    await runner.claim_next_task()
    # A step the crash caught in the open, which no worker is left to close.
    runner_session.add_all(
        [
            TaskStep(task_id=running_id, index=0, name="Retrieving references", status="succeeded"),
            TaskStep(task_id=running_id, index=1, name="Generating the block", status="running"),
        ]
    )
    await runner_session.commit()

    assert await interrupt_orphaned_tasks(runner_session) == 1
    runner_session.expire_all()

    stopped = await get_task(runner_session, task_id=running_id)
    assert stopped is not None
    assert stopped.status == TaskStatus.INTERRUPTED
    assert stopped.error == INTERRUPTED_ERROR
    assert stopped.finished_at is not None
    assert [step.status for step in stopped.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.FAILED,
    ]

    # The task nobody had claimed is left where it was: the reconciliation reads
    # the row, not the clock.
    still_queued = await get_task(runner_session, task_id=queued_id)
    assert still_queued is not None
    assert still_queued.status == TaskStatus.PENDING


async def test_a_restart_with_nothing_running_changes_nothing(runner_session):
    owner = await _owner(runner_session)
    await _queued(runner_session, owner, brief="Still waiting its turn")

    assert await interrupt_orphaned_tasks(runner_session) == 0


async def test_the_worker_drains_the_queue_and_stops(runner_session, harness):
    """The loop, end to end: a queued brief becomes a published block."""
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id

    stop = asyncio.Event()
    worker = asyncio.create_task(runner.run_worker(stop, poll_seconds=0.01))

    try:
        await _wait_for(runner_session, task_id, TaskStatus.SUCCEEDED)
    finally:
        stop.set()
        await worker

    runner_session.expire_all()
    drained = await get_task(runner_session, task_id=task_id)
    assert drained is not None
    assert drained.component_id is not None
