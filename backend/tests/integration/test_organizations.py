import uuid

import pytest
from sqlalchemy import func, select

from app.organizations.models import Membership
from app.users.models import User
from tests.auth_stub import mint_token
from tests.helpers import auth_header

pytestmark = pytest.mark.anyio


async def _create_organization(client, token: str, name: str = "Acme") -> dict:
    """Create an organization through the API and return the response body."""
    response = await client.post(
        "/v1/organizations", json={"name": name}, headers=auth_header(token)
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _add_member(
    client,
    db_session,
    *,
    organization_id: str,
    token: str,
    email: str,
    role: str = "member",
) -> None:
    """Provision the token's user and add them to the organization.

    Invitations do not exist yet, so a test builds the membership directly, the
    way accepting one eventually would.
    """
    await client.get("/v1/users/me", headers=auth_header(token))
    user = await db_session.scalar(select(User).where(User.email == email))
    db_session.add(
        Membership(user_id=user.id, organization_id=uuid.UUID(organization_id), role=role)
    )
    await db_session.commit()


async def test_organizations_require_authentication(client):
    assert (await client.get("/v1/organizations")).status_code == 401
    assert (await client.post("/v1/organizations", json={"name": "Acme"})).status_code == 401


async def test_creating_an_organization_makes_the_creator_its_owner(client):
    token = mint_token()

    organization = await _create_organization(client, token)

    assert organization["name"] == "Acme"
    assert organization["slug"] == "acme"
    assert organization["role"] == "owner"


async def test_the_owner_is_the_only_member_at_first(client):
    token = mint_token()
    organization = await _create_organization(client, token)

    response = await client.get(
        f"/v1/organizations/{organization['id']}/members", headers=auth_header(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["role"] == "owner"
    # The member's profile comes along, so a client can render a member list
    # without a second request per row.
    assert body["items"][0]["user"]["email"] == "jane@example.com"


async def test_reading_an_organization_returns_the_callers_role(client):
    token = mint_token()
    organization = await _create_organization(client, token)

    response = await client.get(
        f"/v1/organizations/{organization['id']}", headers=auth_header(token)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "owner"


async def test_renaming_an_organization_works_for_the_owner(client):
    token = mint_token()
    organization = await _create_organization(client, token)

    response = await client.patch(
        f"/v1/organizations/{organization['id']}",
        json={"name": "Acme Renamed"},
        headers=auth_header(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Acme Renamed"
    # The slug identifies the organization in URLs, so renaming must not move it.
    assert body["slug"] == organization["slug"]


async def test_renaming_requires_the_owner_role(client, db_session):
    """A member can read the organization but not change it."""
    owner_token = mint_token(email="owner@example.com")
    member_token = mint_token(email="member@example.com")
    organization = await _create_organization(client, owner_token)

    await _add_member(
        client,
        db_session,
        organization_id=organization["id"],
        token=member_token,
        email="member@example.com",
    )

    read = await client.get(
        f"/v1/organizations/{organization['id']}", headers=auth_header(member_token)
    )
    assert read.status_code == 200

    rename = await client.patch(
        f"/v1/organizations/{organization['id']}",
        json={"name": "Hijacked"},
        headers=auth_header(member_token),
    )
    assert rename.status_code == 403


async def test_renaming_is_invisible_to_non_members(client):
    owner_token = mint_token()
    stranger_token = mint_token()
    organization = await _create_organization(client, owner_token)

    response = await client.patch(
        f"/v1/organizations/{organization['id']}",
        json={"name": "Nope"},
        headers=auth_header(stranger_token),
    )

    # A 403 here would confirm that the organization exists.
    assert response.status_code == 404


async def test_renaming_requires_authentication(client):
    response = await client.patch(f"/v1/organizations/{uuid.uuid4()}", json={"name": "Acme"})

    assert response.status_code == 401


async def test_renaming_rejects_an_empty_name(client):
    token = mint_token()
    organization = await _create_organization(client, token)

    response = await client.patch(
        f"/v1/organizations/{organization['id']}",
        json={"name": ""},
        headers=auth_header(token),
    )

    assert response.status_code == 422


async def test_an_organization_is_invisible_to_non_members(client):
    """Tenancy is enforced by the query: a stranger gets a 404, not a 403.

    A 403 would confirm that the organization exists, which leaks the tenant map
    to anyone who can guess an id.
    """
    owner_token = mint_token()
    stranger_token = mint_token()
    organization = await _create_organization(client, owner_token)

    listed = await client.get("/v1/organizations", headers=auth_header(stranger_token))
    assert listed.status_code == 200
    assert listed.json()["total"] == 0

    read = await client.get(
        f"/v1/organizations/{organization['id']}", headers=auth_header(stranger_token)
    )
    assert read.status_code == 404

    members = await client.get(
        f"/v1/organizations/{organization['id']}/members", headers=auth_header(stranger_token)
    )
    assert members.status_code == 404


async def test_an_unknown_organization_is_a_404(client):
    token = mint_token()

    response = await client.get(f"/v1/organizations/{uuid.uuid4()}", headers=auth_header(token))

    assert response.status_code == 404


async def test_members_see_organizations_they_do_not_own(client, db_session):
    owner_token = mint_token(email="owner@example.com")
    member_token = mint_token(email="member@example.com")
    organization = await _create_organization(client, owner_token)

    await _add_member(
        client,
        db_session,
        organization_id=organization["id"],
        token=member_token,
        email="member@example.com",
    )

    response = await client.get("/v1/organizations", headers=auth_header(member_token))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["role"] == "member"


async def test_organizations_with_the_same_name_get_distinct_slugs(client):
    token = mint_token()

    first = await _create_organization(client, token, name="Acme")
    second = await _create_organization(client, token, name="Acme")

    assert first["slug"] == "acme"
    assert second["slug"] == "acme-2"


async def test_organizations_are_paginated(client):
    token = mint_token()
    for name in ("Alpha", "Bravo", "Charlie"):
        await _create_organization(client, token, name=name)

    response = await client.get("/v1/organizations?limit=2", headers=auth_header(token))

    body = response.json()
    assert body["total"] == 3  # total ignores pagination
    assert body["limit"] == 2
    assert len(body["items"]) == 2


async def test_an_unknown_sort_field_is_rejected(client):
    token = mint_token()

    response = await client.get("/v1/organizations?sort=nope", headers=auth_header(token))

    assert response.status_code == 422


async def test_each_list_endpoint_has_its_own_sort_allowlist(client):
    """The members endpoint sorts by its own fields, not by the organization's."""
    token = mint_token()
    organization = await _create_organization(client, token)
    members_url = f"/v1/organizations/{organization['id']}/members"

    rejected = await client.get(f"{members_url}?sort=name", headers=auth_header(token))
    assert rejected.status_code == 422

    accepted = await client.get(f"{members_url}?sort=role", headers=auth_header(token))
    assert accepted.status_code == 200


async def test_an_unknown_query_parameter_is_rejected(client):
    """List parameters are validated together, so a typo is a 422, not ignored."""
    token = mint_token()

    response = await client.get("/v1/organizations?limt=2", headers=auth_header(token))

    assert response.status_code == 422


async def test_an_empty_name_is_rejected(client):
    token = mint_token()

    response = await client.post("/v1/organizations", json={"name": ""}, headers=auth_header(token))

    assert response.status_code == 422


async def test_deleting_a_profile_removes_its_memberships(client, db_session):
    """The foreign key cascades, so a hard delete leaves no dangling rows."""
    token = mint_token()
    await _create_organization(client, token)

    assert (await client.delete("/v1/users/me", headers=auth_header(token))).status_code == 204

    remaining = await db_session.scalar(select(func.count()).select_from(Membership))
    assert remaining == 0
