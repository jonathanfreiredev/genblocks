"""Fetching a published asset so a tool can hand the picture over.

An MCP tool result can carry an image block, and that is what makes a chat client
render the artifact instead of a link. The bytes are already in the delivery
account — the tool was written when they were stored — so this module reads them
back, with the guards a network call out of the server deserves: a timeout, a
size bound and an image type.

Two things are deliberate. The address is composed from the account's base and a
public id that came out of our own database, never from an argument, so there is
no host to allow-list here. And a failure is never fatal: a tool that cannot
download a picture still answers with the data, because the picture is the bonus
and the row is the answer.
"""

from dataclasses import dataclass

import httpx
import structlog

from app import urls

logger = structlog.get_logger("app.mcp.assets")

# A cold CDN edge on the other side of the world, not a slow database.
TIMEOUT_SECONDS = 15.0

# A render is tens of kilobytes and a generated picture a few hundred. Past this
# the caller gets the URL and no bytes: an answer is not worth megabytes.
MAX_BYTES = 8 * 1024 * 1024

# What FastMCP's ``Image`` calls each type Cloudinary serves. Anything else is
# not a picture this server stored, so it is not handed over.
FORMATS = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/webp": "webp",
    "image/gif": "gif",
}


@dataclass(frozen=True)
class Picture:
    """One asset, in the two facts a content block needs."""

    data: bytes
    format: str


async def fetch(
    public_id: str | None, *, client: httpx.AsyncClient | None = None
) -> Picture | None:
    """Read one published asset, or ``None`` when there is nothing to hand over.

    ``client`` is how a test watches the request without sending it.
    """
    address = urls.asset_url(public_id)
    if address is None:
        return None

    if client is not None:
        return await _read(client, address, public_id=public_id)

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=False) as http:
        return await _read(http, address, public_id=public_id)


async def _read(
    client: httpx.AsyncClient, address: str, *, public_id: str | None
) -> Picture | None:
    try:
        response = await client.get(address)
    except httpx.HTTPError as broke:
        logger.warning("asset could not be fetched", path=public_id, error=str(broke))
        return None

    if response.status_code != 200:
        logger.warning(
            "asset answered with no content", path=public_id, status=response.status_code
        )
        return None

    picture_format = FORMATS.get(_media_type(response))
    if picture_format is None:
        logger.warning("asset is not an image", path=public_id, media_type=_media_type(response))
        return None

    if len(response.content) > MAX_BYTES:
        logger.warning(
            "asset is too large to hand over", path=public_id, size=len(response.content)
        )
        return None

    return Picture(data=response.content, format=picture_format)


def _media_type(response: httpx.Response) -> str:
    """The type without its parameters: ``image/png; charset=x`` is ``image/png``."""
    return response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
