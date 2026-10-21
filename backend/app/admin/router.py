"""Operator endpoints for the whole vault, not just the report queue."""

import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependencies import get_admin_user
from app.admin.schemas import (
    AdminBanRequest,
    AdminComponentListQuery,
    AdminComponentSummary,
    AdminDeletionRead,
    AdminImageListQuery,
    AdminImageRead,
    AdminUserRead,
)
from app.admin.service import is_admin
from app.components.models import Component
from app.components.service import list_components, renders
from app.db.session import get_async_db_session
from app.deletion import service as deletion
from app.deletion.models import DeletionAudit
from app.images.models import Image
from app.images.service import list_images
from app.pagination import OffsetPage
from app.users.models import User
from app.users.service import display_names, get_user, list_users, set_ban

admin_items_router = APIRouter(prefix="/admin", tags=["admin"])


async def _component_summaries(
    session: AsyncSession, components: Sequence[Component]
) -> list[AdminComponentSummary]:
    names = await display_names(session, ids=[one.created_by for one in components])
    shots = await renders(session, ids=[one.id for one in components])

    return [
        AdminComponentSummary.model_validate(component).model_copy(
            update={
                "author": names.get(component.created_by) if component.created_by else None,
                "screenshot_path": shots.get(component.id),
            }
        )
        for component in components
    ]


def _image_read(image: Image, author: str | None) -> AdminImageRead:
    return AdminImageRead.model_validate(image).model_copy(update={"author": author})


@admin_items_router.get("/components", response_model=OffsetPage[AdminComponentSummary])
async def read_admin_components(
    _: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[AdminComponentListQuery, Query()],
) -> OffsetPage[AdminComponentSummary]:
    """Every public block, newest first."""
    components, total = await list_components(
        session,
        params=params,
        category_id=params.category_id,
        search=params.search,
    )

    return OffsetPage(
        items=await _component_summaries(session, components),
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@admin_items_router.get("/images", response_model=OffsetPage[AdminImageRead])
async def read_admin_images(
    _: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[AdminImageListQuery, Query()],
) -> OffsetPage[AdminImageRead]:
    """Every public picture, newest first."""
    images, total = await list_images(
        session,
        params=params,
        category_id=params.category_id,
        search=params.search,
    )
    names = await display_names(session, ids=[image.created_by for image in images])

    return OffsetPage(
        items=[
            _image_read(image, names.get(image.created_by) if image.created_by else None)
            for image in images
        ],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@admin_items_router.get("/deletions", response_model=list[AdminDeletionRead])
async def read_deletions(
    _: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[AdminDeletionRead]:
    """The latest deletion attempts, successful or not."""
    rows = list(
        await session.scalars(
            select(DeletionAudit).order_by(DeletionAudit.created_at.desc()).limit(limit)
        )
    )
    names = await display_names(session, ids=[row.actor_id for row in rows])

    return [
        AdminDeletionRead(
            id=row.id,
            kind=row.kind,
            target_id=row.target_id,
            slug=row.slug,
            title=row.title,
            actor=names.get(row.actor_id) if row.actor_id else None,
            paths=[str(path) for path in row.paths],
            result=row.result,
            error=row.error,
            created_at=row.created_at,
        )
        for row in rows
    ]


@admin_items_router.get("/users", response_model=list[AdminUserRead])
async def read_users(
    _: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    search: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AdminUserRead]:
    """The operator's user search, for a manual ban."""
    users, _total = await list_users(session, search=search, limit=limit, offset=offset)
    return [AdminUserRead.model_validate(user) for user in users]


@admin_items_router.get("/users/{user_id}", response_model=AdminUserRead)
async def read_user(
    user_id: uuid.UUID,
    _: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> AdminUserRead:
    user = await get_user(session, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such user.")
    return AdminUserRead.model_validate(user)


@admin_items_router.post("/users/{user_id}/ban", response_model=AdminUserRead)
async def ban_user(
    user_id: uuid.UUID,
    operator: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    payload: AdminBanRequest | None = None,
) -> AdminUserRead:
    """Ban a profile. Supabase is banned by the frontend action after this call."""
    if user_id == operator.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot ban your own account.",
        )

    target = await get_user(session, user_id=user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such user.")
    if is_admin(target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An operator account cannot be banned from this screen.",
        )

    await set_ban(
        session,
        user=target,
        operator=operator,
        banned=True,
        reason=payload.reason if payload else None,
    )
    return AdminUserRead.model_validate(target)


@admin_items_router.post("/users/{user_id}/unban", response_model=AdminUserRead)
async def unban_user(
    user_id: uuid.UUID,
    operator: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> AdminUserRead:
    target = await get_user(session, user_id=user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such user.")
    if is_admin(target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An operator account cannot be banned from this screen.",
        )

    await set_ban(session, user=target, operator=operator, banned=False)
    return AdminUserRead.model_validate(target)


@admin_items_router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component_endpoint(
    component_id: uuid.UUID,
    operator: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> Response:
    try:
        await deletion.delete_component(session, component_id=component_id, actor_id=operator.id)
    except deletion.DeletionFailed as failed:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(failed)) from failed

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_items_router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_endpoint(
    image_id: uuid.UUID,
    operator: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> Response:
    try:
        await deletion.delete_image(session, image_id=image_id, actor_id=operator.id)
    except deletion.DeletionFailed as failed:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(failed)) from failed

    return Response(status_code=status.HTTP_204_NO_CONTENT)
