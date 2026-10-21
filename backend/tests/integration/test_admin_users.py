"""A manual ban is a login decision, not a content decision."""

import pytest

from app.settings import settings
from tests.auth_stub import mint_token
from tests.helpers import auth_header

pytestmark = pytest.mark.anyio


async def _me(client, token: str) -> dict:
    response = await client.get("/v1/users/me", headers=auth_header(token))
    assert response.status_code == 200
    return response.json()


async def test_an_operator_can_ban_and_unban_a_user(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    target_token = mint_token(email="target@example.com")
    target = await _me(client, target_token)
    operator_token = mint_token(email="operator@example.com")

    banned = await client.post(
        f"/v1/admin/users/{target['id']}/ban",
        headers=auth_header(operator_token),
        json={"reason": "repeated policy attempts"},
    )

    assert banned.status_code == 200
    assert banned.json()["banned_at"] is not None
    assert banned.json()["ban_reason"] == "repeated policy attempts"
    assert (await client.get("/v1/users/me", headers=auth_header(target_token))).status_code == 403

    found = await client.get(
        "/v1/admin/users",
        headers=auth_header(operator_token),
        params={"search": "target@example.com"},
    )
    assert found.status_code == 200
    assert found.json()[0]["id"] == target["id"]

    unbanned = await client.post(
        f"/v1/admin/users/{target['id']}/unban",
        headers=auth_header(operator_token),
    )
    assert unbanned.status_code == 200
    assert unbanned.json()["banned_at"] is None
    assert (await client.get("/v1/users/me", headers=auth_header(target_token))).status_code == 200


async def test_an_operator_cannot_ban_self_or_another_operator(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com,other@example.com")
    operator_token = mint_token(email="operator@example.com")
    operator = await _me(client, operator_token)
    other_token = mint_token(email="other@example.com")
    other = await _me(client, other_token)

    own = await client.post(
        f"/v1/admin/users/{operator['id']}/ban",
        headers=auth_header(operator_token),
        json={},
    )
    colleague = await client.post(
        f"/v1/admin/users/{other['id']}/ban",
        headers=auth_header(operator_token),
        json={},
    )

    assert own.status_code == 400
    assert colleague.status_code == 400


async def test_a_non_operator_cannot_ban(client, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    target_token = mint_token(email="target@example.com")
    target = await _me(client, target_token)

    response = await client.post(
        f"/v1/admin/users/{target['id']}/ban",
        headers=auth_header(mint_token(email="jane@example.com")),
        json={},
    )

    assert response.status_code == 403
