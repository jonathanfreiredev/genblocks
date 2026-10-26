"""Reading a published asset back, so a tool can hand the picture over.

The URL is composed from the account's base, so there is no host to attack from
an argument. What is worth pinning is the refusal list: no bytes for a missing
asset, an error page, a type that is not a picture, or something too large to be
an answer.
"""

import httpx
import pytest

from app.mcp import assets
from app.settings import settings

pytestmark = pytest.mark.anyio

PNG = b"\x89PNG\r\n\x1a\n"
ADDRESS = "https://assets.example.test/upload/genblocks/images/dawn"


@pytest.fixture
def delivery_base(monkeypatch) -> None:
    monkeypatch.setattr(settings, "asset_base_url", "https://assets.example.test/upload")


def client_for(
    *,
    body: bytes = PNG,
    status: int = 200,
    media_type: str = "image/png",
    broke: Exception | None = None,
) -> tuple[httpx.AsyncClient, dict]:
    """A client that answers one request without sending it, and what it was asked."""
    sent: dict = {}

    async def handle(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        if broke is not None:
            raise broke
        return httpx.Response(status, headers={"content-type": media_type}, content=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handle)), sent


async def test_a_published_picture_comes_back_with_its_format(delivery_base):
    client, _ = client_for()

    found = await assets.fetch("genblocks/images/dawn", client=client)

    assert found is not None
    assert found.data == PNG
    assert found.format == "png"


async def test_the_address_is_the_base_and_the_id(delivery_base):
    client, sent = client_for()

    await assets.fetch("genblocks/images/dawn", client=client)

    assert sent["url"] == ADDRESS


async def test_a_content_type_with_parameters_is_still_a_picture(delivery_base):
    client, _ = client_for(media_type="image/jpeg; charset=binary")

    found = await assets.fetch("genblocks/images/dawn", client=client)

    assert found is not None
    assert found.format == "jpeg"


async def test_an_absent_id_is_not_fetched(delivery_base):
    client, _ = client_for()

    assert await assets.fetch(None, client=client) is None
    assert await assets.fetch("", client=client) is None


async def test_a_deployment_with_no_delivery_base_hands_nothing_over(monkeypatch):
    monkeypatch.setattr(settings, "asset_base_url", "")
    client, _ = client_for()

    assert await assets.fetch("genblocks/images/dawn", client=client) is None


async def test_a_missing_asset_is_not_a_picture(delivery_base):
    client, _ = client_for(status=404)

    assert await assets.fetch("genblocks/images/gone", client=client) is None


async def test_an_answer_that_is_not_an_image_is_not_handed_over(delivery_base):
    client, _ = client_for(media_type="text/html")

    assert await assets.fetch("genblocks/images/dawn", client=client) is None


async def test_something_too_large_to_be_an_answer_is_skipped(delivery_base, monkeypatch):
    monkeypatch.setattr(assets, "MAX_BYTES", 4)
    client, _ = client_for()

    assert await assets.fetch("genblocks/images/dawn", client=client) is None


async def test_a_broken_network_is_not_a_failed_tool(delivery_base):
    client, _ = client_for(broke=httpx.ConnectError("no route"))

    assert await assets.fetch("genblocks/images/dawn", client=client) is None
