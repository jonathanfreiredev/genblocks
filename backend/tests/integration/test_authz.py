"""The REST door admits only first-party tokens.

An access token carrying a ``client_id`` was issued to an OAuth client — an AI
agent — and belongs to the MCP door. Accepting it here would let an agent call
the API directly and skip the tool policies.
"""

import pytest

from tests.auth_stub import mint_token
from tests.helpers import auth_header

pytestmark = pytest.mark.anyio


async def test_a_first_party_token_still_works(client):
    response = await client.get("/v1/users/me", headers=auth_header(mint_token()))

    assert response.status_code == 200


async def test_an_agent_token_cannot_reach_the_profile(client):
    token = mint_token(client_id="some-oauth-client-id")

    response = await client.get("/v1/users/me", headers=auth_header(token))

    assert response.status_code == 403


async def test_an_agent_token_cannot_reach_the_organizations(client):
    token = mint_token(client_id="some-oauth-client-id")
    headers = auth_header(token)

    listed = await client.get("/v1/organizations", headers=headers)
    created = await client.post("/v1/organizations", json={"name": "Acme"}, headers=headers)

    assert listed.status_code == 403
    assert created.status_code == 403
