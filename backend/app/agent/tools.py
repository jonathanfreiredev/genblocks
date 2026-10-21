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

from app.agent.schemas import Proposal, Proposals, Suggestion, Suggestions
from app.categories import service as categories_service
from app.components import planning
from app.components import service as components_service
from app.components.models import Component
from app.db.session import async_session_maker
from app.images import planning as image_planning
from app.images import service as images_service
from app.images.models import Image
from app.images.planning import ImagePlan
from app.images.schemas import ImagePrompt
from app.notifications import email as notifications
from app.pagination import ListParams
from app.tasks.models import Task
from app.tasks.schemas import Brief, TaskCreate
from app.users.models import User
from app.vectors import service as vectors

# How many published blocks a search puts in front of the model. Enough to see
# whether the registry already holds this block, few enough that the answer does
# not crowd out the conversation.
SEARCH_LIMIT = 5

# How near a result has to be before it is offered as a match. Cosine distance,
# smaller is nearer: the measured examples put "pricing block" at 0.51 for the
# pricing table and the next block at 0.63. Cards are a claim that the registry
# has the thing, so the far ones stay out of the conversation.
SEARCH_DISTANCE = 0.58

# How many pictures the library offers for one description.
PICTURE_LIMIT = 3

# Pictures are compared by a prompt against a photograph, so the same query sits
# further away than it would against code. The nearest unrelated scene is around
# 0.78; a workshop at 0.67 is still the workshop.
PICTURE_DISTANCE = 0.72


def build_tools(
    *,
    caller: User,
    queued: list[Task],
    suggested: Suggestions,
    proposals: Proposals | None = None,
) -> list[BaseTool]:
    """The tools one conversation can reach, with the caller already bound.

    ``proposals`` collects the briefs this conversation prepared. The endpoint
    reads them to put a confirmation card on the stream; the task itself is only
    created after the person clicks, through ``/v1/agent/confirm``. ``suggested``
    is the same idea for what the person may want to look at.

    ``queued`` is kept for the stream's shape, but no tool queues directly: a
    model talking to registry text must not be able to spend a month's quota.
    """
    prepared = proposals if proposals is not None else Proposals()

    @tool
    async def registry_overview() -> dict[str, Any]:
        """What the registry holds: how many published blocks and which categories exist.

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
                "These are public artifacts. Use search_components or find_images to show examples."
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
            relevant = [
                (block, distance) for block, distance in found if distance <= SEARCH_DISTANCE
            ]
            renders = await components_service.renders(
                session, ids=[block.id for block, _ in relevant]
            )

        for block, _distance in relevant:
            render = renders.get(block.id)
            suggested.add(_suggested(block, render.screenshot if render else None))

        if not relevant:
            return {
                "matches": [],
                "note": (
                    "Nothing in the registry is close enough to call a match. Say "
                    "so plainly and offer to build the block instead; do not name a "
                    "near miss as if it were the thing asked for."
                ),
            }

        return {
            "matches": [_described(block, distance) for block, distance in relevant],
            "note": (
                "Nearest first. Name the ones that fit; the cards show the "
                "render. A block that already exists is not worth building twice."
            ),
        }

    @tool
    async def find_images(query: str, category: str | None = None) -> dict[str, Any]:
        """Look through the public image library.

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

        relevant = [
            (picture, match.distance)
            for picture, match in zip(pictures, nearest, strict=False)
            if match.distance <= PICTURE_DISTANCE
        ]

        for picture, _distance in relevant:
            suggested.add(_suggested_image(picture))

        if not relevant:
            return {
                "images": [],
                "note": (
                    "Nothing in the library is close enough to the scene asked "
                    "for. Say so; ask for a new picture only if the person "
                    "genuinely wants one."
                ),
            }

        return {
            "images": [
                {
                    "id": str(picture.id),
                    "slug": picture.slug,
                    "prompt": picture.prompt,
                    "width": picture.width,
                    "height": picture.height,
                    "distance": round(distance, 3),
                }
                for picture, distance in relevant
            ],
            "note": (
                "These are already in the library. Name the ones that fit; the "
                "cards show the picture."
            ),
        }

    @tool
    async def plan_image(
        prompt: ImagePrompt, width: int, height: int, category: str
    ) -> dict[str, Any]:
        """Check a standalone image prompt before preparing it.

        ``width`` and ``height`` must be multiples of 32 between 256 and 1536.
        The prompt is checked for unsafe text and for people. If people are
        incidental, the answer contains a no-person prompt to offer the person.
        If the answer is ``ready``, call ``generate_image`` with the same prompt.
        """
        async with async_session_maker() as session:
            plan = await image_planning.plan_image(
                session,
                prompt=prompt,
                width=width,
                height=height,
                category=category,
            )

        await _image_policy_notice(caller, plan)
        return plan.as_body()

    @tool
    async def generate_image(
        prompt: ImagePrompt, width: int, height: int, category: str
    ) -> dict[str, Any]:
        """Prepare one standalone image task for the person to confirm.

        This does **not** queue anything: the person sees the prompt, its size
        and its category, and chooses whether to run it. The same monthly quota
        covers blocks and images.

        A prompt that asks for people is not prepared. Offer the no-person
        rewrite from ``plan_image`` and call this again only if the person
        accepts it.
        """
        async with async_session_maker() as session:
            plan = await image_planning.plan_image(
                session,
                prompt=prompt,
                width=width,
                height=height,
                category=category,
            )

        if not plan.ready:
            await _image_policy_notice(caller, plan)
            return {
                "queued": False,
                "proposed": False,
                "status": plan.status,
                "reason": plan.reason,
                "suggested_prompt": plan.suggested_prompt,
                "message": (
                    "Nothing was prepared. Offer the proposed no-person prompt, "
                    "and only call generate_image again if the person accepts it."
                    if plan.needs_confirmation
                    else "Nothing was prepared. Explain the refusal briefly."
                ),
            }

        prepared.add(
            Proposal(
                kind="image",
                brief=plan.prompt,
                width=plan.width,
                height=plan.height,
                category=plan.category,
            )
        )
        return {
            "queued": False,
            "proposed": True,
            "brief": plan.prompt,
            "width": plan.width,
            "height": plan.height,
            "category": plan.category,
            "message": (
                "The image is ready. Nothing is queued yet: the person sees it "
                "and chooses whether to run it."
            ),
        }

    @tool
    async def plan_component(brief: Brief) -> dict[str, Any]:
        """Check a component brief before preparing or queueing it.

        Every brief is checked for unsafe or injected text and for the image
        direction. A brief that asks for people in its pictures is not queued:
        the answer contains a no-person rewrite to offer the person. If the
        answer is ``ready``, call ``create_component`` with the same brief.
        """
        payload = TaskCreate(brief=brief)
        decision = await planning.plan(payload.brief)
        await _policy_notice(caller, decision)
        return decision.as_body()

    @tool
    async def create_component(brief: Brief, force: bool = False) -> dict[str, Any]:
        """Prepare the one task that would build the block.

        Call this once the brief says what the block is for, what it contains and
        what it must avoid. The brief is what the builder receives, so it is
        written as the request you would make of a designer rather than as a
        title. This call **does not queue anything**: it prepares the brief and
        the person confirms it. Do not call it twice for the same brief.

        It refuses when the registry already holds this block: the answer names
        what it found instead, and nothing is prepared. The person may still want
        their own version — only after they have said so, call it again with
        ``force``.
        """
        # Through the shared type rather than trusted from the argument: the
        # tool's schema tells the model what a brief looks like, and this is what
        # makes the rule hold when a brief arrives too short anyway.
        payload = TaskCreate(brief=brief)

        decision = await planning.plan(payload.brief)
        if not decision.ready:
            await _policy_notice(caller, decision)
            return {
                "queued": False,
                "proposed": False,
                "status": decision.status,
                "reason": decision.reason,
                "proposed_brief": decision.proposed_brief,
                "message": (
                    "Nothing was prepared. Offer the proposed no-person brief, "
                    "and only call create_component again if the person accepts it."
                    if decision.needs_confirmation
                    else "Nothing was prepared. Explain the refusal briefly."
                ),
            }

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
                    "proposed": False,
                    "already": _described(block, distance),
                    "message": (
                        "This block is already in the registry, so nothing was "
                        "prepared. Tell the person what it is, and let them decide "
                        "whether they still want a new one."
                    ),
                }

        prepared.add(Proposal(brief=payload.brief, force=force))
        return {
            "queued": False,
            "proposed": True,
            "brief": payload.brief,
            "message": (
                "The brief is ready. Nothing is queued yet: the person sees it and "
                "chooses whether to run it."
            ),
        }

    return [
        registry_overview,
        search_components,
        find_images,
        plan_image,
        generate_image,
        plan_component,
        create_component,
    ]


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


def _described(block: Component, distance: float | None) -> dict[str, Any]:
    """One block as the model reads it: enough to describe it, and its id."""
    return {
        "id": str(block.id),
        "slug": block.slug,
        "title": block.title,
        "description": block.description,
        **({"distance": round(distance, 3)} if distance is not None else {}),
    }


async def _pictures(session: Any, *, ids: list[Any]) -> list[Image]:
    """The library rows for a list of ids, in the order retrieval ranked them."""
    if not ids:
        return []

    return await images_service.by_ids(session, ids=ids)


def _suggested_image(picture: Image) -> Suggestion:
    """One picture as the dialog draws it."""
    return Suggestion(
        kind="image",
        id=picture.id,
        slug=picture.slug,
        title=picture.prompt,
        detail=f"{picture.width}×{picture.height}",
        path=picture.path,
        width=picture.width,
        height=picture.height,
    )


def _suggested(block: Component, path: str | None) -> Suggestion:
    """One block as the dialog draws it."""
    return Suggestion(
        kind="component",
        id=block.id,
        slug=block.slug,
        title=block.title,
        detail=block.description,
        path=path,
    )


async def _policy_notice(caller: User, decision: planning.PlanDecision) -> None:
    """Send the operator a metadata-only notice when a brief is refused."""
    if decision.ready:
        return

    await notifications.policy_event(
        kind="image_people" if decision.needs_confirmation else "brief_rejected",
        reason=decision.reason,
        brief=decision.brief,
        user_id=caller.id,
        user_email=caller.email,
    )


async def _image_policy_notice(caller: User, plan: ImagePlan) -> None:
    """Send the operator a metadata-only notice when an image prompt is refused."""
    if plan.ready:
        return

    await notifications.policy_event(
        kind="image_people" if plan.needs_confirmation else "image_prompt_rejected",
        reason=plan.reason,
        brief=plan.prompt,
        user_id=caller.id,
        user_email=caller.email,
    )
