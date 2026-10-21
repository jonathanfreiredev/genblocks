"""The tools one conversation reaches, and the briefs they will not take.

The domain tools keep the names the MCP door publishes, so this is where the two
doors are held against each other. The overview is the conversation's own read:
it answers what the registry holds without opening a second door.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.agent.schemas import Proposals, Suggestions
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

    assert [tool.name for tool in tools] == [
        "registry_overview",
        "search_components",
        "find_images",
        "plan_image",
        "generate_image",
        "plan_component",
        "create_component",
    ]
    assert all(tool.description for tool in tools)


def test_the_queue_takes_the_same_briefs_as_the_other_two_doors():
    schema = _tool("create_component", []).args_schema.model_json_schema()
    brief = schema["properties"]["brief"]

    assert brief["minLength"] == BRIEF_MIN_LENGTH
    assert brief["maxLength"] == BRIEF_MAX_LENGTH
    assert schema["required"] == ["brief"]


def test_the_overview_takes_no_arguments():
    schema = _tool("registry_overview", []).args_schema.model_json_schema()

    assert schema.get("required", []) == []


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


async def test_plan_component_offers_the_no_people_rewrite(monkeypatch):
    from app.components import planning

    async def needs_rewrite(brief):
        return planning.PlanDecision(
            status="needs_image_confirmation",
            brief=brief,
            reason="people are not allowed",
            proposed_brief="A pottery wheel with clay, no hands",
        )

    monkeypatch.setattr(planning, "plan", needs_rewrite)

    tool = _tool("plan_component", [])
    answer = await tool.ainvoke({"brief": "A hero with hands shaping clay"})

    assert answer["status"] == "needs_image_confirmation"
    assert answer["proposed_brief"] == "A pottery wheel with clay, no hands"


async def test_generate_image_prepares_an_image_proposal(monkeypatch):
    from app.agent.schemas import Proposals
    from app.images import planning as image_planning

    async def ready(session, *, prompt, width, height, category):
        return image_planning.ImagePlan(
            status="ready",
            prompt=prompt,
            width=width,
            height=height,
            category=category,
            category_id=uuid.uuid4(),
            reason="the prompt has no people",
            suggested_prompt=None,
        )

    monkeypatch.setattr(image_planning, "plan_image", ready)
    proposals = Proposals()
    tool = next(
        one
        for one in build_tools(
            caller=caller(),
            queued=[],
            suggested=Suggestions(),
            proposals=proposals,
        )
        if one.name == "generate_image"
    )

    answer = await tool.ainvoke(
        {
            "prompt": "A quiet harbour at dawn with fishing boats",
            "width": 1024,
            "height": 768,
            "category": "photography",
        }
    )

    assert answer["proposed"] is True
    assert proposals.items[0].kind == "image"
    assert proposals.items[0].brief == "A quiet harbour at dawn with fishing boats"


async def test_a_valid_brief_becomes_a_proposal_not_a_task(monkeypatch):
    """The model prepares; the person's click is what spends the quota."""
    from app.components import service as components_service
    from app.tasks import service as tasks_service

    async def nothing_close(session, *, brief):
        return None

    async def queued_nothing(*args, **kwargs):
        raise AssertionError("the tool must not queue without the person's confirmation")

    monkeypatch.setattr(components_service, "already_built", nothing_close)
    monkeypatch.setattr(tasks_service, "enqueue_task", queued_nothing)

    proposals = Proposals()
    tool = next(
        one
        for one in build_tools(
            caller=caller(), queued=[], suggested=Suggestions(), proposals=proposals
        )
        if one.name == "create_component"
    )
    answer = await tool.ainvoke({"brief": "A hero with one headline"})

    assert answer["queued"] is False
    assert answer["proposed"] is True
    assert "Nothing is queued yet" in answer["message"]
    assert [one.brief for one in proposals.items] == ["A hero with one headline"]


async def test_a_search_offers_only_the_matches_near_enough_to_be_one(monkeypatch):
    """A card is a claim that the registry has the thing, so a far row is not one."""
    from types import SimpleNamespace

    from app.agent import tools as agent_tools
    from app.agent.schemas import Suggestions
    from app.components import service as components_service

    near = SimpleNamespace(
        id=uuid.uuid4(),
        slug="tiered-pricing",
        title="Tiered pricing",
        description="Three plans in a ruled table",
    )
    far = SimpleNamespace(
        id=uuid.uuid4(),
        slug="proof-sheet-hero",
        title="Proof-sheet hero",
        description="A left-aligned headline on a rule grid",
    )

    async def nearest(session, *, query):
        return [(near, 0.29), (far, 0.68)]

    async def renders(session, *, ids):
        return {}

    monkeypatch.setattr(agent_tools, "_nearest_components", nearest)
    monkeypatch.setattr(components_service, "renders", renders)

    suggested = Suggestions()
    tool = next(
        one
        for one in build_tools(caller=caller(), queued=[], suggested=suggested)
        if one.name == "search_components"
    )
    answer = await tool.ainvoke({"query": "pricing table"})

    assert [match["slug"] for match in answer["matches"]] == ["tiered-pricing"]
    assert [one.slug for one in suggested.items] == ["tiered-pricing"]
