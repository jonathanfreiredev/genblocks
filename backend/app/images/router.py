"""The public image library, and the two doors that queue a new picture."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.dependencies import get_first_party_user
from app.db.session import get_async_db_session
from app.images.planning import (
    ImagePromptRejected,
    ImageSuggestionRequired,
    plan_image,
)
from app.images.schemas import (
    ImageListQuery,
    ImagePlanRead,
    ImagePlanRequest,
    ImageRead,
)
from app.images.service import get_image, get_image_by_slug, list_images
from app.notifications import email as notifications
from app.pagination import OffsetPage
from app.tasks.limits import MonthlyQuotaReached
from app.tasks.schemas import TaskRead
from app.tasks.service import enqueue_image_task
from app.users.models import User
from app.users.service import display_names

images_router = APIRouter(prefix="/images", tags=["images"])


def _plan_read(plan) -> ImagePlanRead:
    return ImagePlanRead(
        status=plan.status,
        prompt=plan.prompt,
        width=plan.width,
        height=plan.height,
        category=plan.category,
        reason=plan.reason,
        suggested_prompt=plan.suggested_prompt,
    )


@images_router.get("", response_model=OffsetPage[ImageRead])
async def read_images(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[ImageListQuery, Query()],
) -> OffsetPage[ImageRead]:
    """List public stock images, newest first unless ``sort`` says otherwise."""
    images, total = await list_images(
        session, params=params, category_id=params.category_id, search=params.search
    )

    names = await display_names(session, ids=[image.created_by for image in images])

    return OffsetPage(
        items=[
            ImageRead.model_validate(image).model_copy(
                update={"author": names.get(image.created_by) if image.created_by else None}
            )
            for image in images
        ],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@images_router.post("/plan", response_model=ImagePlanRead)
async def plan_new_image(
    payload: ImagePlanRequest,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ImagePlanRead:
    """Check a standalone prompt without generating or queueing anything."""
    plan = await plan_image(
        session,
        prompt=payload.prompt,
        width=payload.width,
        height=payload.height,
        category=payload.category,
    )
    if not plan.ready:
        await notifications.policy_event(
            kind="image_people" if plan.needs_confirmation else "image_prompt_rejected",
            reason=plan.reason,
            brief=plan.prompt,
            user_id=user.id,
            user_email=user.email,
        )
    return _plan_read(plan)


@images_router.post(
    "/generate",
    response_model=TaskRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_image(
    payload: ImagePlanRequest,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> TaskRead:
    """Queue one standalone image; the worker fills in its checklist."""
    try:
        task = await enqueue_image_task(
            session,
            prompt=payload.prompt,
            width=payload.width,
            height=payload.height,
            category=payload.category,
            created_by=user.id,
        )
    except MonthlyQuotaReached as reached:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(reached)
        ) from reached
    except ImageSuggestionRequired as confirmation:
        await notifications.policy_event(
            kind="image_people",
            reason=confirmation.reason,
            brief=payload.prompt,
            user_id=user.id,
            user_email=user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(confirmation),
                "suggested_prompt": confirmation.suggested_prompt,
            },
        ) from confirmation
    except ImagePromptRejected as refused:
        await notifications.policy_event(
            kind="image_prompt_rejected",
            reason=refused.reason,
            brief=payload.prompt,
            user_id=user.id,
            user_email=user.email,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(refused),
        ) from refused

    return TaskRead.model_validate(task)


@images_router.get("/by-slug/{slug}", response_model=ImageRead)
async def read_image_by_slug(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ImageRead:
    """Return one image by slug, the identifier a link uses."""
    image = await get_image_by_slug(session, slug=slug)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    names = await display_names(session, ids=[image.created_by])

    return ImageRead.model_validate(image).model_copy(
        update={"author": names.get(image.created_by) if image.created_by else None}
    )


@images_router.get("/{image_id}", response_model=ImageRead)
async def read_image(
    image_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ImageRead:
    """Return one image with its generation panel."""
    image = await get_image(session, image_id=image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found.")

    names = await display_names(session, ids=[image.created_by])

    return ImageRead.model_validate(image).model_copy(
        update={"author": names.get(image.created_by) if image.created_by else None}
    )
