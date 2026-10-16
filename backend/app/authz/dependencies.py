"""Resolving the bearer token into the user the REST door accepts.

The API and the MCP server are two doors into the same domain: this one serves
the application's own session, the other serves AI agents. A Supabase access
token says which door it was issued for through its ``client_id`` claim, and each
door only accepts its own.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.auth.claims import TokenClaims
from app.auth.dependencies import get_optional_token_claims, get_token_claims
from app.users.dependencies import get_current_user
from app.users.models import User


async def get_optional_first_party_token(
    caller: Annotated[tuple[str, TokenClaims] | None, Depends(get_optional_token_claims)],
) -> str | None:
    """The caller's raw token when the REST door accepts them, or ``None``.

    The same rule as :func:`get_first_party_user`, for the one endpoint that has to
    answer an anonymous caller: this API never acts on a token issued to an OAuth
    client, not even to relay it to the MCP server on the caller's behalf.
    """
    if caller is None:
        return None

    token, claims = caller
    if claims.client_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This token was issued to an OAuth client and cannot be used with this API.",
        )

    return token


async def get_first_party_user(
    claims: Annotated[TokenClaims, Depends(get_token_claims)],
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Resolve the caller for the REST door, which admits only first-party tokens.

    A token carrying a ``client_id`` was issued to an OAuth client: the user
    approved an agent, and that token belongs to the MCP door. Accepting it here
    would let an agent call this API directly, bypassing the tool policies.

    The rejection is a 403 rather than a 401 on purpose: the token is valid and
    re-authenticating would produce the same token, so a client should not retry.
    """
    if claims.client_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This token was issued to an OAuth client and cannot be used with this API.",
        )

    return user
