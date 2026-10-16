"""The MCP server: the door AI agents come through.

It runs as its own service (see ``docker-compose.yml``) rather than as a route on
the API, so agent traffic, scaling and restarts stay out of the API's way. Both
services share the domain layer, so a tool cannot do anything the API would not
allow, and the token verification is the same code (see ``app/mcp/auth.py``).
"""

from fastmcp import FastMCP
from fastmcp.server.auth.providers.supabase import SupabaseProvider
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.mcp.auth import SupabaseTokenVerifier
from app.settings import settings

auth = SupabaseProvider(
    project_url=settings.supabase_url,
    # The URL clients reach this server at, published in the discovery document.
    base_url=settings.mcp_base_url,
    # Supplied explicitly so tokens are verified by app.auth.verifier instead of a
    # second JWT implementation configured here.
    token_verifier=SupabaseTokenVerifier(),
)

mcp = FastMCP(name="mcp-stack", auth=auth)


@mcp.custom_route("/health", methods=["GET"])
async def _health(_: Request) -> JSONResponse:
    """Liveness probe for orchestrators.

    Custom routes are deliberately never authenticated: a liveness check cannot
    present a token.
    """
    return JSONResponse({"status": "ok"})
