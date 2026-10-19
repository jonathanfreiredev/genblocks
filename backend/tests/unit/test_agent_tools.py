"""The tools one conversation reaches, and the briefs they will not take.

The tools are built for a caller and their names are the ones the MCP door
publishes, so this is where the two doors are held against each other.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.agent.schemas import Suggestions
from app.agent.tools import build_tools
from app.tasks.schemas import BRIEF_MAX_LENGTH, BRIEF_MIN_LENGTH
from app.users.models import User

pytestmark = pytest.mark.anyio


def caller() -> User:
    """The user a conversation is being held for, as the endpoint resolves it."""
    return User(id=uuid.uuid4(), supabase_user_id=uuid.uuid4(), email="maker@example.com")


def _tool(name: str, queued: list) -> object:
    return next(
        tool
        for tool in build_tools(caller=caller(), queued=queued, suggested=Suggestions())
        if tool.name == name
    )


def test_the_conversation_reaches_the_published_tools_by_name():
    tools = build_tools(caller=caller(), queued=[], suggested=Suggestions())

    assert [tool.name for tool in tools] == ["search_components", "find_images", "create_component"]
    assert all(tool.description for tool in tools)


def test_the_queue_takes_the_same_briefs_as_the_other_two_doors():
    schema = _tool("create_component", []).args_schema.model_json_schema()
    brief = schema["properties"]["brief"]

    assert brief["minLength"] == BRIEF_MIN_LENGTH
    assert brief["maxLength"] == BRIEF_MAX_LENGTH
    assert schema["required"] == ["brief"]


def test_a_search_names_the_thing_it_searches_for():
    schema = _tool("search_components", []).args_schema.model_json_schema()

    assert schema["required"] == ["query"]


async def test_a_brief_too_short_to_be_one_never_reaches_the_queue():
    queued: list = []

    with pytest.raises(ValidationError):
        await _tool("create_component", queued).ainvoke({"brief": "hero"})

    assert queued == []


async def test_a_brief_the_registry_already_has_is_not_queued(monkeypatch):
    """The guard refuses, and the answer says what it found instead."""
    from types import SimpleNamespace

    from app.agent.schemas import Suggestions
    from app.components import service as components_service
    from app.tasks import service as tasks_service

    found = SimpleNamespace(
        id=uuid.uuid4(),
        slug="tiered-pricing",
        title="Tiered pricing",
        description="Three plans in a ruled table",
    )
    suggested = Suggestions()

    async def already_built(session, *, brief):
        return (found, 0.42)

    async def queued_nothing(*args, **kwargs):
        raise AssertionError("a duplicate must not reach the queue")

    monkeypatch.setattr(components_service, "already_built", already_built)
    monkeypatch.setattr(tasks_service, "create_task", queued_nothing)

    tool = next(
        one
        for one in build_tools(caller=caller(), queued=[], suggested=suggested)
        if one.name == "create_component"
    )
    answer = await tool.ainvoke({"brief": "A pricing table with three tiers"})

    assert answer["queued"] is False
    assert answer["already"]["slug"] == "tiered-pricing"
    assert [one.id for one in suggested.items] == [found.id]
