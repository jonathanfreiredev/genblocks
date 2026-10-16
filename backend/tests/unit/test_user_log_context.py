import uuid
from types import SimpleNamespace

import pytest
import structlog

from app.auth.claims import TokenClaims
from app.users import dependencies

pytestmark = pytest.mark.anyio


async def test_current_user_binds_user_id_to_the_log_context(monkeypatch):
    user = SimpleNamespace(id=uuid.uuid4())

    async def fake_get_or_create_user(session, claims):
        return user

    monkeypatch.setattr(dependencies, "get_or_create_user", fake_get_or_create_user)

    structlog.contextvars.clear_contextvars()
    claims = TokenClaims(subject=uuid.uuid4(), email=None, metadata={})

    await dependencies.get_current_user(claims=claims, session=None)

    assert structlog.contextvars.get_contextvars()["user_id"] == str(user.id)
    structlog.contextvars.clear_contextvars()
