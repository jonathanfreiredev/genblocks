"""The demo agent, wired the way the LangGraph quickstart wires one.

State that carries messages, a node that decides what to call, a node that calls it,
and an edge back to the decision. It differs from the quickstart in two things: the
decisions are written down instead of asked of a model, so a run needs no key, and the
graph keeps its place so a tool can stop the run and wait for an answer.

The loop is made of the library's own pieces — ``ToolNode`` runs the tools and
``tools_condition`` decides whether there is another round — so there is no
hand-rolled dispatcher to keep in step with them.
"""

from collections.abc import Callable
from typing import Any

from langchain.messages import AIMessage, ToolMessage
from langchain.tools import BaseTool
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.demo.tools import ACCEPTED


class AgentState(MessagesState):
    """What travels between the nodes.

    The messages are the run. ``approval`` is the one thing a tool needs to say
    that is not a message: how the person behind the page answered, which the
    deciding node reads to know whether there is anything left to do.
    """

    approval: str | None


# What the agent is asked to do, in order: the clock, the question, and the server. The
# question comes before the call that goes out, which is where asking belongs, and it
# means an anonymous visitor gets to answer one too.
SCRIPTED_PLAN: tuple[dict[str, Any], ...] = (
    {"name": "current_time", "args": {}},
    {"name": "ask_for_approval", "args": {"action": "call the MCP server as you"}},
    {"name": "whoami", "args": {}},
)


def decide(state: AgentState) -> dict[str, Any]:
    """The next tool call, or nothing left to call.

    This is the node a model would drive. Here the decisions are a tuple, which is what
    makes the run reproducible and free.

    A step that failed ends the script: the rest of the plan was going to lean on it,
    and a written-down plan that carried on anyway would be guessing.
    """
    messages = state["messages"]

    if state.get("approval") not in (None, ACCEPTED):
        # The step the run asked about was turned down, so there is nothing left
        # that it was going to lean on.
        return {"messages": [AIMessage(content="Stopped: the answer was no.")]}

    if any(isinstance(message, ToolMessage) and message.status == "error" for message in messages):
        return {"messages": [AIMessage(content="Stopped: a tool failed.")]}

    answered = sum(isinstance(message, ToolMessage) for message in messages)
    if answered >= len(SCRIPTED_PLAN):
        # No tool calls on the last message is what ends the loop.
        return {"messages": [AIMessage(content="Nothing left to do.")]}

    step = SCRIPTED_PLAN[answered]
    return {
        "messages": [
            AIMessage(content="", tool_calls=[{**step, "id": f"call_{answered}"}]),
        ]
    }


def scripted_agent(
    tools: list[BaseTool],
    on_tool_error: Callable[[Exception], str],
    checkpointer: Any,
) -> Any:
    """Wire the loop over the tools one visitor can reach, and compile it.

    ``on_tool_error`` is what keeps a tool that fails inside the trace: left to itself
    ``ToolNode`` ends the run on the exception, and the page would have nothing to show.

    ``checkpointer`` is what lets a tool stop the run and wait: the graph saves where it
    got to, and the next request carries on from there.
    """
    builder = StateGraph(AgentState)
    builder.add_node("decide", decide)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=on_tool_error))
    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", tools_condition)
    builder.add_edge("tools", "decide")
    return builder.compile(checkpointer=checkpointer)
