"""The tools the conversational agent can reach.

Same names and same services as the MCP door: an agent inside this process and
an agent that arrives from outside queue the same work through the same rules.

Two things are different on purpose. The caller is bound here, when the tools are
built for one conversation, rather than resolved from an argument — a model can
be talked into writing someone else's id into a field, which is what decision 2
of PLAN.md exists to survive. And the answers are JSON rather than the Pydantic
types ``app/mcp/tools.py`` returns, because a langchain tool's result reaches the
model as text and a Pydantic repr is not something to read a task id out of.
"""

from typing import Any

from langchain_core.tools import BaseTool, tool

from app.components import service as components_service
from app.db.session import async_session_maker
from app.pagination import ListParams
from app.tasks import service as tasks_service
from app.tasks.models import Task
from app.tasks.schemas import Brief, TaskCreate, TaskRead
from app.users.models import User

# How many published blocks a search puts in front of the model. Enough to see
# whether the registry already holds this block, few enough that the answer does
# not crowd out the conversation.
SEARCH_LIMIT = 5


def build_tools(*, caller: User, queued: list[Task]) -> list[BaseTool]:
    """The tools one conversation can reach, with the caller already bound.

    ``queued`` collects what this conversation creates. The endpoint reads it to
    put the task on the stream the moment the tool returns, instead of parsing it
    back out of the messages.
    """

    @tool
    async def search_components(query: str) -> dict[str, Any]:
        """Find published blocks that may already answer the brief.

        ``query`` matches a block's title and its description. The result holds
        the matches and the number the registry has in total, so it is clear
        whether there is more to look at.
        """
        params = ListParams(limit=SEARCH_LIMIT)

        async with async_session_maker() as session:
            components, total = await components_service.list_components(
                session, params=params, search=query
            )

        return {
            "matches": [
                {
                    "slug": component.slug,
                    "title": component.title,
                    "description": component.description,
                }
                for component in components
            ],
            "total": total,
        }

    @tool
    async def create_component(brief: Brief) -> dict[str, Any]:
        """Queue the one task that builds the block, and return it.

        Call this once the brief says what the block is for, what it contains and
        what it must avoid. The brief is what the builder receives, so it is
        written as the request you would make of a designer rather than as a
        title. The call returns as soon as the work is queued; it does not wait
        for the block, and there is no reason to call it twice.
        """
        # Through the shared type rather than trusted from the argument: the
        # tool's schema tells the model what a brief looks like, and this is what
        # makes the rule hold when a brief arrives too short anyway.
        payload = TaskCreate(brief=brief)

        async with async_session_maker() as session:
            task = await tasks_service.create_task(
                session, brief=payload.brief, created_by=caller.id
            )

        queued.append(task)
        return TaskRead.model_validate(task).model_dump(mode="json")

    return [search_components, create_component]
