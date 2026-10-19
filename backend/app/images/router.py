"""Public read endpoints for the stock image library."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db_session
from app.images.schemas import ImageListQuery, ImageRead
from app.images.service import get_image, list_images
from app.pagination import OffsetPage
from app.users.service import display_names

images_router = APIRouter(prefix="/images", tags=["images"])


@images_router.get("", response_model=OffsetPage[ImageRead])
async def read_images(
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[ImageListQuery, Query()],
) -> OffsetPage[ImageRead]:
    """List stock images, newest first unless ``sort`` says otherwise.

    ``category_id`` narrows to one type; ``search`` matches the prompt that
    produced the image.
    """
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
