"""The tools the conversational agent can reach.

Same names and same services as the MCP door: an agent inside this process and
an agent that arrives from outside queue the same work through the same rules.

Two things are different on purpose. The caller is bound here, when the tools are
built for one conversation, rather than resolved from an argument — a model can
be talked into writing someone else's id into a field, which is what decision 2
of PLAN.md exists to survive. And the answers are JSON rather than the Pydantic
types ``app/mcp/tools.py`` returns, because a langchain tool's result reaches the
model as text and a Pydantic repr is not something to read a task id out of.

Since Fase 10 the searches are retrieval, not substring: a brief is compared with
what blocks *are*, render included, so "a pricing table with three tiers" finds
the pricing table whether or not either is named that way. Substring search is
kept as the fallback for a registry that has no vectors yet — a development
database, or an embedder having a day — because a search that finds nothing is
worse than a search that finds less.
"""

from typing import Any

from langchain_core.tools import BaseTool, tool
from sqlalchemy import func, select

from app.agent.schemas import Suggestion, Suggestions
from app.categories import service as categories_service
from app.components import service as components_service
from app.components.models import Component
from app.db.session import async_session_maker
from app.images import service as images_service
from app.images.models import Image
from app.moderation import service as moderation
from app.pagination import ListParams
from app.tasks import limits
from app.tasks import service as tasks_service
from app.tasks.models import Task
from app.tasks.schemas import Brief, TaskCreate, TaskRead
from app.users.models import User
from app.vectors import service as vectors

# How many published blocks a search puts in front of the model. Enough to see
# whether the registry already holds this block, few enough that the answer does
# not crowd out the conversation.
SEARCH_LIMIT = 5

# How many pictures the library offers for one description.
PICTURE_LIMIT = 3


def build_tools(*, caller: User, queued: list[Task], suggested: Suggestions) -> list[BaseTool]:
    """The tools one conversation can reach, with the caller already bound.

    ``queued`` collects what this conversation creates. The endpoint reads it to
    put the task on the stream the moment the tool returns, instead of parsing it
    back out of the messages. ``suggested`` is the same idea for what the person
    may want to look at.
    """

    @tool
    async def registry_overview() -> dict[str, Any]:
        """What the registry holds: how many published blocks and pictures.

        Use it for overview questions — "how many blocks are there?", "what can I
        browse?", "which categories exist?" — before searching for a specific
        thing. The categories in the answer are the ones the sidebar shows.
        """
        async with async_session_maker() as session:
            blocks = await session.scalar(
                select(func.count()).select_from(Component).where(Component.deleted_at.is_(None))
            )
            pictures = await session.scalar(
                select(func.count()).select_from(Image).where(Image.deleted_at.is_(None))
            )
            categories = await categories_service.list_categories(session)

        return {
            "blocks": blocks or 0,
            "images": pictures or 0,
            "categories": [
                {"kind": category.kind, "slug": category.slug, "name": category.name}
                for category in categories
                if category.level == 2
            ],
            "note": (
                "These are published artifacts. Use search_components or "
                "find_images to show examples of a category."
            ),
        }

    @tool
    async def search_components(query: str) -> dict[str, Any]:
        """Find published blocks by what they are.

        ``query`` describes the block in plain words; the search compares
        meaning, not spelling. Use it to answer questions about blocks and to see
        what already exists before building. The matches appear as cards in the
        conversation, nearest first.
        """
        async with async_session_maker() as session:
            found = await _nearest_components(session, query=query)
            renders = await components_service.renders(
                session, ids=[block.id for block, _ in found]
            )

        for block, _distance in found:
            suggested.add(_suggested(block, renders.get(block.id)))

        return {
            "matches": [_described(block, distance) for block, distance in found],
            "note": (
                "Nearest first. Name the ones that fit; the cards show the "
                "render. A block that already exists is not worth building twice."
            ),
        }

    @tool
    async def find_images(query: str, category: str | None = None) -> dict[str, Any]:
        """Look through the picture library.

        Use it to answer what pictures exist, or to find one before asking a
        block to make a photograph. The library is reused rather than
        regenerated: a scene already filed is better than a new generation.

        Args:
            query: The scene, in the words a photographer would need.
            category: Which type of image to look in, when the block knows.
        """
        async with async_session_maker() as session:
            nearest = await vectors.find_images(query, limit=PICTURE_LIMIT, category=category)
            pictures = await _pictures(session, ids=[one.id for one in nearest])

        for picture in pictures:
            suggested.add(
                Suggestion(
                    kind="image",
                    id=picture.id,
                    title=picture.prompt,
                    detail=f"{picture.width}×{picture.height}",
                    path=picture.path,
                    width=picture.width,
                    height=picture.height,
                )
            )

        return {
            "images": [
                {
                    "id": str(picture.id),
                    "prompt": picture.prompt,
                    "width": picture.width,
                    "height": picture.height,
                    "distance": round(match.distance, 3),
                }
                for picture, match in zip(pictures, nearest, strict=False)
            ],
            "note": (
                "These are already in the library. Name the ones that fit; the "
                "cards show the picture."
            ),
        }

    @tool
    async def create_component(brief: Brief, force: bool = False) -> dict[str, Any]:
        """Queue the one task that builds the block, and return it.

        Call this once the brief says what the block is for, what it contains and
        what it must avoid. The brief is what the builder receives, so it is
        written as the request you would make of a designer rather than as a
        title. The call returns as soon as the work is queued; it does not wait
        for the block. Do not call it twice for the same brief.

        It refuses when the registry already holds this block: the answer names
        what it found instead, and nothing is queued. The person may still want
        their own version — only after they have said so, call it again with
        ``force``.
        """
        # Through the shared type rather than trusted from the argument: the
        # tool's schema tells the model what a brief looks like, and this is what
        # makes the rule hold when a brief arrives too short anyway.
        payload = TaskCreate(brief=brief)

        async with async_session_maker() as session:
            already = (
                None
                if force
                else await components_service.already_built(session, brief=payload.brief)
            )

            if already is not None:
                block, distance = already
                suggested.add(_suggested(block, None))
                return {
                    "queued": False,
                    "already": _described(block, distance),
                    "message": (
                        "This block is already in the registry, so nothing was "
                        "queued. Tell the person what it is, and let them decide "
                        "whether they still want a new one."
                    ),
                }

            try:
                task = await tasks_service.enqueue_task(
                    session, brief=payload.brief, created_by=caller.id, fresh=force
                )
            except limits.MonthlyQuotaReached as reached:
                return {
                    "queued": False,
                    "limit": str(reached),
                    "message": (
                        "Nothing was queued: the person has used this month's blocks. "
                        "Tell them when the next one opens; do not retry."
                    ),
                }
            except moderation.BriefRejected as refused:
                return {
                    "queued": False,
                    "refused": refused.reason,
                    "message": (
                        "Nothing was queued: the brief was refused. Say why, briefly, "
                        "and offer to write a different one."
                    ),
                }

        queued.append(task)
        return TaskRead.model_validate(task).model_dump(mode="json")

    return [registry_overview, search_components, find_images, create_component]


async def _nearest_components(session: Any, *, query: str) -> list[tuple[Component, float | None]]:
    """The blocks nearest to a query, with how near each one is.

    Retrieval first; free-text over titles and descriptions when there is no index
    to ask. Both are answers, and the second one is what a database with no
    vectors yet can give.
    """
    matches = await vectors.find_components(query, limit=SEARCH_LIMIT)
    blocks = await components_service.by_ids(session, ids=[one.id for one in matches])

    if blocks:
        distances = {one.id: one.distance for one in matches}
        return [(block, distances.get(block.id)) for block in blocks]

    found, _ = await components_service.list_components(
        session, params=ListParams(limit=SEARCH_LIMIT), search=query
    )

    return [(block, None) for block in found]


async def _pictures(session: Any, *, ids: list[Any]) -> list[Image]:
    """The library rows for a list of ids, in the order retrieval ranked them."""
    if not ids:
        return []

    found = await images_service.by_ids(session, ids=ids)

    return found


def _described(block: Component, distance: float | None) -> dict[str, Any]:
    """One block as the model reads it: enough to describe it, and its id."""
    return {
        "id": str(block.id),
        "slug": block.slug,
        "title": block.title,
        "description": block.description,
        **({"distance": round(distance, 3)} if distance is not None else {}),
    }


def _suggested(block: Component, path: str | None) -> Suggestion:
    """One block as the dialog draws it."""
    return Suggestion(
        kind="component",
        id=block.id,
        title=block.title,
        detail=block.description,
        path=path,
    )
