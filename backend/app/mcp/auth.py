"""Token verification for the MCP door.

FastMCP handles the OAuth 2.1 plumbing — the discovery metadata and the 401
challenge that tells a client where to authenticate. The tokens are verified by
``app.auth.verifier``, the same code the REST API uses, so both doors accept
exactly the same tokens and the signature algorithms, issuer and audience stay
pinned in one place.

What neither door can check is the *audience*: Supabase does not support RFC 8707
resource indicators, so an access token is not bound to a specific resource, and
a token minted for the MCP server is also accepted by the API (and the reverse).
The API compensates by accepting only first-party tokens; the MCP tools are
constrained by their own policies. Both are documented in the README.
"""

import asyncio

from fastmcp.server.auth import AccessToken, TokenVerifier

from app.auth.claims import InvalidClaims, parse_claims
from app.auth.verifier import InvalidTokenError, decode_access_token


class SupabaseTokenVerifier(TokenVerifier):
    """Verify a Supabase access token exactly as the REST API does."""

    def __init__(self) -> None:
        # No base_url: the SupabaseProvider this is handed to owns the discovery
        # metadata, so this verifier only answers "is this token ours?".
        super().__init__()

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return the access token, or ``None`` when it must be rejected."""
        try:
            # Verifying is blocking (the JWKS lookup hits the network on a cache
            # miss), so it runs in a worker thread instead of stalling the loop.
            payload = await asyncio.to_thread(decode_access_token, token)
            claims = parse_claims(payload)
        except InvalidTokenError, InvalidClaims:
            return None

        return AccessToken(
            token=token,
            # Empty for the application's own login, which carries no client_id.
            client_id=claims.client_id or "",
            scopes=[],
            claims=dict(payload),
        )
