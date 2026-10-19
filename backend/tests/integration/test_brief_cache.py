"""A brief the registry has answered is answered again for free.

The cache is exact: same words, same block. Similarity is the guard's job, and it
gives the person a choice; this gives them back the block and spends nothing.
"""

import uuid

import pytest
from sqlalchemy import select

from app.briefs import service as briefs
from app.components.models import Component
from app.db.models import utcnow
from app.moderation import service as moderation
from app.settings import settings
from app.tasks import service
from app.tasks.models import Task, TaskStatus, TaskStep
from app.users.models import User
from tests.helpers import create_category, create_component

pytestmark = pytest.mark.anyio

BRIEF = "A pricing page for a developer tool"


async def _owner(session, email: str = "maker@example.com") -> User:
    user = User(supabase_user_id=uuid.uuid4(), email=email)
    session.add(user)
    await session.commit()

    return user


async def _block(session, slug: str = "tiered-pricing") -> Component:
    category = await create_category(session, slug=f"{slug}-type")
    return await create_component(session, category_id=category.id, slug=slug)


def test_the_key_is_the_words_and_not_the_typing():
    assert briefs.key_for("  A Pricing  Page ") == "a pricing page"
    # Word choice is meaning: that is the guard's question, not the cache's.
    assert briefs.key_for("a pricing page") != briefs.key_for("a price list")


async def test_a_brief_remembers_the_block_it_became(db_session):
    block = await _block(db_session)

    await briefs.remember(db_session, brief=BRIEF, component_id=block.id)
    await db_session.commit()

    found = await briefs.find(db_session, brief="  a PRICING page for a developer tool ")
    assert found is not None
    assert found.id == block.id


async def test_a_block_that_left_the_registry_is_a_miss(db_session):
    block = await _block(db_session)
    await briefs.remember(db_session, brief=BRIEF, component_id=block.id)
    block.deleted_at = utcnow()
    await db_session.commit()

    assert await briefs.find(db_session, brief=BRIEF) is None


async def test_the_same_brief_built_twice_keeps_the_newer_answer(db_session):
    first = await _block(db_session, slug="tiered-pricing")
    second = await _block(db_session, slug="pricing-two")

    await briefs.remember(db_session, brief=BRIEF, component_id=first.id)
    await briefs.remember(db_session, brief=BRIEF, component_id=second.id)
    await db_session.commit()

    found = await briefs.find(db_session, brief=BRIEF)
    assert found is not None
    assert found.id == second.id
    assert await db_session.scalar(select(Task)) is None


async def test_an_answered_brief_is_a_finished_task_and_asks_no_model(db_session, monkeypatch):
    block = await _block(db_session)
    await briefs.remember(db_session, brief=BRIEF, component_id=block.id)
    await db_session.commit()
    owner = await _owner(db_session)

    async def never(text, *, client=None):
        raise AssertionError("a cached brief is not moderated again")

    monkeypatch.setattr(moderation, "refusal", never)

    task = await service.enqueue_task(db_session, brief=BRIEF, created_by=owner.id)

    assert task.cached is True
    assert task.status == TaskStatus.SUCCEEDED
    assert task.component_id == block.id
    assert task.finished_at is not None
    assert [step.name for step in task.steps] == [service.ANSWERED_STEP]
    assert task.steps[0].status == "succeeded"


async def test_a_cached_brief_does_not_spend_the_month(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    block = await _block(db_session)
    await briefs.remember(db_session, brief=BRIEF, component_id=block.id)
    await db_session.commit()
    owner = await _owner(db_session)
    await service.enqueue_task(db_session, brief="A different brief entirely", created_by=owner.id)

    # The month is spent, and the registry still answers what it already has.
    task = await service.enqueue_task(db_session, brief=BRIEF, created_by=owner.id)

    assert task.cached is True
    assert await db_session.scalar(select(TaskStep).where(TaskStep.task_id == task.id)) is not None


async def test_asking_for_a_fresh_one_skips_the_cache_and_is_paid_for(db_session, monkeypatch):
    block = await _block(db_session)
    await briefs.remember(db_session, brief=BRIEF, component_id=block.id)
    await db_session.commit()
    owner = await _owner(db_session)

    task = await service.enqueue_task(db_session, brief=BRIEF, created_by=owner.id, fresh=True)

    # "Build mine anyway" is a run, not a lookup: pending, unbuilt, and charged.
    assert task.cached is False
    assert task.status == TaskStatus.PENDING
    assert task.component_id is None
