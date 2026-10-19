"""The task runner, driven the way a worker drives it.

What a run leaves behind *is* the product's claim: a checklist that says what
happened, an attempt that keeps its own scores, a block that only exists because
the judge cleared it, and the pictures it asked for filed in the library. These
tests read those rows back from the database rather than from the objects the run
was holding.

What is faked here is everything that leaves the process — the agent, the sandbox,
the cloud, the image provider — and the model calls. What is real is the runner,
the gate, the thresholds it applies and the rows it writes.
"""

import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.components.models import Component, ComponentAsset
from app.db.models import utcnow
from app.generations.models import Generation, Verdict
from app.harness import agent, cloudinary, sandbox
from app.harness.agent import Built, Placed
from app.harness.images import Generated
from app.harness.schemas import FATAL_CHECKS, SandboxCheck, SandboxFile, SandboxResult
from app.images.models import Image
from app.judge import scoring as judging
from app.judge.rubrics import COMPONENTS, IMAGES
from app.judge.schemas import DimensionScore, JudgeAnswer, Judged
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
CATEGORY = "photography"

# What the harness writes, in a test: a project of two files, and the same two
# every time.
CODE = "export default function Block() {\n  return <section>Pricing</section>;\n}\n"
PART = "export default function Rule() { return <hr />; }\n"
ENTRY = "src/Block.tsx"
PROJECT = {ENTRY: CODE, "src/parts/Rule.tsx": PART}

# What the sandbox finds on a run that went well. One entry per check it makes,
# in the order it makes them.
FINDINGS = (
    SandboxCheck(name="imports", ok=True),
    SandboxCheck(name="typecheck", ok=True),
    SandboxCheck(name="lint", ok=True),
    SandboxCheck(name="build", ok=True),
    SandboxCheck(name="render", ok=True),
    SandboxCheck(name="layout:desktop", ok=True),
    SandboxCheck(name="layout:tablet", ok=True),
    SandboxCheck(name="layout:phone", ok=True),
    SandboxCheck(name="accessibility", ok=True),
)

# What the sandbox read out of the project: the install line the block declares.
DEPENDENCIES = {"motion": "^13.0.0", "react": "^19.2.4"}

PNG = b"\x89PNG\r\n\x1a\n"
PICTURE = b"\xff\xd8\xff\xe0jpeg-bytes"

# What the fake judge says, and what the thresholds it is read against are. The
# bars are pinned in the fixture rather than read from settings: recalibrating the
# shipped ones must not move a test, and what the thresholds *do* is tested where
# they live.
THRESHOLDS = {
    "render": 80,
    "accessibility": 75,
    "visual": 70,
    "copy": 70,
    "compliance": 80,
    "prompt_fit": 70,
}

# Above every one of them.
GOOD = {"render": 91, "accessibility": 89, "visual": 84, "copy": 86, "compliance": 93}
# Misses the copy bar, and misses nothing else.
WEAK = {**GOOD, "copy": 41}
# What an image is scored on, by its own shorter rubric.
PICTURE_SCORES = {"visual": 88, "prompt_fit": 91, "compliance": 97}

# How long a test waits on the worker before calling it stuck. Generous: the
# worker polls every hundredth of a second and the run itself never leaves the
# process, so anything near this is a real hang rather than a slow machine.
WAIT_SECONDS = 10.0


def findings(*failing: str) -> SandboxResult:
    """What the sandbox finds, with the named checks failed.

    The render comes back only when something rendered: a run that failed a fatal
    check never got as far as a page, and the fake mirrors that rather than
    handing back a picture the real sandbox would not have taken.
    """
    refused = set(failing)

    return SandboxResult(
        checks=[
            SandboxCheck(
                name=check.name,
                ok=check.name not in refused,
                detail=f"{check.name} did not pass" if check.name in refused else None,
            )
            for check in FINDINGS
        ],
        dependencies=dict(DEPENDENCIES),
        screenshot=None if refused & set(FATAL_CHECKS) else PNG,
    )


def picture(slot: str = "hero", category: str = CATEGORY) -> Placed:
    """One picture the harness asked the library for."""
    return Placed(
        slot=slot,
        category=category,
        url="https://cdn.test/genblocks/images/abc123",
        width=1024,
        height=768,
        image=Generated(
            prompt="A wide photograph of an empty road at dawn",
            path="genblocks/images/abc123",
            url="https://cdn.test/genblocks/images/abc123",
            width=1024,
            height=768,
            media_type="image/jpeg",
            data=PICTURE,
        ),
    )


class Harness:
    """What the runner asked the harness for, and what it was answered.

    A real run talks to a model, a container and two clouds. A test that did any of
    those would be testing somebody else's uptime and this machine's network. What
    is real here is everything the runner does with the answers.
    """

    def __init__(self) -> None:
        self.asked: list[dict] = []
        self.library = None
        self.checked: list[list[SandboxFile]] = []
        self.uploaded: list[str] = []
        self.answer = findings()
        # A test that needs the sandbox to answer differently on a later call
        # writes the whole script; its last answer is repeated after that.
        self.script: list[SandboxResult] = []
        self.built = Built(files=dict(PROJECT), images=[], iterations=3, skills="1a2b3c4d")

    def fails(self, *names: str) -> None:
        """Make the named checks fail, the way the sandbox would report it."""
        self.answer = findings(*names)

    def unrendered(self) -> None:
        """A run that never got as far as a page, so there is nothing to keep."""
        self.answer = SandboxResult(checks=list(FINDINGS), dependencies=dict(DEPENDENCIES))

    def next_answer(self) -> SandboxResult:
        """The answer for the call being made, from the script or the default."""
        if not self.script:
            return self.answer

        return self.script[min(len(self.checked) - 1, len(self.script) - 1)]


class Judge:
    """What the judge was shown, and what it decided to say.

    A real one sends the project, the sandbox's report and a render to a vision
    model. The messages are somebody else's uptime; what is real here is what the
    runner does with the answer, so the fake answers through the same
    ``app.judge.scoring.read`` the model's answer goes through — thresholds,
    verdict and rubric version included.
    """

    def __init__(self) -> None:
        self.shown: list[tuple[str, dict[str, str]]] = []
        self.pictures: list[str] = []
        self.script: list[dict[str, int]] = [GOOD]

    def _answer(self, said: dict[str, int]) -> JudgeAnswer:
        return JudgeAnswer(
            dimensions={
                name: DimensionScore(score=score, note=f"{name} earned this")
                for name, score in said.items()
            },
            summary="What the judge said in full.",
        )

    async def score_component(
        self, *, brief: str, files: dict[str, str], found: SandboxResult
    ) -> Judged:
        self.shown.append((brief, files))
        said = self.script[min(len(self.shown) - 1, len(self.script) - 1)]

        return judging.read(self._answer(said), COMPONENTS)

    async def score_image(
        self, *, prompt: str, image: bytes, width: int, height: int, media_type: str
    ) -> Judged:
        assert image == PICTURE
        self.pictures.append(prompt)

        return judging.read(self._answer(PICTURE_SCORES), IMAGES)


@pytest.fixture
def harness(monkeypatch) -> Harness:
    """The harness, the sandbox and the cloud, answered without leaving the process."""
    harness = Harness()

    async def build(
        *,
        brief: str,
        category: str,
        image_categories: list[str] | None = None,
        library=None,
        model=None,
    ) -> Built:
        harness.asked.append(
            {"brief": brief, "category": category, "image_categories": image_categories}
        )
        harness.library = library

        return harness.built

    async def check(files: list[SandboxFile]) -> SandboxResult:
        harness.checked.append(files)

        return harness.next_answer()

    async def store(data: bytes, *, name: str, media_type: str = "image/png", client=None) -> str:
        harness.uploaded.append(name)

        return name

    monkeypatch.setattr(agent, "build", build)
    monkeypatch.setattr(sandbox, "check", check)
    monkeypatch.setattr(cloudinary, "store", store)

    return harness


@pytest.fixture
def judge(monkeypatch) -> Judge:
    """The judge, answering without leaving the process."""
    judge = Judge()
    monkeypatch.setattr(settings, "rubric_thresholds", dict(THRESHOLDS))
    monkeypatch.setattr(judging, "score_component", judge.score_component)
    monkeypatch.setattr(judging, "score_image", judge.score_image)

    return judge


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


async def _attempts(session: AsyncSession, task_id: uuid.UUID) -> list[Generation]:
    """The attempts of a task, oldest first, read back from the table."""
    found = await session.scalars(
        select(Generation).where(Generation.task_id == task_id).order_by(Generation.attempt_no)
    )
    return list(found)


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


async def test_a_queued_task_runs_towards_a_published_block(runner_session, harness, judge):
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

    # Four steps, every one of them closed, and the harness's own numbers on the
    # step that did the work.
    assert [step.name for step in ran.steps] == list(runner.STEP_NAMES)
    assert [step.status for step in ran.steps] == [StepStatus.SUCCEEDED] * len(runner.STEP_NAMES)
    assert ran.steps[0].detail == {"category": canned.CATEGORY_SLUG}
    assert ran.steps[1].detail == {
        "checks": "9/9",
        "files": 2,
        "iterations": 3,
        "skills": "1a2b3c4d",
    }
    # The judge's line carries the dimension that decided it, not a mean: a mean
    # can look respectable on an attempt that failed one (see the ledger).
    assert ran.steps[2].detail == {"weakest": "visual 84"}
    assert ran.steps[3].detail == {"slug": slug, "files": 2, "pictures": 0}

    # The harness was asked for this brief and this type, the project went to the
    # sandbox file by file, and the judge was shown the whole of it.
    assert harness.asked == [
        {"brief": BRIEF, "category": canned.CATEGORY_SLUG, "image_categories": []}
    ]
    assert sorted(one.path for one in harness.checked[0]) == ["src/Block.tsx", "src/parts/Rule.tsx"]
    assert judge.shown == [(BRIEF, PROJECT)]

    attempts = await _attempts(runner_session, task_id)
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt.attempt_no == 1
    assert attempt.verdict == Verdict.PUBLISHED
    # The project, and which file of it is the block: the text is in the project
    # once, and the entry only names it.
    assert attempt.entry == ENTRY
    assert attempt.files == PROJECT
    assert attempt.model == settings.llm_model
    assert attempt.scores == GOOD
    assert attempt.rubric_version == COMPONENTS.version

    # What the sandbox found is kept on the attempt, and the render is uploaded
    # under the tree the cloudinary module owns.
    assert attempt.screenshot_path == cloudinary.screenshot_id(task_id, 1)
    assert harness.uploaded == [cloudinary.screenshot_id(task_id, 1)]
    assert attempt.checks is not None
    assert attempt.checks["blocked"] is False
    assert (attempt.checks["passed"], attempt.checks["total"]) == (9, 9)

    component = await runner_session.get(Component, ran.component_id)
    assert component is not None
    assert component.slug == slug
    assert component.category_id == category_id
    assert component.entry == ENTRY
    assert component.files == PROJECT
    # The install line, read from the project by the sandbox rather than declared
    # by the model that wrote it.
    assert component.dependencies == DEPENDENCIES
    assert component.delivery_prompt == BRIEF
    assert component.license == "MIT"
    assert component.created_by == owner_id
    assert component.winning_generation_id == attempt.id
    assert attempt.component_id == component.id

    assert await runner.claim_next_task() is None


async def test_a_block_under_the_bar_is_kept_as_an_attempt_and_not_published(
    runner_session, harness, judge
):
    """The judge is a gate: the block is readable, and the library does not have it."""
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id
    judge.script = [WEAK]

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    failed = await get_task(runner_session, task_id=task_id)
    assert failed is not None
    assert failed.status == TaskStatus.FAILED
    assert failed.component_id is None
    # The reason travels with the task: which dimension, by how much, and why.
    assert "copy 41, below 70" in (failed.error or "")
    assert "copy earned this" in (failed.error or "")
    assert "What the judge said in full." in (failed.error or "")

    # Every step that ran says so, and publishing never happened.
    assert [step.status for step in failed.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.SUCCEEDED,
        StepStatus.SUCCEEDED,
        StepStatus.PENDING,
    ]
    assert failed.steps[2].detail == {"weakest": "copy 41", "below": "copy"}

    # The attempt survives, with everything it is: a reader can see what was built
    # and what it was told about it.
    attempt = (await _attempts(runner_session, task_id))[0]
    assert attempt.verdict == Verdict.REJECTED
    assert attempt.scores == WEAK
    assert attempt.rubric_version == COMPONENTS.version
    assert attempt.files == PROJECT
    assert attempt.component_id is None

    assert await runner_session.scalar(select(Component)) is None


async def test_a_block_the_sandbox_refuses_is_kept_and_nobody_judges_it(
    runner_session, harness, judge
):
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
    assert "typecheck did not pass" in (failed.error or "")

    # The judge is not asked about something the sandbox would not build, and the
    # step that ran is closed with the checks it found.
    assert judge.shown == []
    assert failed.steps[1].detail["checks"] == "8/9"
    assert failed.steps[2].status == StepStatus.PENDING

    attempt = (await _attempts(runner_session, task_id))[0]
    assert attempt.verdict == Verdict.REJECTED
    assert attempt.scores is None
    assert attempt.screenshot_path is None
    assert attempt.checks is not None
    assert attempt.checks["blocked"] is True
    assert harness.uploaded == []

    assert await runner_session.scalar(select(Component)) is None


async def test_the_pictures_a_block_asks_for_are_filed_and_linked(runner_session, harness, judge):
    """A picture is a library artifact of its own, judged as it enters."""
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    await create_category(runner_session, slug=CATEGORY, kind="image")
    owner = await _owner(runner_session)
    owner_id = owner.id
    task = await _queued(runner_session, owner)
    task_id = task.id
    harness.built = Built(
        files=dict(PROJECT),
        images=[picture()],
        iterations=4,
        skills="1a2b3c4d",
    )

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    done = await get_task(runner_session, task_id=task_id)
    assert done is not None
    assert done.status == TaskStatus.SUCCEEDED

    # The taxonomy was handed to the harness rather than invented by it.
    assert harness.asked[0]["image_categories"] == [CATEGORY]

    image = await runner_session.scalar(select(Image))
    assert image is not None
    assert image.path == "genblocks/images/abc123"
    assert image.width == 1024
    assert image.height == 768
    assert image.model == settings.image_model
    assert image.created_by == owner_id
    # Scored on entry, by the shorter rubric, and the judge was given the bytes.
    assert image.scores == PICTURE_SCORES
    assert image.rubric_version == IMAGES.version
    assert judge.pictures == ["A wide photograph of an empty road at dawn"]

    # And linked to the block in its slot, which is what a visitor needs to know
    # which assets came with the code.
    asset = await runner_session.scalar(select(ComponentAsset))
    assert asset is not None
    assert asset.image_id == image.id
    assert asset.slot == "hero"
    assert asset.component_id == done.component_id
    assert done.steps[3].detail["pictures"] == 1


async def test_a_picture_asked_for_by_a_block_that_is_not_published_stays_in_the_library(
    runner_session, harness, judge
):
    await create_category(runner_session, slug=canned.CATEGORY_SLUG)
    await create_category(runner_session, slug=CATEGORY, kind="image")
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner)
    task_id = task.id
    harness.built = Built(files=dict(PROJECT), images=[picture()], iterations=4, skills="1a2b3c4d")
    judge.script = [WEAK]

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    failed = await get_task(runner_session, task_id=task_id)
    assert failed is not None
    assert failed.status == TaskStatus.FAILED

    # The block was refused and the picture is still the library's: it is stock,
    # and a later run can reuse it instead of generating another (Fase 10).
    assert await runner_session.scalar(select(Image)) is not None
    assert await runner_session.scalar(select(ComponentAsset)) is None


async def test_findings_that_are_not_fatal_are_evidence_not_a_gate(runner_session, harness, judge):
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
    assert done.steps[1].detail["checks"] == "7/9"

    attempt = (await _attempts(runner_session, task_id))[0]
    assert attempt.checks is not None
    assert attempt.checks["blocked"] is False
    assert [check["name"] for check in attempt.checks["checks"] if not check["ok"]] == [
        "layout:phone",
        "accessibility",
    ]


async def test_a_run_with_no_render_is_still_judged_and_publishes_without_a_photo(
    runner_session, harness, judge
):
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
    assert judge.shown == [(BRIEF, PROJECT)]

    attempt = (await _attempts(runner_session, task_id))[0]
    assert attempt.screenshot_path is None
    assert attempt.scores == GOOD
    assert harness.uploaded == []


async def test_a_harness_that_writes_nothing_fails_the_task(runner_session, harness, monkeypatch):
    async def wrote_nothing(
        *, brief: str, category: str, image_categories=None, library=None, model=None
    ) -> Built:
        raise agent.NothingWritten(
            "The harness finished without writing anything into the project."
        )

    monkeypatch.setattr(agent, "build", wrote_nothing)

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
    assert "without writing anything" in (failed.error or "")
    # The step that was open is the one that failed, and no attempt was written.
    assert [step.status for step in failed.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.FAILED,
        StepStatus.PENDING,
        StepStatus.PENDING,
    ]
    assert await runner_session.scalar(select(Generation)) is None


async def test_a_sandbox_that_never_answers_fails_the_task_with_its_words(
    runner_session, harness, judge, monkeypatch
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

    assert [step.status for step in failed.steps] == [
        StepStatus.SUCCEEDED,
        StepStatus.FAILED,
        StepStatus.PENDING,
        StepStatus.PENDING,
    ]
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


async def test_the_worker_drains_the_queue_and_stops(runner_session, harness, judge):
    """The worker, end to end: a queued brief becomes a published block."""
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
