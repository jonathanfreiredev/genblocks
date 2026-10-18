"""Storing a render in Cloudinary.

A screenshot is a write into somebody else's account, so the upload is signed
with the API secret, and what comes back is stored as a public id rather than a
URL — the transform belongs to whoever renders it (PLAN.md, decision 11).

Every id is built by :func:`public_id`, under the ``genblocks/`` root this module
owns: there is no way to write outside that tree from here.
"""

import hashlib
import time
import uuid

import httpx

from app.settings import settings

# The root the code owns, from the plan's folder tree. Nothing writes beside it.
ROOT = "genblocks"
SCREENSHOTS = f"{ROOT}/screenshots"

# A render is a few hundred kilobytes over a link we do not control. This bounds
# the upload only; the sandbox has its own bound.
UPLOAD_TIMEOUT_SECONDS = 60.0


class ScreenshotsUnavailable(Exception):
    """There is no cloud to store a render in, or it refused the write."""


def public_id(task_id: uuid.UUID, attempt_no: int) -> str:
    """Where one attempt's render lives.

    Named after the task and the attempt rather than the block: the block's slug
    is only decided at commit, and a render's name should not change once it
    exists.
    """
    return f"{SCREENSHOTS}/{task_id.hex[:12]}-{attempt_no}"


def signature(params: dict[str, str], *, api_secret: str) -> str:
    """Cloudinary's signature: the parameters in order, then the secret.

    Their rule, not a choice of ours: sorted by name, joined with ``&``, the
    secret appended, sha1 over the whole thing. The parameters signed are the
    ones sent, minus the API key and the file itself.
    """
    to_sign = "&".join(f"{key}={params[key]}" for key in sorted(params))
    return hashlib.sha1(f"{to_sign}{api_secret}".encode()).hexdigest()


async def store(
    png: bytes,
    *,
    name: str,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Upload one render and return its public id.

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
        return await _send(client, url, fields, png)

    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT_SECONDS) as http:
        return await _send(http, url, fields, png)


def _account() -> str:
    """The cloud name, or a refusal that says what to configure."""
    if not (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        raise ScreenshotsUnavailable(
            "No Cloudinary account is configured, so a render cannot be stored: "
            "set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET."
        )

    return settings.cloudinary_cloud_name


async def _send(
    client: httpx.AsyncClient,
    url: str,
    fields: dict[str, str],
    png: bytes,
) -> str:
    """The upload itself, and the public id out of the answer."""
    response = await client.post(
        url,
        data=fields,
        files={"file": ("render.png", png, "image/png")},
    )

    if response.status_code >= 400:
        raise ScreenshotsUnavailable(
            f"Cloudinary refused the upload ({response.status_code}): {response.text[:200]}"
        )

    stored = response.json().get("public_id")
    if not isinstance(stored, str):
        raise ScreenshotsUnavailable("Cloudinary answered without a public id.")

    return stored
