"""One run of the demo.

The graph knows about messages and tools and nothing else. What this module owns is
what the graph should not: where those tools came from, whose token travels with them,
how a run that stopped to ask is carried on, and how the messages it leaves behind
become the trace the page renders.
"""

import json
import uuid
from typing import Any

from fastmcp.client import Client
from langchain.mcp import MCPAdapter
from langchain.messages import AIMessage, AnyMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from mcp.shared.exceptions import MCPError

from app.demo.graph import SCRIPTED_PLAN, scripted_agent
from app.demo.schemas import DemoRun, DemoToolCall
from app.demo.tools import AGENT_TOOLS, unlisted_server_tools
from app.settings import settings

REFUSAL = "This run carries no access token, so the server would not let it in."

# Where a run that stopped to ask waits for its answer. In memory, because this is one
# process and because a run nobody answers is worth nothing more than that; a real
# deployment would keep these somewhere it can expire them.
CHECKPOINTS = InMemorySaver()


async def run_demo(
    token: str | None,
    thread_id: str | None = None,
    decision: str | None = None,
) -> DemoRun:
    """Run the agent once, or carry on with a run that stopped to ask something.

    ``token`` is the visitor's, and it is what produces the two outcomes the page
    shows: with it the server publishes its catalogue and answers as the caller, and
    without it the run calls the tools by name and the door refuses them.

    ``thread_id`` and ``decision`` are set on the second request, when the visitor is
    answering a run that stopped: it is the same run, carried on from where it waited.
    """
    endpoint = settings.mcp_internal_endpoint
    failures: list[Exception] = []

    def keep(error: Exception) -> str:
        """Leave a failed tool in the trace instead of ending the run on it."""
        failures.append(error)
        return str(error)

    if token:
        # With a token the server describes its own tools, and the run works with what
        # it publishes instead of with anything written down here.
        try:
            async with MCPAdapter(Client(endpoint, auth=token)) as adapter:
                server_tools = await adapter.list_tools()
        except MCPError as shut:
            # The token was not accepted, so nothing was listed and nothing ran. That
            # is a fault at this end rather than the door turning a stranger away.
            failures.append(shut)
            refused, failed = _stopped(failures, token)
            return DemoRun(calls=[], refused=refused, failed=failed)
    else:
        # Without one there is no catalogue to ask for, so the plan's names are called
        # as the visitor and the door refuses them.
        server_tools = unlisted_server_tools(SCRIPTED_PLAN, AGENT_TOOLS, endpoint)

    agent = scripted_agent([*AGENT_TOOLS, *server_tools], keep, CHECKPOINTS)
    # The thread is what makes a stopped run findable again. The first request invents
    # one, and the page hands it back to carry on.
    thread = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread}}

    if decision is None:
        final = await agent.ainvoke({"messages": []}, config)
    else:
        final = await agent.ainvoke(Command(resume=decision), config)

    refused, failed = _stopped(failures, token)

    return DemoRun(
        calls=_trace(final["messages"], {tool.name for tool in server_tools}),
        refused=refused,
        failed=failed,
        approval=_question(final),
        thread_id=thread,
    )


def _question(final: dict[str, Any]) -> str | None:
    """What the run stopped to ask, when it stopped at all."""
    interrupts = final.get("__interrupt__") or []
    return str(interrupts[0].value) if interrupts else None


def _trace(messages: list[AnyMessage], server: set[str]) -> list[DemoToolCall]:
    """The trace the page renders, read off the messages the run left behind.

    The call the agent decided on is one message and its result is the next, so the two
    are paired up by the id the tool call carries. A call with no result yet is the one
    the run is waiting on, and the last one in the trace.
    """
    asked = {
        call["id"]: call
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    }
    answered = {message.tool_call_id for message in messages if isinstance(message, ToolMessage)}

    trace = []
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue

        call = asked.get(message.tool_call_id, {})
        name = message.name or call.get("name", "")
        broke = message.status == "error"
        trace.append(
            DemoToolCall(
                name=name,
                source="mcp" if name in server else "agent",
                arguments=call.get("args", {}),
                result=None if broke else _result(message),
                error=str(message.content) if broke else None,
            )
        )

    for call_id, call in asked.items():
        if call_id in answered:
            continue

        name = call.get("name", "")
        trace.append(
            DemoToolCall(
                name=name,
                source="mcp" if name in server else "agent",
                arguments=call.get("args", {}),
                pending=True,
            )
        )

    return trace


def _result(message: ToolMessage) -> dict[str, Any]:
    """A tool's answer as the page shows it.

    A server tool that declares an output type keeps its data in the message artifact,
    already structured. Everything else arrives as the text a model would read, which
    for these tools is the same data as JSON.
    """
    artifact = message.artifact
    if isinstance(artifact, dict):
        structured = artifact.get("structured_content")
        if isinstance(structured, dict):
            return structured

    return _as_data(message.content)


def _as_data(content: Any) -> dict[str, Any]:
    """A tool's answer as the block of data the page renders."""
    if isinstance(content, list):
        content = " ".join(block.get("text", "") for block in content if isinstance(block, dict))

    if isinstance(content, str):
        try:
            content = json.loads(content)
        except ValueError:
            return {"text": content}

    return content if isinstance(content, dict) else {"text": content}


def _stopped(failures: list[Exception], token: str | None) -> tuple[str | None, str | None]:
    """Which of the two failure states the run ended in, as the page words them.

    A refusal is the server turning away a caller with no token. Anything else is a
    tool that broke, and a rejected token counts as one of those: the caller had one and
    the server still said no.
    """
    if not failures:
        return None, None

    if token is None and isinstance(failures[0], MCPError):
        return REFUSAL, None

    return None, str(failures[0])
