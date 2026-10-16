"""The tools the MCP server exposes.

A tool is a thin adapter: resolve the caller from the token, call the domain, and
return a typed result. No business rule lives here — the rules are in the domain
services, shared with the API, so the two doors cannot drift apart.

Nor does authorization live here. The service a tool calls is the one that checks
what the caller's role grants, exactly as it does for the API, so there is no
second place where a permission could be written down and then forgotten.

A tool name is published the moment it ships, so these are frozen: a new tool is
added beside an old one, never renamed over it (see PLAN.md).
"""

import uuid

from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.claims import parse_claims
from app.categories import service as categories_service
from app.categories.models import CategoryKind
from app.categories.schemas import CategoryRead
from app.components import service as components_service
from app.components.models import Component
from app.components.schemas import ComponentRead, ComponentSummary
from app.db.session import async_session_maker
from app.images import service as images_service
from app.images.schemas import ImageRead
from app.mcp.server import mcp
from app.pagination import DEFAULT_LIMIT, ListParams, OffsetPage
from app.tasks import service as tasks_service
from app.tasks.models import TaskStatus
from app.tasks.schemas import TaskRead
from app.users.models import User
from app.users.service import get_or_create_user


class CallerProfile(BaseModel):
    """The authenticated caller's own profile."""

    id: uuid.UUID
    email: str | None
    full_name: str | None


async def _caller(session: AsyncSession) -> User:
    """Resolve the caller from the access token, never from an argument.

    Arguments are chosen by a model, and a model can be talked into lying, so the
    identity a tool acts on comes from the token and from nowhere else.
    """
    access = get_access_token()
    if access is None:  # pragma: no cover - the endpoint rejects unauthenticated calls
        raise RuntimeError("An MCP tool was called without an access token")

    return await get_or_create_user(session, parse_claims(access.claims))


@mcp.tool
async def whoami() -> CallerProfile:
    """Return the profile of the user whose token is calling this tool."""
    async with async_session_maker() as session:
        user = await _caller(session)

    return CallerProfile(id=user.id, email=user.email, full_name=user.full_name)


@mcp.tool
async def list_categories(kind: CategoryKind | None = None) -> list[CategoryRead]:
    """List the taxonomy: the two kinds and the types filed under each.

    Pass ``kind`` ("component" or "image") to narrow it to one side. The taxonomy
    is small and fixed, so it comes back whole rather than paginated.
    """
    async with async_session_maker() as session:
        categories = await categories_service.list_categories(session, kind=kind)

    return [CategoryRead.model_validate(category) for category in categories]


@mcp.tool
async def search_components(
    query: str | None = None,
    category_id: uuid.UUID | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> OffsetPage[ComponentSummary]:
    """Find published blocks to reuse, newest first.

    ``query`` matches the title and the description; ``category_id`` narrows to
    one type. ``total`` in the result is the number of matches, so ``limit`` and
    ``offset`` can walk through them. Read one in full with ``get_component``.
    """
    params = ListParams(limit=limit, offset=offset)

    async with async_session_maker() as session:
        components, total = await components_service.list_components(
            session, params=params, category_id=category_id, search=query
        )

    return OffsetPage(
        items=[ComponentSummary.model_validate(component) for component in components],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


async def _find_component(
    session: AsyncSession,
    *,
    component_id: uuid.UUID | None,
    slug: str | None,
) -> Component | None:
    """Resolve whichever identifier the caller gave; ``None`` if it named nothing."""
    if component_id is not None:
        return await components_service.get_component(session, component_id=component_id)

    if slug is not None:
        return await components_service.get_component_by_slug(session, slug=slug)

    return None


@mcp.tool
async def get_component(
    component_id: uuid.UUID | None = None,
    slug: str | None = None,
) -> ComponentRead:
    """Read one block in full: its code, its delivery prompt and its spec.

    Give exactly one identifier — ``component_id`` from a search, or ``slug``
    from a link.
    """
    if component_id is None and slug is None:
        raise ValueError("Give either component_id or slug.")
    if component_id is not None and slug is not None:
        raise ValueError("Give either component_id or slug, not both.")

    async with async_session_maker() as session:
        component = await _find_component(session, component_id=component_id, slug=slug)

    if component is None:
        raise ValueError("No component matches that identifier.")

    return ComponentRead.model_validate(component)


@mcp.tool
async def search_images(
    query: str | None = None,
    category_id: uuid.UUID | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> OffsetPage[ImageRead]:
    """Find stock images to illustrate a block, newest first.

    ``query`` matches the prompt that produced the image; ``category_id`` narrows
    to one type. Each result carries its own generation panel: the model, the
    scores and the trace.
    """
    params = ListParams(limit=limit, offset=offset)

    async with async_session_maker() as session:
        images, total = await images_service.list_images(
            session, params=params, category_id=category_id, search=query
        )

    return OffsetPage(
        items=[ImageRead.model_validate(image) for image in images],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@mcp.tool
async def list_tasks(
    status: TaskStatus | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> OffsetPage[TaskRead]:
    """List the background tasks you started, newest first, with their checklists.

    Only your own tasks are returned. Pass ``status`` to see, for instance, what
    is still running.
    """
    params = ListParams(limit=limit, offset=offset)

    async with async_session_maker() as session:
        caller = await _caller(session)
        tasks, total = await tasks_service.list_tasks(
            session, params=params, created_by=caller.id, status=status
        )

    return OffsetPage(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@mcp.tool
async def get_task(task_id: uuid.UUID) -> TaskRead:
    """Read one of your own tasks: its status, its error and its checklist.

    Call this to follow a task you started, instead of waiting on the call that
    created it.
    """
    async with async_session_maker() as session:
        caller = await _caller(session)
        task = await tasks_service.get_task(session, task_id=task_id, created_by=caller.id)

    if task is None:
        raise ValueError("No task of yours matches that id.")

    return TaskRead.model_validate(task)
