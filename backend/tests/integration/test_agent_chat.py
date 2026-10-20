"""The conversation, over HTTP.

The graph, the tools and the checkpointer are the ones that ship. Only the model
is a script (``tests/agent_stub.py``): a test that reached OpenAI would be a test
that fails when the network does, and every phase after this one would inherit
it.

The stream is read the way the dialog reads it — frame by frame, off one
response — because that is the contract the frontend is written against.
"""

import contextlib
import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy import select

from app.agent import tools as agent_tools
from app.agent.model import get_chat_model
from app.main import app
from app.tasks.models import Task
from app.users.models import User
from tests.agent_stub import ScriptedChatModel
from tests.auth_stub import mint_token
from tests.helpers import auth_header, create_category, create_component

pytestmark = pytest.mark.anyio

BRIEF = "A pricing page for a developer tool: three tiers, an annual toggle."


def call(name: str, **arguments: Any) -> AIMessage:
    """A turn that reaches for a tool instead of talking."""
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": arguments, "id": f"call_{uuid.uuid4().hex[:8]}"}],
    )


def says(text: str) -> AIMessage:
    """A turn that answers in words."""
    return AIMessage(content=text)


@pytest.fixture
def agent_db(monkeypatch, db_session):
    """Point the agent's tools at the test session, the way a request gets one."""

    @contextlib.asynccontextmanager
    async def session_factory() -> AsyncIterator:
        yield db_session

    monkeypatch.setattr(agent_tools, "async_session_maker", session_factory)
    return db_session


@pytest.fixture
def scripted():
    """Hand the endpoint a model that says what it was told to say."""

    def run(model: ScriptedChatModel) -> ScriptedChatModel:
        app.dependency_overrides[get_chat_model] = lambda: model
        return model

    yield run
    app.dependency_overrides.pop(get_chat_model, None)


async def _sign_in(client, db_session, email: str) -> tuple[str, User]:
    """Provision the token's user the way a first sign-in does, and return both."""
    token = mint_token(email=email)
    response = await client.get("/v1/users/me", headers=auth_header(token))
    assert response.status_code == 200, response.text

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    return token, user


async def _turn(client, token: str, *, message: str, thread: str):
    return await client.post(
        "/v1/agent/chat",
        json={"message": message, "thread_id": thread},
        headers=auth_header(token),
    )


def _frames(response) -> list[tuple[str, dict]]:
    """The stream as the dialog reads it: one entry per event."""
    events = []
    for block in response.text.split("\n\n"):
        if not block.strip():
            continue

        name, _, data = block.partition("\ndata: ")
        events.append((name.removeprefix("event: "), json.loads(data)))

    return events


def _words(events: list[tuple[str, dict]]) -> str:
    return "".join(data["text"] for name, data in events if name == "token")


async def test_the_conversation_requires_a_token(client):
    response = await client.post(
        "/v1/agent/chat", json={"message": "build a hero", "thread_id": "thread-anon"}
    )

    assert response.status_code == 401


async def test_an_agents_own_token_cannot_hold_a_conversation(client):
    # A token issued to an OAuth client belongs to the MCP door. Accepting it
    # here would let an agent hold the conversation and queue through it.
    response = await _turn(
        client,
        mint_token(client_id="an-agent"),
        message="build a hero",
        thread="thread-agent",
    )

    assert response.status_code == 403


async def test_a_turn_streams_the_words_the_tools_and_the_task(
    client, db_session, agent_db, scripted
):
    token, user = await _sign_in(client, db_session, "maker@example.com")
    scripted(
        ScriptedChatModel(
            turns=[
                call("search_components", query="pricing"),
                call("create_component", brief=BRIEF),
                says("Queued. The checklist below is the task's own record."),
            ]
        )
    )

    response = await _turn(client, token, message="a pricing page, please", thread="thread-1")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _frames(response)
    names = [name for name, _ in events]

    # The model reaches for what the registry holds, then for the queue, and the
    # dialog is told about each call before it is told the call is over.
    assert events[0] == ("tool", {"name": "search_components", "state": "started"})
    assert ("tool", {"name": "search_components", "state": "finished"}) in events
    assert ("tool", {"name": "create_component", "state": "started"}) in events
    assert ("tool", {"name": "create_component", "state": "finished"}) in events

    # The task is on the wire as soon as the tool that made it returns, and
    # before the agent has finished the sentence about it.
    task = next(data for name, data in events if name == "task")
    assert names.index("task") < names.index("token")
    assert task["status"] == "pending"
    assert task["brief"] == BRIEF
    assert task["component_id"] is None
    assert task["steps"] == []

    # Words arrive in pieces rather than whole, which is the point of the stream.
    assert names.count("token") > 1
    assert _words(events).startswith("Queued.")
    assert events[-1] == ("done", {})

    queued = await db_session.scalar(select(Task).where(Task.id == uuid.UUID(task["id"])))
    assert queued is not None
    assert queued.created_by == user.id


async def test_the_overview_tells_the_model_what_the_registry_holds(
    client, db_session, agent_db, scripted
):
    token, _ = await _sign_in(client, db_session, "reader@example.com")
    category = await create_category(db_session, slug="hero")
    await create_component(db_session, category_id=category.id, slug="alpha")

    model = scripted(
        ScriptedChatModel(
            turns=[
                call("registry_overview"),
                says("One block so far, filed under Hero."),
            ]
        )
    )

    events = _frames(
        await _turn(
            client,
            token,
            message="what is in the registry?",
            thread="thread-overview",
        )
    )

    assert ("tool", {"name": "registry_overview", "state": "started"}) in events
    assert ("tool", {"name": "registry_overview", "state": "finished"}) in events
    assert _words(events) == "One block so far, filed under Hero."

    # The overview is a read, not a build: the answer carries the counts and the
    # categories the sidebar shows, and nothing was queued.
    told = " ".join(str(message.content) for message in model.seen[1])
    assert "blocks" in told
    assert "hero" in told
    assert "task" not in [name for name, _ in events]


async def test_the_next_turn_carries_on_where_the_last_one_stopped(
    client, db_session, agent_db, scripted
):
    token, _ = await _sign_in(client, db_session, "talker@example.com")
    model = scripted(
        ScriptedChatModel(turns=[says("What is this block for?"), says("Understood.")])
    )

    await _turn(client, token, message="I need a pricing page", thread="thread-memory")
    await _turn(client, token, message="For developers", thread="thread-memory")

    # The second turn was asked with the first one in front of it: two requests,
    # one conversation.
    said = [message.content for message in model.seen[1]]
    assert "I need a pricing page" in said
    assert "What is this block for?" in said
    assert said[-1] == "For developers"


async def test_one_conversation_is_not_another(client, db_session, agent_db, scripted):
    mine, _ = await _sign_in(client, db_session, "mine@example.com")
    theirs, _ = await _sign_in(client, db_session, "theirs@example.com")
    model = scripted(ScriptedChatModel(turns=[says("Hello.")]))

    await _turn(client, mine, message="my own words", thread="thread-shared")
    await _turn(client, theirs, message="their own words", thread="thread-shared")

    # A thread id is a name the browser chose, so it is namespaced by user: the
    # same name in another account is a different conversation.
    said = [message.content for message in model.seen[1]]
    assert "their own words" in said
    assert "my own words" not in said


async def test_a_brief_the_queue_refused_queues_nothing(client, db_session, agent_db, scripted):
    token, _ = await _sign_in(client, db_session, "slipper@example.com")
    model = scripted(
        ScriptedChatModel(
            turns=[
                call("create_component", brief="hero"),
                says("Let me ask again: what is the block for?"),
            ]
        )
    )

    events = _frames(await _turn(client, token, message="build something", thread="thread-refused"))

    # A brief too short to be one does not end the turn: the tool says so, the
    # model is told, and the conversation carries on with nothing queued.
    assert ("tool", {"name": "create_component", "state": "finished"}) in events
    assert "task" not in [name for name, _ in events]
    assert events[-1] == ("done", {})

    told = " ".join(str(message.content) for message in model.seen[1])
    assert "at least 10 characters" in told
    assert (await db_session.scalar(select(Task))) is None


async def test_a_model_that_breaks_ends_the_stream_with_a_word(
    client, db_session, agent_db, scripted
):
    class Breaking(ScriptedChatModel):
        def _stream(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("the model went away")

    token, _ = await _sign_in(client, db_session, "unlucky@example.com")
    scripted(Breaking(turns=[says("unreachable")]))

    events = _frames(await _turn(client, token, message="build a hero", thread="thread-broken"))

    # The 200 went out with the stream, so the failure has to be an event: a
    # dialog left waiting on a turn that died is the worst of the two endings.
    assert [name for name, _ in events] == ["error", "done"]
    assert "Nothing was queued" in events[0][1]["message"]
