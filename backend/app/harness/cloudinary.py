"""Storing what we generate in Cloudinary.

Two trees of one account: the renders of blocks (``genblocks/screenshots``) and the
stock images (``genblocks/images``). Both are writes into somebody else's account,
so both are signed with the API secret, and what comes back is kept as a public id
rather than a URL — the transform belongs to whoever renders it (PLAN.md, decision
11).

Every id is built here, under the ``genblocks/`` root this module owns: there is no
way to write outside that tree from this code.
"""

import hashlib
import time
import uuid

import httpx

from app.settings import settings

# The root the code owns, from the plan's folder tree. Nothing writes beside it.
ROOT = "genblocks"
SCREENSHOTS = f"{ROOT}/screenshots"
IMAGES = f"{ROOT}/images"

# A render is a few hundred kilobytes over a link we do not control. This bounds
# the upload only; the sandbox has its own bound.
UPLOAD_TIMEOUT_SECONDS = 60.0

# How much of a content hash names an image. Content-addressed on purpose: the
# same picture asked for twice is the same object in the CDN, and the unique path
# on the row is what keeps it from becoming two rows.
IMAGE_ID_LENGTH = 16


class StorageUnavailable(Exception):
    """There is no cloud to store in, or it refused the write."""


def screenshot_id(task_id: uuid.UUID, attempt_no: int) -> str:
    """Where one attempt's render lives.

    Named after the task and the attempt rather than the block: the block's slug
    is only decided at commit, and a render's name should not change once it
    exists.
    """
    return f"{SCREENSHOTS}/{task_id.hex[:12]}-{attempt_no}"


def thumbnail_id(task_id: uuid.UUID, attempt_no: int) -> str:
    """Where the catalogue crop of the same attempt lives."""
    return f"{screenshot_id(task_id, attempt_no)}-thumb"


def image_id(data: bytes) -> str:
    """Where one generated image lives: named after its own bytes."""
    return f"{IMAGES}/{hashlib.sha256(data).hexdigest()[:IMAGE_ID_LENGTH]}"


def delivery_url(public_id: str) -> str:
    """The URL a browser reads an asset from.

    A block is served from somebody else's page, so it needs an address rather
    than an id. No transformation is added here on purpose: dynamic Cloudinary
    transformations consume the plan's transformation credits, and a block copied
    a thousand times would make that somebody else's bill. The stored bytes are
    already the size and format the library decided to keep.
    """
    return f"https://res.cloudinary.com/{_account()}/image/upload/{public_id}"


def signature(params: dict[str, str], *, api_secret: str) -> str:
    """Cloudinary's signature: the parameters in order, then the secret.

    Their rule, not a choice of ours: sorted by name, joined with ``&``, the
    secret appended, sha1 over the whole thing. The parameters signed are the
    ones sent, minus the API key and the file itself.
    """
    to_sign = "&".join(f"{key}={params[key]}" for key in sorted(params))
    return hashlib.sha1(f"{to_sign}{api_secret}".encode()).hexdigest()


async def store(
    data: bytes,
    *,
    name: str,
    media_type: str = "image/png",
    client: httpx.AsyncClient | None = None,
) -> str:
    """Upload one asset and return its public id.

    ``client`` is how a test watches the request without sending it.
    """
    account = _account()

    params = {"public_id": name, "timestamp": str(int(time.time()))}
    fields = {
        **params,
        "api_key": settings.cloudinary_api_key or "",
        "signature": signature(params, api_secret=settings.cloudinary_api_secret or ""),
    }
    url = f"https://api.cloudinary.com/v1_1/{account}/image/upload"

    if client is not None:
        return await _send(client, url, fields, data, media_type=media_type)

    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT_SECONDS) as http:
        return await _send(http, url, fields, data, media_type=media_type)


def _account() -> str:
    """The cloud name, or a refusal that says what to configure."""
    if not (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        raise StorageUnavailable(
            "No Cloudinary account is configured, so nothing can be stored: "
            "set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET."
        )

    return settings.cloudinary_cloud_name


async def destroy(
    public_id: str,
    *,
    invalidate: bool = False,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Remove one public asset from the CDN.

    ``invalidate`` asks Cloudinary to purge its delivery cache too. A known URL
    can still survive in a browser or another proxy; this is the strongest purge
    the provider offers.
    """
    account = _account()
    params = {
        "public_id": public_id,
        "timestamp": str(int(time.time())),
        "invalidate": "true" if invalidate else "false",
    }
    fields = {
        **params,
        "api_key": settings.cloudinary_api_key or "",
        "signature": signature(params, api_secret=settings.cloudinary_api_secret or ""),
    }
    url = f"https://api.cloudinary.com/v1_1/{account}/image/destroy"

    if client is not None:
        await _delete(client, url, fields)
        return

    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT_SECONDS) as http:
        await _delete(http, url, fields)


def is_configured() -> bool:
    """Whether this deployment has a Cloudinary account to delete from."""
    return bool(
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )


async def _delete(client: httpx.AsyncClient, url: str, fields: dict[str, str]) -> None:
    response = await client.post(url, data=fields)

    if response.status_code >= 400:
        raise StorageUnavailable(
            f"Cloudinary refused the delete ({response.status_code}): {response.text[:200]}"
        )

    try:
        result = response.json().get("result")
    except ValueError as broke:
        raise StorageUnavailable("Cloudinary answered the delete without JSON.") from broke

    # "not found" is success for a destructive operation: a retry after a partial
    # failure must be able to finish.
    if result not in {"ok", "not found"}:
        raise StorageUnavailable(f"Cloudinary did not delete the asset: {result!r}")


async def _send(
    client: httpx.AsyncClient,
    url: str,
    fields: dict[str, str],
    data: bytes,
    *,
    media_type: str,
) -> str:
    """The upload itself, and the public id out of the answer."""
    extension = media_type.rsplit("/", 1)[-1]
    response = await client.post(
        url,
        data=fields,
        files={"file": (f"asset.{extension}", data, media_type)},
    )

    if response.status_code >= 400:
        raise StorageUnavailable(
            f"Cloudinary refused the upload ({response.status_code}): {response.text[:200]}"
        )

    stored = response.json().get("public_id")
    if not isinstance(stored, str):
        raise StorageUnavailable("Cloudinary answered without a public id.")

    return stored
