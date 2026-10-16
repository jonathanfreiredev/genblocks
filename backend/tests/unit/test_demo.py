"""The playground agent, driven without a network.

The graph under test is the real one, and so is the way a run becomes a trace and the
way a stopped run is carried on. Only the two ends are faked: the adapter that lists
the server's tools with a token, and the client a tool call goes out on, which is where
the door answers.
"""

import pytest
from langchain.tools import tool
from mcp.shared.exceptions import MCPError

from app.demo import runner, tools

pytestmark = pytest.mark.anyio

PLANNED = ["current_time", "ask_for_approval", "whoami"]
QUESTION = "Approve this action: call the MCP server as you?"


class Reached:
    """What a run sent towards the server."""

    def __init__(self) -> None:
        self.client: dict = {}
        self.calls: list[str] = []


class _Answer:
    """What a client hands back for a tool that answered."""

    def __init__(self, structured: dict) -> None:
        self.structured_content = structured


@pytest.fixture
def reached(monkeypatch) -> Reached:
    """A stand-in for the server, the adapter that lists it and the client underneath."""
    reached = Reached()

    class FakeClient:
        def __init__(self, url, auth=None) -> None:
            self.authorized = auth is not None
            reached.client = {"url": url, "authorized": self.authorized}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc) -> None:
            return None

        async def call_tool(self, name, arguments):
            reached.calls.append(name)

            if not self.authorized:
                raise MCPError(401, "Server returned an error response")

            return _Answer({"email": "jane@example.com"})

    @tool("whoami")
    async def whoami() -> dict:
        """Return the profile of the user whose token is calling."""
        reached.calls.append("whoami")

        if not reached.client["authorized"]:
            raise MCPError(401, "Server returned an error response")

        return {"email": "jane@example.com"}

    class FakeAdapter:
        def __init__(self, client) -> None:
            self.client = client

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc) -> None:
            return None

        async def list_tools(self):
            return [whoami]

    # The client is patched in the two places a run reaches for one: the adapter that
    # lists the catalogue, and the tool that calls the server by name when there is no
    # token to list it with.
    monkeypatch.setattr(runner, "Client", FakeClient)
    monkeypatch.setattr(tools, "Client", FakeClient)
    monkeypatch.setattr(runner, "MCPAdapter", FakeAdapter)
    return reached


async def test_the_run_stops_to_ask_and_says_what_it_is_waiting_on(reached):
    run = await runner.run_demo(token="a-visitor-token")

    assert run.approval == QUESTION
    assert run.thread_id is not None
    assert [call.name for call in run.calls] == ["current_time", "ask_for_approval"]

    waiting = run.calls[-1]
    assert waiting.pending is True
    assert waiting.source == "agent"
    assert waiting.result is None
    assert waiting.error is None
    # Nothing has gone out: the run is waiting on the person.
    assert reached.calls == []


async def test_with_no_token_the_run_asks_and_then_the_door_refuses(reached):
    paused = await runner.run_demo(token=None)

    assert paused.approval == QUESTION
    assert paused.refused is None

    refused = await runner.run_demo(
        token=None,
        thread_id=paused.thread_id,
        decision="accept",
    )

    assert [call.name for call in refused.calls] == PLANNED
    assert refused.calls[-1].source == "mcp"
    assert refused.calls[-1].error is not None
    assert refused.refused is not None
    assert refused.failed is None
    # No token means no header at all, which is what makes the refusal the server's
    # answer rather than a client that broke on the way there.
    assert reached.client["authorized"] is False
    assert reached.calls == ["whoami"]


async def test_accepting_carries_the_run_on(reached):
    paused = await runner.run_demo(token="a-visitor-token")

    resumed = await runner.run_demo(
        token="a-visitor-token",
        thread_id=paused.thread_id,
        decision="accept",
    )

    # The same run: the earlier step is still there, the question is answered, and the
    # server's tool is reached with the caller's token.
    assert [call.name for call in resumed.calls] == PLANNED
    assert resumed.approval is None
    assert resumed.calls[1].pending is False
    assert resumed.calls[1].result == {"decision": "accept", "message": "You accepted."}
    assert resumed.calls[2].source == "mcp"
    assert resumed.calls[2].result == {"email": "jane@example.com"}


async def test_rejecting_ends_the_run_before_the_call_goes_out(reached):
    paused = await runner.run_demo(token="a-visitor-token")

    resumed = await runner.run_demo(
        token="a-visitor-token",
        thread_id=paused.thread_id,
        decision="reject",
    )

    # What was asked about is the step that would have gone out, so refusing it leaves
    # nothing to do and nothing reaches the server.
    assert [call.name for call in resumed.calls] == ["current_time", "ask_for_approval"]
    assert resumed.calls[-1].result == {"decision": "reject", "message": "You rejected."}
    assert resumed.approval is None
    assert reached.calls == []


async def test_the_agents_own_tool_never_reaches_the_server(reached):
    run = await runner.run_demo(token="a-visitor-token")

    first = run.calls[0]
    assert first.name == "current_time"
    assert first.source == "agent"
    assert first.result is not None
    assert first.error is None


async def test_a_token_the_server_rejects_is_a_fault(reached, monkeypatch):
    class RefusingAdapter:
        def __init__(self, client) -> None:
            pass

        async def __aenter__(self):
            raise MCPError(401, "Server returned an error response")

        async def __aexit__(self, *exc) -> None:
            return None

        async def list_tools(self):
            raise AssertionError("the catalogue should have been refused")

    monkeypatch.setattr(runner, "MCPAdapter", RefusingAdapter)

    run = await runner.run_demo(token="a-rejected-token")

    # A caller the server should have known is a fault, not a stranger at the door.
    assert run.calls == []
    assert run.failed is not None
    assert run.refused is None


async def test_a_tool_that_breaks_is_reported_as_a_fault(reached, monkeypatch):
    @tool("whoami")
    async def whoami() -> dict:
        """Return the profile of the user whose token is calling."""
        raise RuntimeError("the database went away")

    class BreakingAdapter:
        def __init__(self, client) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc) -> None:
            return None

        async def list_tools(self):
            return [whoami]

    monkeypatch.setattr(runner, "MCPAdapter", BreakingAdapter)

    paused = await runner.run_demo(token="a-visitor-token")
    run = await runner.run_demo(
        token="a-visitor-token",
        thread_id=paused.thread_id,
        decision="accept",
    )

    # The fault is in the trace and named as one, not as the door refusing.
    assert run.calls[-1].error is not None
    assert run.failed is not None
    assert "the database went away" in run.failed
    assert run.refused is None
