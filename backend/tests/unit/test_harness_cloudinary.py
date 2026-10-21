"""Storing what we make: the signature, the tree it writes in, and the answer.

Cloudinary's signature is a rule rather than a choice, so it is pinned here: the
parameters sorted by name, the secret appended, sha1 over the whole thing. A
change to that order would be an upload the account refuses, and this is where it
should be caught instead.
"""

import uuid

import httpx
import pytest

from app.harness import cloudinary
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
    assert cloudinary.signature(PARAMS, api_secret="secret") == SIGNED


def test_the_signature_does_not_depend_on_the_order_of_the_parameters():
    shuffled = {"timestamp": PARAMS["timestamp"], "public_id": PARAMS["public_id"]}

    assert cloudinary.signature(shuffled, api_secret="secret") == SIGNED


def test_the_signature_changes_with_the_cloud_secret():
    assert cloudinary.signature(PARAMS, api_secret="another") != SIGNED


def test_a_render_is_named_under_the_root_the_code_owns():
    task_id = uuid.UUID("0123456789abcdef0123456789abcdef")

    name = cloudinary.screenshot_id(task_id, 2)

    assert name == "genblocks/screenshots/0123456789ab-2"
    assert name.startswith(f"{cloudinary.ROOT}/")


def test_the_card_crop_sits_beside_the_render_it_came_from():
    task_id = uuid.UUID("0123456789abcdef0123456789abcdef")

    name = cloudinary.thumbnail_id(task_id, 1)

    assert name == f"{cloudinary.screenshot_id(task_id, 1)}-thumb"
    assert name.startswith(f"{cloudinary.ROOT}/")


def test_an_image_is_named_after_its_own_bytes():
    # Content-addressed: the same picture asked for twice is one object in the
    # CDN, and the unique path on the library row is what keeps it one row.
    assert cloudinary.image_id(PNG) == cloudinary.image_id(PNG)
    assert cloudinary.image_id(PNG) != cloudinary.image_id(PNG + b"more")
    assert cloudinary.image_id(PNG).startswith(f"{cloudinary.IMAGES}/")


def test_an_image_is_addressable_where_a_block_can_read_it(account):
    url = cloudinary.delivery_url("genblocks/images/abc123")

    assert url == "https://res.cloudinary.com/genblocks/image/upload/genblocks/images/abc123"


def test_a_deployment_with_no_cloud_cannot_address_anything(monkeypatch):
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)

    with pytest.raises(cloudinary.StorageUnavailable):
        cloudinary.delivery_url("genblocks/images/abc123")


async def test_the_upload_is_signed_with_what_it_sends(account):
    sent: dict = {}
    client = client_for(sent)

    stored = await cloudinary.store(PNG, name=PARAMS["public_id"], client=client)

    assert stored == PARAMS["public_id"]
    assert sent["url"] == "https://api.cloudinary.com/v1_1/genblocks/image/upload"

    body = sent["body"].decode("utf-8", "replace")
    assert "genblocks/screenshots/0123456789ab-1" in body
    assert 'name="api_key"' in body
    # The signature is over the parameters sent, and the secret never travels.
    signature = cloudinary.signature(
        {"public_id": PARAMS["public_id"], "timestamp": _timestamp_in(body)},
        api_secret="secret",
    )
    assert _field_in(body, "signature") == signature
    assert "secret" not in body


async def test_what_an_image_is_sent_as_is_what_it_was_made_as(account):
    sent: dict = {}
    client = client_for(sent)

    await cloudinary.store(PNG, name=PARAMS["public_id"], media_type="image/jpeg", client=client)

    # The filename carries the extension, and the part's content type is the one
    # the bytes actually are: Cloudinary reads the part, not a guess of ours.
    assert "asset.jpeg" in sent["body"].decode("utf-8", "replace")
    assert b"image/jpeg" in sent["body"]


async def test_a_cloud_that_refuses_the_write_is_not_a_stored_asset(account):
    client = client_for({}, answer={"error": {"message": "Unknown API key"}}, status=401)

    with pytest.raises(cloudinary.StorageUnavailable) as refused:
        await cloudinary.store(PNG, name=PARAMS["public_id"], client=client)

    assert "401" in str(refused.value)


async def test_an_answer_with_no_public_id_is_a_failure(account):
    client = client_for({}, answer={"secure_url": "https://example.test/render.png"})

    with pytest.raises(cloudinary.StorageUnavailable):
        await cloudinary.store(PNG, name=PARAMS["public_id"], client=client)


async def test_a_deployment_with_no_cloud_says_what_to_configure(monkeypatch):
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)

    with pytest.raises(cloudinary.StorageUnavailable) as refused:
        await cloudinary.store(PNG, name=PARAMS["public_id"])

    assert "CLOUDINARY_CLOUD_NAME" in str(refused.value)


async def test_a_delete_can_purge_the_delivery_cache(account):
    sent: dict = {}

    async def handle(request: httpx.Request) -> httpx.Response:
        sent["body"] = request.read().decode()
        return httpx.Response(200, json={"result": "ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))

    await cloudinary.destroy(PARAMS["public_id"], invalidate=True, client=client)

    body = sent["body"]
    assert "invalidate=true" in body
    assert "public_id=genblocks%2Fscreenshots%2F0123456789ab-1" in body


async def test_a_missing_cloudinary_asset_is_still_deleted(account):
    async def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": "not found"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))

    await cloudinary.destroy(PARAMS["public_id"], client=client)


def _timestamp_in(body: str) -> str:
    return _field_in(body, "timestamp")


def _field_in(body: str, field: str) -> str:
    """One multipart field's value, read off the encoded body."""
    marker = f'name="{field}"'
    _, _, rest = body.partition(marker)
    _, _, value = rest.partition("\r\n\r\n")

    return value.split("\r\n", 1)[0]
