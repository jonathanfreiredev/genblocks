"""Public read endpoints for the taxonomy.

Reading is public: the gallery is the shop window, and the taxonomy that organises
it is part of what a visitor sees.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import CategoryKind
from app.categories.schemas import CategoryRead
from app.categories.service import list_categories
from app.db.session import get_async_db_session

categories_router = APIRouter(prefix="/categories", tags=["categories"])


@categories_router.get("", response_model=list[CategoryRead])
async def read_categories(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    kind: Annotated[CategoryKind | None, Query()] = None,
) -> list[CategoryRead]:
    """Return the taxonomy, optionally narrowed to one kind.

    Unpaginated on purpose: the taxonomy is small and fixed, so a client renders
    the whole tree from one request.
    """
    categories = await list_categories(session, kind=kind)

    return [CategoryRead.model_validate(category) for category in categories]
