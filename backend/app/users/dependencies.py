from typing import Annotated

import structlog
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.claims import TokenClaims
from app.auth.dependencies import get_token_claims
from app.db.session import get_async_db_session
from app.users.models import User
from app.users.service import get_or_create_user


async def get_current_user(
    claims: Annotated[TokenClaims, Depends(get_token_claims)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> User:
    """Resolve the bearer token to a local profile, provisioning it if needed."""
    user = await get_or_create_user(session, claims)
    # Attach the user to the log context so their requests are traceable.
    structlog.contextvars.bind_contextvars(user_id=str(user.id))
    return user
