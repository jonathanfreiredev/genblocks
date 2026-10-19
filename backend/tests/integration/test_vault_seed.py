"""The development dataset: idempotent, and consistent with itself.

The seed is run the way the CLI runs it — ``seed_categories`` first, then
``seed_vault`` — so the tests exercise the same code path a person gets from
``python -m app.seed.vault``.
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.categories.seed import seed_categories
from app.components.models import Component
from app.generations.models import Generation
from app.images.models import Image
from app.seed import vault
from app.tasks.models import Task
from app.tasks.service import get_task
from app.users.models import User

pytestmark = pytest.mark.anyio


async def _count(session, model) -> int:
    return await session.scalar(select(func.count()).select_from(model))


async def _planted_counts(session) -> tuple[int, int, int, int]:
    return (
        await _count(session, Component),
        await _count(session, Image),
        await _count(session, Task),
        await _count(session, Generation),
    )


async def test_the_seed_is_idempotent(db_session):
    await seed_categories(db_session)

    first = await vault.seed_vault(db_session)
    counts = await _planted_counts(db_session)
    component_ids = set(await db_session.scalars(select(Component.id)))

    second = await vault.seed_vault(db_session)

    assert first == second
    assert counts == (6, 6, 2, 13)
    assert await _planted_counts(db_session) == counts
    assert set(await db_session.scalars(select(Component.id))) == component_ids


async def test_a_seeded_block_points_at_its_own_published_attempt(db_session):
    await seed_categories(db_session)
    await vault.seed_vault(db_session)

    component = await db_session.scalar(select(Component).where(Component.slug == "tiered-pricing"))
    winner = await db_session.get(Generation, component.winning_generation_id)

    assert winner is not None
    assert winner.component_id == component.id
    assert winner.attempt_no == 2
    assert winner.verdict == "published"
    # The block is the project that run produced, and the attempt says which file
    # of it the block is.
    assert winner.entry == component.entry
    assert winner.files == component.files


async def test_every_seeded_block_keeps_two_attempts(db_session):
    await seed_categories(db_session)
    await vault.seed_vault(db_session)

    component_ids = list(await db_session.scalars(select(Component.id)))
    assert len(component_ids) == 6

    for component_id in component_ids:
        attempts = list(
            await db_session.scalars(
                select(Generation)
                .where(Generation.component_id == component_id)
                .order_by(Generation.attempt_no)
            )
        )
        assert [attempt.verdict for attempt in attempts] == ["rejected", "published"]
        # A seeded attempt has no task behind it, which is the case the schema
        # explicitly allows.
        assert all(attempt.task_id is None for attempt in attempts)


async def test_seeded_steps_read_in_index_order(db_session):
    await seed_categories(db_session)
    await vault.seed_vault(db_session)
    # Expire first, so the order asserted below comes from the table and not
    # from the collection the seed built in memory.
    db_session.expire_all()

    for spec in vault.TASKS:
        task = await db_session.scalar(select(Task).where(Task.brief == spec.brief))
        assert task is not None

        loaded = await get_task(db_session, task_id=task.id)

        assert loaded is not None
        assert [step.index for step in loaded.steps] == list(range(len(spec.steps)))


async def test_the_owner_flag_attaches_both_tasks(db_session):
    await seed_categories(db_session)
    owner = User(supabase_user_id=uuid.uuid4(), email="owner@example.com")
    db_session.add(owner)
    await db_session.commit()

    summary = await vault.seed_vault(db_session, owner_email="owner@example.com")

    assert summary.owner_email == "owner@example.com"
    assert summary.tasks == 2
    assert list(await db_session.scalars(select(Task.created_by))) == [owner.id, owner.id]


async def test_tasks_are_unowned_without_the_flag(db_session):
    await seed_categories(db_session)

    summary = await vault.seed_vault(db_session)

    assert summary.owner_email is None
    assert list(await db_session.scalars(select(Task.created_by))) == [None, None]


async def test_an_unknown_owner_email_is_a_clear_error(db_session):
    await seed_categories(db_session)

    with pytest.raises(vault.SeedError) as error:
        await vault.seed_vault(db_session, owner_email="nobody@example.com")

    assert "nobody@example.com" in str(error.value)
    # Nothing is planted when the owner cannot be resolved.
    assert await _count(db_session, Task) == 0


async def test_the_seed_refuses_to_run_without_the_taxonomy(db_session):
    with pytest.raises(vault.SeedError) as error:
        await vault.seed_vault(db_session)

    assert "python -m app.categories.seed" in str(error.value)
    assert await _count(db_session, Component) == 0


async def test_the_owner_flag_is_optional():
    assert vault._parse_args([]).owner is None
    assert vault._parse_args(["--owner", "owner@example.com"]).owner == "owner@example.com"
