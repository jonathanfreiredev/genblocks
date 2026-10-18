"""Storing a render: the signature, the tree it writes in, and the answer.

Cloudinary's signature is a rule rather than a choice, so it is pinned here: the
parameters sorted by name, the secret appended, sha1 over the whole thing. A
change to that order would be an upload the account refuses, and this is where it
should be caught instead.
"""

import uuid

import httpx
import pytest

from app.harness import screenshots
from app.settings import settings

pytestmark = pytest.mark.anyio

# One signature, worked out by hand from Cloudinary's rule.
PARAMS = {"public_id": "genblocks/screenshots/0123456789ab-1", "timestamp": "1700000000"}
SIGNED = "ec86040d7bc8fded028d73d655916616f9f7e761"

PNG = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def account(monkeypatch) -> None:
    """A configured cloud, so the upload gets as far as the request."""
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "genblocks")
    monkeypatch.setattr(settings, "cloudinary_api_key", "key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "secret")


def client_for(sent: dict, *, answer: dict | None = None, status: int = 200) -> httpx.AsyncClient:
    """A client that answers one upload, and remembers what it was sent."""

    async def handle(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["body"] = request.content

        return httpx.Response(
            status, json=answer if answer is not None else {"public_id": PARAMS["public_id"]}
        )

    return httpx.AsyncClient(transport=httpx.MockTransport(handle))


def test_the_signature_is_cloudinary_rules():
    assert screenshots.signature(PARAMS, api_secret="secret") == SIGNED


def test_the_signature_does_not_depend_on_the_order_of_the_parameters():
    shuffled = {"timestamp": PARAMS["timestamp"], "public_id": PARAMS["public_id"]}

    assert screenshots.signature(shuffled, api_secret="secret") == SIGNED


def test_the_signature_changes_with_the_cloud_secret():
    assert screenshots.signature(PARAMS, api_secret="another") != SIGNED


def test_a_render_is_named_under_the_root_the_code_owns():
    task_id = uuid.UUID("0123456789abcdef0123456789abcdef")

    name = screenshots.public_id(task_id, 2)

    assert name == "genblocks/screenshots/0123456789ab-2"
    assert name.startswith(f"{screenshots.ROOT}/")


async def test_the_upload_is_signed_with_what_it_sends(account):
    sent: dict = {}
    client = client_for(sent)

    stored = await screenshots.store(PNG, name=PARAMS["public_id"], client=client)

    assert stored == PARAMS["public_id"]
    assert sent["url"] == "https://api.cloudinary.com/v1_1/genblocks/image/upload"

    body = sent["body"].decode("utf-8", "replace")
    assert "genblocks/screenshots/0123456789ab-1" in body
    assert 'name="api_key"' in body
    # The signature is over the parameters sent, and the secret never travels.
    signature = screenshots.signature(
        {"public_id": PARAMS["public_id"], "timestamp": _timestamp_in(body)},
        api_secret="secret",
    )
    assert _field_in(body, "signature") == signature
    assert "secret" not in body


async def test_a_cloud_that_refuses_the_write_is_not_a_stored_render(account):
    client = client_for({}, answer={"error": {"message": "Unknown API key"}}, status=401)

    with pytest.raises(screenshots.ScreenshotsUnavailable) as refused:
        await screenshots.store(PNG, name=PARAMS["public_id"], client=client)

    assert "401" in str(refused.value)


async def test_an_answer_with_no_public_id_is_a_failure(account):
    client = client_for({}, answer={"secure_url": "https://example.test/render.png"})

    with pytest.raises(screenshots.ScreenshotsUnavailable):
        await screenshots.store(PNG, name=PARAMS["public_id"], client=client)


async def test_a_deployment_with_no_cloud_says_what_to_configure(monkeypatch):
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)

    with pytest.raises(screenshots.ScreenshotsUnavailable) as refused:
        await screenshots.store(PNG, name=PARAMS["public_id"])

    assert "CLOUDINARY_CLOUD_NAME" in str(refused.value)


def _timestamp_in(body: str) -> str:
    return _field_in(body, "timestamp")


def _field_in(body: str, field: str) -> str:
    """One multipart field's value, read off the encoded body."""
    marker = f'name="{field}"'
    _, _, rest = body.partition(marker)
    _, _, value = rest.partition("\r\n\r\n")

    return value.split("\r\n", 1)[0]
