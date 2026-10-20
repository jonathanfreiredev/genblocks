from typing import Annotated

from fastapi import Depends

from app.admin.service import require_admin
from app.authz.dependencies import get_first_party_user
from app.users.models import User


async def get_admin_user(
    user: Annotated[User, Depends(get_first_party_user)],
) -> User:
    """Resolve the caller and refuse anyone who is not a configured operator."""
    require_admin(user)
    return user
