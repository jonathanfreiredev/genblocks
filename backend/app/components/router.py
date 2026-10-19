"""Public read endpoints for the block vault.

Every block here has been through the judge; that is what makes the vault public.
"""

import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import Component
from app.components.schemas import ComponentListQuery, ComponentRead, ComponentSummary
from app.components.service import (
    get_component,
    get_component_by_slug,
    list_components,
    renders,
)
from app.db.session import get_async_db_session
from app.generations.schemas import GenerationRead
from app.generations.service import list_generations
from app.pagination import OffsetPage
from app.users.service import display_names

components_router = APIRouter(prefix="/components", tags=["components"])


async def _summaries(
    session: AsyncSession, components: Sequence[Component]
) -> list[ComponentSummary]:
    """The list shape, with the two facts that live outside the block's row."""
    names = await display_names(session, ids=[one.created_by for one in components])
    shots = await renders(session, ids=[one.id for one in components])

    return [
        ComponentSummary.model_validate(component).model_copy(
            update={
                "author": names.get(component.created_by) if component.created_by else None,
                "screenshot_path": shots.get(component.id),
            }
        )
        for component in components
    ]


async def _read(session: AsyncSession, component: Component) -> ComponentRead:
    (summary,) = await _summaries(session, [component])

    return ComponentRead.model_validate(component).model_copy(
        update={
            "author": summary.author,
            "screenshot_path": summary.screenshot_path,
        }
    )


@components_router.get("", response_model=OffsetPage[ComponentSummary])
async def read_components(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[ComponentListQuery, Query()],
) -> OffsetPage[ComponentSummary]:
    """List blocks, newest first unless ``sort`` says otherwise.

    ``category_id`` narrows to one type; ``search`` matches the title and the
    description. The response carries the ``total`` matching the filters, so a
    client can page through them.
    """
    components, total = await list_components(
        session, params=params, category_id=params.category_id, search=params.search
    )

    return OffsetPage(
        items=await _summaries(session, components),
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@components_router.get("/by-slug/{slug}", response_model=ComponentRead)
async def read_component_by_slug(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ComponentRead:
    """Return one block by slug, the identifier a link uses."""
    component = await get_component_by_slug(session, slug=slug)
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found.")

    return await _read(session, component)


@components_router.get("/{component_id}", response_model=ComponentRead)
async def read_component(
    component_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ComponentRead:
    """Return one block in full, including the code a visitor copies."""
    component = await get_component(session, component_id=component_id)
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found.")

    return await _read(session, component)


@components_router.get("/{component_id}/generations", response_model=list[GenerationRead])
async def read_component_generations(
    component_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> list[GenerationRead]:
    """Return a block's whole attempt history, oldest first.

    Public like the rest of the vault. Not paginated: the list is bounded by the
    attempts of the tasks that produced this block, which is a handful by
    construction, so a page envelope would only get in the way.
    """
    component = await get_component(session, component_id=component_id)
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found.")

    attempts = await list_generations(session, component_id=component.id)

    return [GenerationRead.model_validate(attempt) for attempt in attempts]
