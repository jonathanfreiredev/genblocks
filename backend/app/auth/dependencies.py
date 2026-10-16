import asyncio
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.claims import InvalidClaims, TokenClaims, parse_claims
from app.auth.verifier import InvalidTokenError, decode_access_token

# auto_error=False so we control the response: a missing header is a 401, not a
# framework-generated error.
_bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_token_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> TokenClaims:
    """Resolve a verified Supabase access token into its claims."""
    if credentials is None:
        raise _UNAUTHORIZED

    try:
        # Verifying is blocking (the JWKS lookup hits the network on a cache
        # miss), so it runs in a worker thread instead of stalling the loop.
        payload = await asyncio.to_thread(decode_access_token, credentials.credentials)
        return parse_claims(payload)
    except InvalidTokenError, InvalidClaims:
        raise _UNAUTHORIZED from None


async def get_optional_token_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> tuple[str, TokenClaims] | None:
    """The caller's raw token and its claims, or ``None`` when they sent none.

    For the endpoints where an anonymous caller is a valid caller and the same
    request is meant to behave differently depending on whether a token is
    present. Verification is shared with ``get_token_claims``, so an invalid token
    is rejected exactly as it is everywhere else.
    """
    if credentials is None:
        return None

    return credentials.credentials, await get_token_claims(credentials)
