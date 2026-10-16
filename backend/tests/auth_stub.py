"""Test helpers to forge Supabase-style access tokens without a real project.

The tokens are signed with a local RSA key and verified against it: only the
JWKS *lookup* is stubbed, so signature, issuer, audience and expiry checks are
still exercised for real.
"""

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.settings import settings

ALGORITHM = "RS256"

PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = PRIVATE_KEY.public_key()


class _StubJWKClient:
    def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
        return SimpleNamespace(key=PUBLIC_KEY)


def install_fake_jwks(monkeypatch) -> None:
    """Make the verifier resolve signing keys from the local test key."""
    import app.auth.verifier as verifier

    monkeypatch.setattr(verifier, "_get_jwk_client", lambda: _StubJWKClient())


def mint_token(
    subject: uuid.UUID | None = None,
    email: str | None = "jane@example.com",
    full_name: str | None = "Jane Doe",
    audience: str | None = None,
    issuer: str | None = None,
    expires_in_seconds: int = 3600,
    client_id: str | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject or uuid.uuid4()),
        "aud": audience or settings.supabase_jwt_audience,
        "iss": issuer or settings.supabase_issuer,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in_seconds),
        "role": "authenticated",
        "email": email,
        "user_metadata": {"full_name": full_name},
    }
    if client_id is not None:
        # Supabase omits this claim for its own (first-party) logins and sets it
        # when the token was issued to an OAuth client.
        payload["client_id"] = client_id
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)
