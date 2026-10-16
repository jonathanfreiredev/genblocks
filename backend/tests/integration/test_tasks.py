import uuid

import pytest

from app.pagination import ListParams
from app.tasks.models import Task, TaskStep
from app.tasks.service import get_task, list_tasks
from app.users.models import User

pytestmark = pytest.mark.anyio


async def test_a_task_keeps_its_steps_in_order(db_session):
    task = Task(
        brief="A pricing page",
        steps=[TaskStep(index=0, name="spec"), TaskStep(index=1, name="harness")],
    )
    db_session.add(task)
    await db_session.commit()

    loaded = await get_task(db_session, task_id=task.id)

    assert loaded is not None
    assert [step.name for step in loaded.steps] == ["spec", "harness"]


async def test_tasks_are_scoped_to_their_owner(db_session):
    owner = User(supabase_user_id=uuid.uuid4(), email="owner@example.com")
    other = User(supabase_user_id=uuid.uuid4(), email="other@example.com")
    db_session.add_all([owner, other])
    await db_session.commit()

    db_session.add_all(
        [
            Task(brief="mine", created_by=owner.id),
            Task(brief="theirs", created_by=other.id),
        ]
    )
    await db_session.commit()

    tasks, total = await list_tasks(db_session, params=ListParams(), created_by=owner.id)

    assert total == 1
    assert tasks[0].brief == "mine"


async def test_an_unknown_task_is_not_found(db_session):
    assert await get_task(db_session, task_id=uuid.uuid4()) is None
