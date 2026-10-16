import uuid

import pytest

from app.auth.claims import TokenClaims
from app.users.service import _create_user
from tests.auth_stub import mint_token
from tests.helpers import auth_header

pytestmark = pytest.mark.anyio


async def test_me_requires_authentication(client):
    response = await client.get("/v1/users/me")

    assert response.status_code == 401


async def test_me_rejects_an_invalid_token(client):
    response = await client.get("/v1/users/me", headers=auth_header("not-a-jwt"))

    assert response.status_code == 401


async def test_me_provisions_a_profile_from_the_token(client):
    token = mint_token(email="jane@example.com", full_name="Jane Doe")

    response = await client.get("/v1/users/me", headers=auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert body["full_name"] == "Jane Doe"


async def test_provisioning_is_idempotent(client):
    token = mint_token(subject=uuid.uuid4())
    headers = auth_header(token)

    first = await client.get("/v1/users/me", headers=headers)
    second = await client.get("/v1/users/me", headers=headers)

    assert first.status_code == 200
    assert first.json()["id"] == second.json()["id"]


async def test_profile_email_is_kept_in_sync_with_the_token(client):
    subject = uuid.uuid4()

    old_token = mint_token(subject=subject, email="old@example.com")
    new_token = mint_token(subject=subject, email="new@example.com")

    await client.get("/v1/users/me", headers=auth_header(old_token))
    response = await client.get("/v1/users/me", headers=auth_header(new_token))

    assert response.json()["email"] == "new@example.com"


async def test_provisioning_tolerates_a_concurrent_insert(db_session):
    """Two first requests can both miss the lookup and try to insert."""
    subject = uuid.uuid4()
    claims = TokenClaims(subject=subject, email="race@example.com", metadata={})

    first = await _create_user(db_session, claims)
    second = await _create_user(db_session, claims)

    assert first.id == second.id
    assert second.supabase_user_id == subject


async def test_update_profile(client):
    token = mint_token(full_name="Jane Doe")

    response = await client.patch(
        "/v1/users/me",
        json={"full_name": "Jane Smith"},
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Jane Smith"


async def test_delete_profile_requires_authentication(client):
    response = await client.delete("/v1/users/me")

    assert response.status_code == 401


async def test_delete_profile_is_a_hard_delete(client):
    token = mint_token(email="gone@example.com")
    headers = auth_header(token)

    assert (await client.get("/v1/users/me", headers=headers)).status_code == 200
    assert (await client.delete("/v1/users/me", headers=headers)).status_code == 204

    # The Supabase identity is still valid, so the next request provisions a
    # brand new profile for it.
    response = await client.get("/v1/users/me", headers=headers)
    assert response.status_code == 200


async def test_an_email_can_be_reused_after_the_profile_is_deleted(client):
    """Deleting a profile must not block a new identity with the same email."""
    email = "reuse@example.com"

    first = mint_token(email=email)
    await client.get("/v1/users/me", headers=auth_header(first))
    await client.delete("/v1/users/me", headers=auth_header(first))

    # A different Supabase subject signing up with the same email.
    second = mint_token(email=email)
    response = await client.get("/v1/users/me", headers=auth_header(second))

    assert response.status_code == 200
    assert response.json()["email"] == email
