"""The tools the MCP server exposes.

A tool is a thin adapter: resolve the caller from the token, call the domain, and
return a typed result. No business rule lives here — the rules are in the domain
services, shared with the API, so the two doors cannot drift apart.

Nor does authorization live here. The service a tool calls is the one that checks
what the caller's role grants, exactly as it does for the API, so there is no
second place where a permission could be written down and then forgotten.
"""

import uuid

from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel

from app.auth.claims import parse_claims
from app.db.session import async_session_maker
from app.mcp.server import mcp
from app.users.service import get_or_create_user


class CallerProfile(BaseModel):
    """The authenticated caller's own profile."""

    id: uuid.UUID
    email: str | None
    full_name: str | None


@mcp.tool
async def whoami() -> CallerProfile:
    """Return the profile of the user whose token is calling this tool.

    The caller comes from the access token, never from an argument: arguments are
    chosen by a model, and a model can be talked into lying.
    """
    access = get_access_token()
    if access is None:  # pragma: no cover - the endpoint rejects unauthenticated calls
        raise RuntimeError("whoami was called without an access token")

    claims = parse_claims(access.claims)

    async with async_session_maker() as session:
        user = await get_or_create_user(session, claims)

    return CallerProfile(id=user.id, email=user.email, full_name=user.full_name)
