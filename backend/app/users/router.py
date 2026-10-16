from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz.dependencies import get_first_party_user
from app.db.session import get_async_db_session
from app.users.models import User
from app.users.schemas import UserRead, UserUpdate

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("/me", response_model=UserRead)
async def read_current_user(user: Annotated[User, Depends(get_first_party_user)]) -> User:
    """Return the current user's profile, provisioning it on first use."""
    return user


@users_router.patch("/me", response_model=UserRead)
async def update_current_user(
    data: UserUpdate,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> User:
    """Update the current user's profile (name only; email lives in Supabase)."""
    if data.full_name is not None:
        user.full_name = data.full_name
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


@users_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> None:
    """Delete the current user's profile.

    Hard delete: the row (and its mirrored email) is removed, so the same email
    can be used to sign up again. The Supabase identity is removed separately by
    the frontend, through the admin API.
    """
    await session.delete(user)
    await session.commit()
