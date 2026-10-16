"""The tools the demo agent carries itself.

Two live here. One reads the clock and needs nobody's permission. The other stops the
run and asks the person behind the page to approve an action, which is where a tool
that changes something should start.

The server's tools are not here. Where they come from depends on who is asking, and
`app/demo/runner.py` picks between the server's own catalogue and a call by name.
"""

import json
from datetime import UTC, datetime
from typing import Any

from fastmcp.client import Client
from langchain.messages import ToolMessage
from langchain.tools import BaseTool, ToolRuntime, tool
from langgraph.types import Command, interrupt

# What the page sends back when the visitor approves. Anything else is a refusal, so a
# run cannot be carried on by accident.
ACCEPTED = "accept"


@tool
def current_time() -> dict[str, Any]:
    """What the time is, in UTC."""
    return {"utc": datetime.now(UTC).isoformat(timespec="seconds")}


@tool
def ask_for_approval(action: str, runtime: ToolRuntime) -> dict[str, Any] | Command:
    """Ask the person behind the page to approve an action before it happens.

    Where a tool asks, the run stops and waits. The graph saves where it got to, the
    page puts the question to whoever is looking at it, and the same run carries on with
    their answer: nothing in between is lost, and the question is not asked twice.

    An accepted action is the tool's answer, and the run goes on. A refused one is said
    in the trace and written into the state, so the deciding node knows the step that was
    going to follow is not wanted. Doing the action belongs after the interrupt, which is
    the shape to copy for anything that changes something.
    """
    decision = interrupt(f"Approve this action: {action}?")

    if decision == ACCEPTED:
        return {"decision": decision, "message": "You accepted."}

    answer = {"decision": decision, "message": "You rejected."}
    return Command(
        update={
            "approval": decision,
            "messages": [
                ToolMessage(
                    content=json.dumps(answer),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


AGENT_TOOLS: list[BaseTool] = [current_time, ask_for_approval]


def unlisted_server_tools(
    plan: tuple[dict[str, Any], ...],
    agent_tools: list[BaseTool],
    url: str,
) -> list[BaseTool]:
    """The server's tools, for a caller it will not show its catalogue to.

    With a token the server describes its own tools and the graph uses those, so
    nothing about them is written down here. Without one there is no catalogue to ask
    for, and the run would have no tools at all — so one is built per server name the
    plan mentions, and it calls the server as the visitor. The door answering that call
    is the half of the demo an anonymous reader came for.

    No arguments are declared because the tools this server publishes take none. A tool
    that took some would need them described twice, and that is the point at which a
    caller with no token has to be given a catalogue some other way.
    """
    own = {tool.name for tool in agent_tools}
    return [_by_name(step["name"], url) for step in plan if step["name"] not in own]


def _by_name(name: str, url: str) -> BaseTool:
    """One server tool, reached by the name the plan uses."""

    @tool(name)
    async def call() -> dict[str, Any]:
        """A tool the MCP server publishes."""
        async with Client(url) as client:
            result = await client.call_tool(name, {})

        return result.structured_content or {}

    return call
