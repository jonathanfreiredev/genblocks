"""The shapes the playground hands to the browser."""

from typing import Any, Literal

from pydantic import BaseModel


class DemoToolCall(BaseModel):
    """One tool the agent ran.

    ``source`` is the point of the demo: a tool that lives in the agent's own code needs
    nobody's permission, and a tool that lives on the MCP server has to get through the
    door first.

    ``pending`` is set while the run waits on a person: the agent asked for this one and
    it has not answered.
    """

    name: str
    source: Literal["agent", "mcp"]
    arguments: dict[str, Any] = {}
    result: dict[str, Any] | None = None
    error: str | None = None
    pending: bool = False


class DemoRunRequest(BaseModel):
    """What the page sends.

    Both are set when the visitor is answering a run that stopped to ask them something:
    the id is the run, and the decision is the answer. A run that has not stopped sends
    neither.
    """

    thread_id: str | None = None
    decision: Literal["accept", "reject"] | None = None


class DemoRun(BaseModel):
    """One pass of the demo, as the page renders it."""

    calls: list[DemoToolCall]
    # Set when the run never got past the MCP door, which is what an anonymous visitor
    # sees.
    refused: str | None = None
    # Set when a tool failed for a reason that is not the door.
    failed: str | None = None
    # Set when the run stopped to ask the visitor something, with the id the page sends
    # back to carry it on.
    approval: str | None = None
    thread_id: str | None = None
