"""Asking BFL for a picture, and keeping it.

The provider's flow is asynchronous — queue, poll, download — and the picture
arrives at a signed URL that expires, so what is tested here is the shape of the
two calls and the promise that no BFL address is ever what we keep.
"""

import httpx
import pytest

from app.harness import cloudinary, images
from app.settings import settings

pytestmark = pytest.mark.anyio

PROMPT = "A wide photograph of an empty road at dawn"
SAMPLE = "https://delivery.bfl.ai/region/sample.jpg?signature=abc"
PICTURE = b"\xff\xd8\xff\xe0jpeg-bytes"


@pytest.fixture
def key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "bfl_api_key", "bfl-test")
    monkeypatch.setattr(settings, "bfl_base_url", "https://api.bfl.ai/v1")
    monkeypatch.setattr(settings, "image_model", "flux-2-pro")


@pytest.fixture
def stored(monkeypatch) -> list[dict]:
    """Cloudinary, answered without an account: what it was handed is kept."""
    kept: list[dict] = []

    async def store(data: bytes, *, name: str, media_type: str = "image/png", client=None) -> str:
        kept.append({"data": data, "name": name, "media_type": media_type})

        return name

    monkeypatch.setattr(cloudinary, "store", store)
    monkeypatch.setattr(
        cloudinary, "delivery_url", lambda public_id: f"https://cdn.test/{public_id}"
    )

    return kept


def client_for(sent: dict, *, statuses: list[str] | None = None) -> httpx.AsyncClient:
    """A client that queues a request, answers the poll, and serves the picture."""
    left = list(statuses or ["Ready"])

    async def handle(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            sent["queued"] = request.content.decode()
            sent["headers"] = dict(request.headers)

            return httpx.Response(
                200,
                json={"id": "req-1", "polling_url": "https://api.bfl.ai/v1/get_result?id=req-1"},
            )

        if "get_result" in str(request.url):
            sent.setdefault("polls", 0)
            sent["polls"] += 1
            status = left.pop(0) if len(left) > 1 else left[0]

            if status == "Ready":
                return httpx.Response(200, json={"status": "Ready", "result": {"sample": SAMPLE}})

            return httpx.Response(200, json={"status": status})

        sent["downloaded"] = str(request.url)

        return httpx.Response(200, content=PICTURE, headers={"content-type": "image/jpeg"})

    return httpx.AsyncClient(transport=httpx.MockTransport(handle))


def test_a_size_the_api_cannot_make_is_refused_before_it_is_asked_for():
    assert images.size_complaint(1024, 768) is None
    assert "multiple of 32" in (images.size_complaint(1000, 768) or "")
    assert "between" in (images.size_complaint(128, 768) or "")
    assert "between" in (images.size_complaint(4096, 768) or "")


async def test_a_picture_is_queued_with_the_prompt_and_the_size(key, stored):
    sent: dict = {}

    made = await images.generate(prompt=PROMPT, width=1024, height=768, client=client_for(sent))

    assert sent["headers"]["x-key"] == "bfl-test"
    assert PROMPT in sent["queued"]
    assert '"width":1024' in sent["queued"]
    # What comes back is ours: the signed URL is read once and never kept.
    assert sent["downloaded"] == SAMPLE
    assert made.url.startswith("https://cdn.test/genblocks/images/")
    assert SAMPLE not in made.url
    assert made.data == PICTURE
    assert made.media_type == "image/jpeg"


async def test_the_picture_is_stored_as_the_bytes_it_arrived_as(key, stored):
    await images.generate(prompt=PROMPT, width=512, height=512, client=client_for({}))

    assert stored[0]["data"] == PICTURE
    assert stored[0]["media_type"] == "image/jpeg"
    assert stored[0]["name"].startswith("genblocks/images/")


async def test_a_request_is_waited_for_rather_than_guessed(key, stored):
    sent: dict = {}

    await images.generate(
        prompt=PROMPT,
        width=512,
        height=512,
        client=client_for(sent, statuses=["Pending", "Pending", "Ready"]),
    )

    assert sent["polls"] == 3


async def test_a_picture_that_never_arrives_is_a_failure(key, stored, monkeypatch):
    monkeypatch.setattr(images, "GENERATION_TIMEOUT_SECONDS", 0.0)
    monkeypatch.setattr(images, "POLL_SECONDS", 0.0)

    with pytest.raises(images.ImagesUnavailable) as refused:
        await images.generate(
            prompt=PROMPT, width=512, height=512, client=client_for({}, statuses=["Pending"])
        )

    assert "did not finish" in str(refused.value)


async def test_a_refused_generation_says_what_happened(key, stored):
    with pytest.raises(images.ImagesUnavailable) as refused:
        await images.generate(
            prompt=PROMPT, width=512, height=512, client=client_for({}, statuses=["Error"])
        )

    assert "Error" in str(refused.value)


async def test_a_size_the_api_cannot_make_never_reaches_the_provider(key, stored):
    sent: dict = {}

    with pytest.raises(images.ImagesUnavailable):
        await images.generate(prompt=PROMPT, width=1000, height=768, client=client_for(sent))

    assert "queued" not in sent


async def test_no_credits_is_said_in_those_words(monkeypatch, stored):
    monkeypatch.setattr(settings, "bfl_api_key", "bfl-test")

    async def paywall(request: httpx.Request) -> httpx.Response:
        return httpx.Response(402, json={"detail": "no credits"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(paywall))

    with pytest.raises(images.ImagesUnavailable) as refused:
        await images.generate(prompt=PROMPT, width=512, height=512, client=client)

    assert "credits" in str(refused.value)


async def test_a_deployment_with_no_key_says_what_to_configure(monkeypatch, stored):
    monkeypatch.setattr(settings, "bfl_api_key", None)

    with pytest.raises(images.ImagesUnavailable) as refused:
        await images.generate(prompt=PROMPT, width=512, height=512)

    assert "BFL_API_KEY" in str(refused.value)
