"""The stock image library: asking BFL for a picture, and keeping it.

The API is asynchronous — a request is queued and answered with a polling URL, and
the sample it finally returns is a signed URL that expires in ten minutes and is
not meant to be served to anybody. So every image is downloaded here, and what
travels on is a public id of ours; no BFL URL is ever stored or handed to a block.

What this module does **not** do is write a row or put the bytes in a public CDN.
The library's rows belong to the runner (``app.tasks.runner``), which holds a
session; what comes back from here is everything a row needs, plus the bytes. The
runner moderates and scores the picture first, and only then uploads it. A
picture that should not exist never gets an address that could be served.
"""

import asyncio
from dataclasses import dataclass

import httpx

from app.harness import cloudinary
from app.harness.network import UnsafeProviderUrl, checked_provider_url
from app.images.sanitize import ImageRefused, sanitize_image
from app.moderation import service as moderation
from app.settings import settings

# The statuses BFL reports while a task is alive, and the ones that mean it is not
# coming back. Anything else is still working.
READY = "Ready"
FAILED = ("Error", "Failed", "Content Moderated", "Request Moderated")

# The sizes the API accepts, and how it rounds. Enforced here rather than at the
# provider: a request with a side that cannot be generated is a call, and a call
# that fails late is a turn the agent pays for twice.
SIZE_STEP = 32
MIN_SIDE = 256
MAX_SIDE = 1536

# How long one generation may take, how often it is asked about, and how long the
# download of the finished picture may take.
POLL_SECONDS = 1.0
GENERATION_TIMEOUT_SECONDS = 120.0
DOWNLOAD_TIMEOUT_SECONDS = 60.0

DEFAULT_MEDIA_TYPE = "image/jpeg"


class ImagesUnavailable(Exception):
    """The library cannot make a picture: no key, no credits, or nobody answered."""


class ImagesRefused(Exception):
    """The picture was made, and the safety gate refused it."""


@dataclass(frozen=True)
class Generated:
    """One picture, ready to be a row and to be referenced by a block."""

    prompt: str
    # Cloudinary public id, and the URL a block puts in its markup.
    path: str
    url: str
    width: int
    height: int
    media_type: str
    # The bytes, kept so the judge scores what was actually made.
    data: bytes
    # The safety gate ran here, before storage, and cleared the bytes. The runner
    # does not pay for the same check twice.
    screened: bool = False


def size_complaint(width: int, height: int) -> str | None:
    """Why a size cannot be generated, or ``None`` when it can.

    A separate question from :func:`generate` so the tool can answer it without
    spending a call, and say what to ask for instead.
    """
    for side, name in ((width, "width"), (height, "height")):
        if side % SIZE_STEP:
            return f"{name} must be a multiple of {SIZE_STEP} (asked for {side})."
        if not MIN_SIDE <= side <= MAX_SIDE:
            return f"{name} must be between {MIN_SIDE} and {MAX_SIDE} (asked for {side})."

    return None


async def generate(
    *,
    prompt: str,
    width: int,
    height: int,
    client: httpx.AsyncClient | None = None,
) -> Generated:
    """Generate one image, store it, and return what it is.

    ``client`` is how a test answers without a provider or a cloud.
    """
    if complaint := size_complaint(width, height):
        raise ImagesUnavailable(complaint)

    if client is not None:
        return await _generate(client, prompt=prompt, width=width, height=height)

    async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT_SECONDS) as http:
        return await _generate(http, prompt=prompt, width=width, height=height)


async def _generate(
    client: httpx.AsyncClient,
    *,
    prompt: str,
    width: int,
    height: int,
) -> Generated:
    key = _key()
    asked = await client.post(
        f"{settings.bfl_base_url.rstrip('/')}/{settings.image_model}",
        headers={"x-key": key, "accept": "application/json"},
        json={"prompt": prompt, "width": width, "height": height},
    )
    if asked.status_code >= 400:
        raise ImagesUnavailable(_refused(asked))

    queued = asked.json()
    try:
        polling_url = checked_provider_url(
            queued.get("polling_url"),
            hosts=settings.bfl_polling_hosts,
            what="polling",
        )
    except UnsafeProviderUrl as refused:
        raise ImagesUnavailable(str(refused)) from refused

    sample = await _poll(client, key=key, polling_url=polling_url)
    try:
        sample = checked_provider_url(
            sample,
            hosts=settings.bfl_asset_host_list,
            what="sample",
        )
    except UnsafeProviderUrl as refused:
        raise ImagesUnavailable(str(refused)) from refused

    picture = await client.get(sample)
    if picture.status_code >= 400:
        raise ImagesUnavailable(
            f"The finished image could not be downloaded ({picture.status_code})."
        )

    data = picture.content
    media_type = picture.headers.get("content-type", DEFAULT_MEDIA_TYPE).split(";")[0]

    # Decode and re-encode before moderation. The classifier should see the
    # picture the registry would serve, and the CDN should only ever receive
    # bytes with no camera metadata, location or provider container quirks.
    try:
        clean = sanitize_image(data, media_type=media_type)
    except ImageRefused as refused:
        raise ImagesRefused(f"The picture could not be stored safely — {refused}") from refused

    data = clean.data
    media_type = clean.media_type
    width = clean.width
    height = clean.height

    # Safety before storage. A picture that should not exist never gets a public
    # address, and a picture that passes can be used in the next render because it
    # already has one.
    why = await moderation.image_refusal(data, media_type=media_type)
    if why is not None:
        raise ImagesRefused(why)

    path = await cloudinary.store(data, name=cloudinary.image_id(data), media_type=media_type)

    return Generated(
        prompt=prompt,
        path=path,
        url=cloudinary.delivery_url(path),
        width=width,
        height=height,
        media_type=media_type,
        data=data,
        screened=True,
    )


async def _poll(client: httpx.AsyncClient, *, key: str, polling_url: str) -> str:
    """Wait for the queued request, and return the URL of the finished picture."""
    deadline = asyncio.get_running_loop().time() + GENERATION_TIMEOUT_SECONDS

    while True:
        answer = await client.get(polling_url, headers={"x-key": key, "accept": "application/json"})
        if answer.status_code >= 400:
            raise ImagesUnavailable(_refused(answer))

        said = answer.json()
        status = said.get("status")
        if status == READY:
            return said["result"]["sample"]

        if status in FAILED:
            raise ImagesUnavailable(f"The image was refused while generating: {status}.")

        if asyncio.get_running_loop().time() > deadline:
            raise ImagesUnavailable(
                f"The image did not finish within {GENERATION_TIMEOUT_SECONDS:.0f} seconds."
            )

        await asyncio.sleep(POLL_SECONDS)


def _key() -> str:
    """The BFL key, or a refusal that says what to configure."""
    if not settings.bfl_api_key:
        raise ImagesUnavailable(
            "The image library has no key configured: set BFL_API_KEY on the API."
        )

    return settings.bfl_api_key


def _refused(answer: httpx.Response) -> str:
    """What BFL said, in the words that matter (credits and rate limits included)."""
    if answer.status_code == 402:
        return "BFL has no credits left (402)."

    if answer.status_code == 429:
        return "BFL is at its limit of active tasks (429): nothing else can be queued yet."

    return f"BFL refused the request ({answer.status_code}): {answer.text[:200]}"
