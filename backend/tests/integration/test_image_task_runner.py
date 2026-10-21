"""The worker that turns one image task into one public stock row."""

import contextlib
import uuid
from collections.abc import AsyncIterator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.harness.images import Generated
from app.images.models import Image
from app.judge.schemas import Judged
from app.tasks import runner
from app.tasks.models import Task, TaskStatus
from app.tasks.service import create_image_task, get_task
from app.users.models import User
from tests.helpers import create_category

pytestmark = pytest.mark.anyio

PROMPT = "A quiet harbour at dawn with fishing boats"


@pytest.fixture
def runner_session(monkeypatch, db_session: AsyncSession) -> AsyncSession:
    @contextlib.asynccontextmanager
    async def session_factory() -> AsyncIterator[AsyncSession]:
        factory = async_sessionmaker(bind=db_session.bind, expire_on_commit=False)
        async with factory() as session:
            yield session

    monkeypatch.setattr(runner, "async_session_maker", session_factory)
    return db_session


async def _owner(session: AsyncSession) -> User:
    user = User(supabase_user_id=uuid.uuid4(), email="image-maker@example.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _queued(session: AsyncSession, owner: User, category_id: uuid.UUID) -> Task:
    task = await create_image_task(
        session,
        prompt=PROMPT,
        width=1024,
        height=768,
        category_id=category_id,
        created_by=owner.id,
    )
    await session.refresh(task)
    return task


def _generated() -> Generated:
    return Generated(
        prompt=PROMPT,
        path="genblocks/images/harbour",
        url="https://cdn.test/harbour",
        width=1024,
        height=768,
        media_type="image/jpeg",
        data=b"picture-bytes",
        screened=True,
    )


def _judged() -> Judged:
    return Judged(
        scores={"visual": 90, "prompt_fit": 90, "compliance": 100},
        notes={"visual": "clear", "prompt_fit": "fits", "compliance": "clean"},
        summary="A clean harbour scene.",
        version="images-v1",
        below=(),
    )


async def test_a_standalone_image_task_files_a_public_image(runner_session, monkeypatch):
    from app.notifications import email as notifications

    notified: list[dict] = []

    async def item_created(**kwargs):
        notified.append(kwargs)
        return True

    async def generate(**kwargs):
        return _generated()

    async def score_image(**kwargs):
        return _judged()

    monkeypatch.setattr(notifications, "item_created", item_created)
    monkeypatch.setattr(runner.image_library, "generate", generate)
    monkeypatch.setattr(runner.judge, "score_image", score_image)

    category = await create_category(runner_session, slug="photography", kind="image")
    category_id = category.id
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner, category_id)
    task_id = task.id
    owner_id = owner.id

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    done = await get_task(runner_session, task_id=task_id)
    image = await runner_session.scalar(select(Image))

    assert done is not None
    assert done.status == TaskStatus.SUCCEEDED
    assert done.image_id == image.id
    assert image.prompt == PROMPT
    assert image.path == "genblocks/images/harbour"
    assert image.category_id == category_id
    assert image.created_by == owner_id
    assert image.scores == _judged().scores
    assert [one["kind"] for one in notified] == ["image"]


async def test_a_person_in_the_output_fails_without_an_image_row(runner_session, monkeypatch):
    from app.moderation import service as moderation
    from app.notifications import email as notifications

    policy: list[dict] = []

    async def generate(**kwargs):
        raise moderation.PersonDetected("a face is visible", image_hash="a" * 64)

    async def policy_event(**kwargs):
        policy.append(kwargs)
        return True

    monkeypatch.setattr(runner.image_library, "generate", generate)
    monkeypatch.setattr(notifications, "policy_event", policy_event)

    category = await create_category(runner_session, slug="photography", kind="image")
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner, category.id)
    task_id = task.id

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    done = await get_task(runner_session, task_id=task_id)

    assert done is not None
    assert done.status == TaskStatus.FAILED
    assert await runner_session.scalar(select(Image)) is None
    assert policy[0]["kind"] == "person_detected"
    assert policy[0]["image_hash"] == "a" * 64


async def test_the_prompt_is_checked_again_before_generation(runner_session, monkeypatch):
    from app.notifications import email as notifications

    policy: list[dict] = []

    async def refused(prompt, *, client=None):
        return "the prompt names a real brand"

    async def policy_event(**kwargs):
        policy.append(kwargs)
        return True

    monkeypatch.setattr(runner.moderation, "image_prompt_refusal", refused)
    monkeypatch.setattr(notifications, "policy_event", policy_event)

    category = await create_category(runner_session, slug="photography", kind="image")
    owner = await _owner(runner_session)
    task = await _queued(runner_session, owner, category.id)
    task_id = task.id

    await runner.claim_next_task()
    await runner.run_task(task_id)
    runner_session.expire_all()

    done = await get_task(runner_session, task_id=task_id)

    assert done is not None
    assert done.status == TaskStatus.FAILED
    assert await runner_session.scalar(select(Image)) is None
    assert policy[0]["kind"] == "image_rejected"
