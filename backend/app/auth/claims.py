"""Our own view of a Supabase access token.

Both doors need the same mapping from verified claims to ``TokenClaims``. The API
verifies the signature itself (``app/auth/verifier.py``) while the MCP server
delegates that to FastMCP, but what they read out of the payload is identical, so
that mapping lives here instead of inside either door.
"""

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenClaims:
    """The subset of Supabase access-token claims the application relies on."""

    subject: uuid.UUID
    email: str | None
    metadata: dict
    # Set when the token was issued to an OAuth client (an AI agent), and unset
    # for the application's own login. Each door treats them differently.
    client_id: str | None = None


class InvalidClaims(Exception):
    """Raised when a verified token does not carry the claims we need."""


def parse_claims(payload: Mapping[str, Any]) -> TokenClaims:
    """Build ``TokenClaims`` from a token payload whose signature is verified."""
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidClaims("The token carries no subject")

    try:
        subject_id = uuid.UUID(subject)
    except ValueError as error:
        raise InvalidClaims("The token subject is not a UUID") from error

    return TokenClaims(
        subject=subject_id,
        email=payload.get("email"),
        metadata=payload.get("user_metadata") or {},
        client_id=payload.get("client_id"),
    )
