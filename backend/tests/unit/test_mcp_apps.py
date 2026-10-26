"""The gallery an MCP Apps host draws beside a search.

A tool that carries a UI resource is two things: an answer, and a page that can
draw it. These tests pin the wiring — the resource is served as an app, its
policy allows our pictures and the host's helper and nothing else, and the two
searches are the tools that point at it.
"""

import pytest

from app.mcp import apps
from app.mcp import tools as mcp_tools  # noqa: F401  (import registers the tools)
from app.mcp.server import mcp
from app.settings import settings

pytestmark = pytest.mark.anyio


async def resources() -> dict[str, object]:
    return {str(one.uri): one for one in await mcp.list_resources()}


async def described_tools() -> dict[str, object]:
    return {one.name: one for one in await mcp.list_tools()}


async def test_the_gallery_is_served_as_an_app():
    gallery = (await resources())[apps.GALLERY_URI]

    # The host only renders it as a page under this type; anything else is a file.
    assert gallery.mime_type == "text/html;profile=mcp-app"


async def test_the_gallery_may_load_our_pictures_and_the_host_helper():
    gallery = (await resources())[apps.GALLERY_URI]

    # Same list the module builds, so a developer with another account still
    # passes; what matters is the two entries existing and being computed.
    assert gallery.meta["ui"]["csp"]["resourceDomains"] == apps.resource_domains()
    assert "https://unpkg.com" in apps.resource_domains()


async def test_the_policy_follows_the_delivery_base(monkeypatch):
    """The allowlist is the account's origin, not a constant somebody must update."""
    monkeypatch.setattr(settings, "asset_base_url", "https://assets.example.test/upload")

    assert apps.resource_domains() == [
        "https://assets.example.test",
        "https://unpkg.com",
    ]


async def test_a_deployment_with_no_delivery_base_allows_no_pictures(monkeypatch):
    monkeypatch.setattr(settings, "asset_base_url", "")

    assert apps.resource_domains() == ["https://unpkg.com"]


async def test_the_searches_are_the_tools_that_point_at_it():
    described = await described_tools()

    for name in ("search_images", "search_components"):
        assert described[name].meta["ui"]["resourceUri"] == apps.GALLERY_URI


async def test_a_single_read_has_no_gallery():
    """One item is text and two URLs; a gallery of one is a slower way to say it."""
    described = await described_tools()

    for name in ("get_image", "get_component"):
        assert described[name].meta is None or "ui" not in described[name].meta


async def test_the_gallery_draws_what_the_answer_carries():
    found = await mcp.read_resource(apps.GALLERY_URI)
    html = found.contents[0].content

    assert 'id="grid"' in html
    assert "structuredContent" in html
    # No picture is baked into the page: they arrive with each answer, which is
    # what lets one page serve every search.
    assert "res.cloudinary.com" not in html
    assert "https://unpkg.com/@modelcontextprotocol/ext-apps" in html


async def test_the_searches_still_publish_their_schema():
    """The resource is additive: a client that cannot draw it still deserializes."""
    described = await described_tools()

    for name in ("search_images", "search_components"):
        assert {"items", "total"} <= set(described[name].output_schema["properties"])
