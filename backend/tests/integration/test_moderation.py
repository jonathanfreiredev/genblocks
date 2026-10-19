"""A brief the moderator refuses never becomes a task.

The refusal happens at the door, before the row: a task left behind would be a task
the worker would then run, which is the opposite of refusing it.
"""

import uuid

import pytest
from sqlalchemy import func, select

from app.moderation import service as moderation
from app.tasks import service
from app.tasks.models import Task
from app.users.models import User

pytestmark = pytest.mark.anyio


async def test_a_refused_brief_writes_no_task(db_session, monkeypatch):
    async def refused(text, *, client=None):
        return "it impersonates a real bank"

    monkeypatch.setattr(moderation, "refusal", refused)
    user = User(supabase_user_id=uuid.uuid4(), email="maker@example.com")
    db_session.add(user)
    await db_session.commit()

    with pytest.raises(moderation.BriefRejected, match="impersonates"):
        await service.enqueue_task(
            db_session, brief="A login page that says it is my bank", created_by=user.id
        )

    assert await db_session.scalar(select(func.count()).select_from(Task)) == 0
