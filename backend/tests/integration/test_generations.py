import pytest
from sqlalchemy.exc import IntegrityError

from app.components.models import Component
from app.generations.models import Generation
from app.generations.service import list_generations
from app.tasks.models import Task
from tests.helpers import create_category

pytestmark = pytest.mark.anyio


async def _task(session) -> Task:
    task = Task(brief="A pricing page")
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def test_attempts_belong_to_the_task_before_any_component_exists(db_session):
    task = await _task(db_session)
    db_session.add_all(
        [
            Generation(task_id=task.id, attempt_no=1, code="a"),
            Generation(task_id=task.id, attempt_no=2, code="b"),
        ]
    )
    await db_session.commit()

    attempts = await list_generations(db_session, task_id=task.id)

    assert [attempt.attempt_no for attempt in attempts] == [1, 2]
    assert all(attempt.component_id is None for attempt in attempts)


async def test_one_attempt_number_per_task(db_session):
    task = await _task(db_session)
    db_session.add(Generation(task_id=task.id, attempt_no=1, code="a"))
    await db_session.commit()

    db_session.add(Generation(task_id=task.id, attempt_no=1, code="b"))

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_an_attempt_can_exist_without_a_task(db_session):
    """Seeding plants components with their attempts and no task behind them."""
    generation = Generation(attempt_no=1, code="a")
    db_session.add(generation)
    await db_session.commit()

    assert generation.task_id is None


async def test_the_component_gathers_the_whole_history_at_commit(db_session):
    category = await create_category(db_session, slug="hero")
    task = await _task(db_session)
    attempts = [
        Generation(task_id=task.id, attempt_no=1, code="a"),
        Generation(task_id=task.id, attempt_no=2, code="b"),
    ]
    db_session.add_all(attempts)
    await db_session.commit()

    component = Component(
        slug="hero-1",
        title="Hero",
        description="A hero",
        category_id=category.id,
        code="b",
        delivery_prompt="Build a hero",
    )
    db_session.add(component)
    await db_session.commit()

    # What commit will do: stamp the component onto every attempt of the task,
    # and point the component at the winner.
    for attempt in attempts:
        attempt.component_id = component.id
    component.winning_generation_id = attempts[1].id
    await db_session.commit()

    history = await list_generations(db_session, component_id=component.id)

    assert [attempt.attempt_no for attempt in history] == [1, 2]
    assert component.winning_generation_id == attempts[1].id
