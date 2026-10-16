"""Public read endpoints for the block vault.

Every block here has been through the judge; that is what makes the vault public.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.schemas import ComponentListQuery, ComponentRead, ComponentSummary
from app.components.service import get_component, get_component_by_slug, list_components
from app.db.session import get_async_db_session
from app.pagination import OffsetPage

components_router = APIRouter(prefix="/components", tags=["components"])


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
        items=[ComponentSummary.model_validate(component) for component in components],
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

    return ComponentRead.model_validate(component)


@components_router.get("/{component_id}", response_model=ComponentRead)
async def read_component(
    component_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ComponentRead:
    """Return one block in full, including the code a visitor copies."""
    component = await get_component(session, component_id=component_id)
    if component is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found.")

    return ComponentRead.model_validate(component)
