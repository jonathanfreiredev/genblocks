"""The bodies of the write tools, driven directly.

Same arrangement as ``test_mcp_read_tools.py``: the session factory and the
access token are swapped, which is what a successful call over HTTP ends up
doing. A write tool is not special — it queues work and returns; it never waits
on the pipeline.
"""

import contextlib
import uuid
from collections.abc import AsyncIterator

import pytest
from fastmcp.server.auth import AccessToken
from pydantic import ValidationError
from sqlalchemy import func, select

from app.mcp import tools
from app.mcp.server import mcp
from app.tasks.models import Task, TaskStatus
from app.tasks.schemas import TaskRead
from app.users.models import User

pytestmark = pytest.mark.anyio

# Published the moment they ship and never renamed. ``generate_image`` and
# ``vary_component`` are reserved (see PLAN.md) and not registered yet.
PUBLISHED_WRITE_TOOLS = {"plan_component", "create_component"}

BRIEF = "A pricing page for a developer tool, three tiers"


@pytest.fixture
def tool_session(monkeypatch, db_session):
    """Point the tools at the test session instead of the application's engine."""

    @contextlib.asynccontextmanager
    async def session_factory() -> AsyncIterator:
        yield db_session

    monkeypatch.setattr(tools, "async_session_maker", session_factory)
    return db_session


def sign_in(monkeypatch, *, subject: uuid.UUID, email: str = "agent@example.com") -> None:
    """Make the tools see a verified token for this subject."""
    monkeypatch.setattr(
        tools,
        "get_access_token",
        lambda: AccessToken(
            token="ignored",
            client_id="",
            scopes=[],
            claims={"sub": str(subject), "email": email},
        ),
    )


async def _caller_user(session, *, subject: uuid.UUID) -> User:
    return await session.scalar(select(User).where(User.supabase_user_id == subject))


async def test_the_published_write_tools_are_registered():
    listed = {tool.name for tool in await mcp.list_tools()}

    assert listed >= PUBLISHED_WRITE_TOOLS


async def test_plan_component_answers_without_queueing(tool_session, monkeypatch):
    subject = uuid.uuid4()
    sign_in(monkeypatch, subject=subject)

    plan = await tools.plan_component(brief=BRIEF)

    assert plan.status == "ready"
    assert plan.proposed_brief is None
    assert await tool_session.scalar(select(func.count()).select_from(Task)) == 0


async def test_create_component_queues_a_task_for_the_caller(tool_session, monkeypatch):
    subject = uuid.uuid4()
    sign_in(monkeypatch, subject=subject)

    task = await tools.create_component(brief=BRIEF)

    assert isinstance(task, TaskRead)
    assert task.status == TaskStatus.PENDING
    assert task.brief == BRIEF
    assert task.component_id is None

    # The task belongs to the token's user, never to an argument.
    me = await _caller_user(tool_session, subject=subject)
    queued = await tool_session.scalar(select(Task).where(Task.id == task.id))
    assert queued is not None
    assert queued.created_by == me.id


async def test_create_component_says_when_the_month_is_spent(tool_session, monkeypatch):
    from datetime import UTC, datetime

    from app.tasks import limits

    sign_in(monkeypatch, subject=uuid.uuid4())

    async def spent(session, *, user_id, now=None):
        raise limits.MonthlyQuotaReached(
            used=10, limit=10, reopens=datetime(2026, 11, 1, tzinfo=UTC)
        )

    monkeypatch.setattr(limits, "admitted", spent)

    # The third door answers in the same words as the other two: a tool error the
    # calling agent can read and repeat.
    with pytest.raises(ValueError, match="10 of your 10 blocks"):
        await tools.create_component(brief=BRIEF)


async def test_create_component_takes_the_same_briefs_as_the_api(tool_session, monkeypatch):
    """One brief, one set of rules: the tool and the endpoint share the type."""
    sign_in(monkeypatch, subject=uuid.uuid4())

    with pytest.raises(ValidationError):
        await tools.create_component(brief="hero")

    assert (await tools.list_tasks()).total == 0


async def test_create_component_leaves_the_task_for_get_task_to_find(tool_session, monkeypatch):
    sign_in(monkeypatch, subject=uuid.uuid4())

    queued = await tools.create_component(brief=BRIEF)
    found = await tools.get_task(task_id=queued.id)

    assert found.id == queued.id
    assert found.status == TaskStatus.PENDING
    assert found.steps == []
