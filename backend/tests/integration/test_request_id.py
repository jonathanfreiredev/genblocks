import pytest

pytestmark = pytest.mark.anyio


async def test_response_includes_a_request_id(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


async def test_inbound_request_id_is_echoed(client):
    response = await client.get("/health", headers={"X-Request-ID": "trace-42"})

    assert response.headers["x-request-id"] == "trace-42"


async def test_invalid_request_id_is_replaced(client):
    response = await client.get("/health", headers={"X-Request-ID": "   "})

    request_id = response.headers["x-request-id"]
    assert request_id
    assert request_id != "   "
