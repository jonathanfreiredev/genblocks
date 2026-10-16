"""The contract of the MCP door: discovery, and a token or nothing.

No tool call over HTTP is exercised here: that needs a token FastMCP will accept,
which means a real Supabase project. What these tests cover is what the server
promises every client — the discovery document, the 401 challenge, and that a
cookie is not a credential — plus the one tool's body, driven directly.
"""

import contextlib
import uuid
from collections.abc import AsyncIterator

import pytest
from fastmcp.server.auth import AccessToken
from httpx import ASGITransport, AsyncClient

from app.mcp import tools
from app.mcp.main import app as mcp_app
from app.mcp.server import mcp
from app.settings import settings

pytestmark = pytest.mark.anyio

# A well-formed JSON-RPC handshake, so a rejection can only come from auth.
_INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "1"},
    },
}
_STREAMING_HEADERS = {"Accept": "application/json, text/event-stream"}


@pytest.fixture
async def mcp_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=mcp_app)
    async with AsyncClient(transport=transport, base_url=settings.mcp_base_url) as client:
        yield client


async def test_the_discovery_document_points_at_supabase(mcp_client):
    # Path-aware, per RFC 9728: the resource is the MCP endpoint, so its metadata
    # lives under that path. Clients find it through the 401 challenge below.
    response = await mcp_client.get("/.well-known/oauth-protected-resource/mcp")

    assert response.status_code == 200
    body = response.json()
    assert body["resource"] == f"{settings.mcp_base_url}/mcp"
    assert body["authorization_servers"] == [settings.supabase_issuer]
    assert body["bearer_methods_supported"] == ["header"]


async def test_the_mcp_endpoint_challenges_for_a_token(mcp_client):
    response = await mcp_client.post("/mcp", json=_INITIALIZE, headers=_STREAMING_HEADERS)

    assert response.status_code == 401
    assert "resource_metadata=" in response.headers["www-authenticate"]


async def test_a_cookie_is_not_a_credential(mcp_client):
    mcp_client.cookies.set("sb-access-token", "not-a-token")

    response = await mcp_client.post("/mcp", json=_INITIALIZE, headers=_STREAMING_HEADERS)

    assert response.status_code == 401


async def test_the_server_is_alive(mcp_client):
    response = await mcp_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_whoami_is_registered():
    listed = await mcp.list_tools()

    assert "whoami" in {tool.name for tool in listed}


async def test_whoami_takes_the_caller_from_the_token(monkeypatch, db_session):
    subject = uuid.uuid4()
    monkeypatch.setattr(
        tools,
        "get_access_token",
        lambda: AccessToken(
            token="ignored",
            client_id="",
            scopes=[],
            claims={
                "sub": str(subject),
                "email": "jane@example.com",
                "user_metadata": {"full_name": "Jane Doe"},
            },
        ),
    )

    @contextlib.asynccontextmanager
    async def session_factory() -> AsyncIterator:
        yield db_session

    monkeypatch.setattr(tools, "async_session_maker", session_factory)

    profile = await tools.whoami()

    assert profile.email == "jane@example.com"
    assert profile.full_name == "Jane Doe"
    # Provisioned just-in-time, so a second call reuses the same profile.
    assert (await tools.whoami()).id == profile.id
