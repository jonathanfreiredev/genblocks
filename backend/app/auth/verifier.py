import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError

from app.settings import settings

# Supabase signs access tokens with an asymmetric key. RS256 is the default for
# new projects; ES256 is accepted for projects configured with an EC key.
ALLOWED_ALGORITHMS = ["RS256", "ES256"]

_jwk_client: PyJWKClient | None = None


class InvalidTokenError(Exception):
    """Raised when an access token is missing, malformed or untrusted."""


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(settings.supabase_jwks_url, cache_keys=True)
    return _jwk_client


def decode_access_token(token: str) -> dict:
    """Verify a Supabase access token and return its claims.

    The signature is checked against the project's JWKS, and the issuer and
    audience are validated so tokens from another project (or with the wrong
    audience) are rejected. Anything that fails raises ``InvalidTokenError``.

    This is blocking: the JWKS fetch does network I/O on a cache miss, so async
    callers must run it off the event loop (see ``get_token_claims``).
    """
    try:
        signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=ALLOWED_ALGORITHMS,
            audience=settings.supabase_jwt_audience,
            issuer=settings.supabase_issuer,
        )
    except (PyJWTError, PyJWKClientError) as error:
        raise InvalidTokenError(str(error)) from error
