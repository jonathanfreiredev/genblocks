"""The conversational agent, wired once and remembered per conversation.

The loop is the library's own: ``create_agent`` builds the model → tools → model
cycle and compiles it with a checkpointer. The checkpointer is what makes a
conversation a conversation — the next turn is the same thread carried on rather
than a fresh start — and it is in memory, one per process, because a conversation
ends when the task starts (PLAN.md, Fase 6): it is a courtesy to the turn in
progress, not a store. The endpoint namespaces the key by user.
"""

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.prompts import SYSTEM_PROMPT

# Where one conversation's turns wait for the next request. In memory: this is
# one process, and what is kept is a single dialog's worth of turns.
MEMORY = InMemorySaver()


def build_agent(*, model: BaseChatModel, tools: list[BaseTool]):
    """Wire the loop over the tools one conversation can reach, and compile it."""
    return create_agent(
        model,
        tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MEMORY,
    )
