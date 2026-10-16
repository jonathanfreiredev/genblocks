import httpx
import pytest

from app.db.session import get_async_db_session
from app.health import router as health
from app.main import app
from app.settings import settings

pytestmark = pytest.mark.anyio


async def test_liveness_does_not_require_authentication(client):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_reports_the_database_is_up(client):
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


async def test_readiness_reports_unavailable_when_the_database_is_down(client):
    class BrokenSession:
        async def execute(self, *args, **kwargs):
            raise RuntimeError("database is down")

    async def override_broken_session():
        yield BrokenSession()

    app.dependency_overrides[get_async_db_session] = override_broken_session

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down"}


def mcp_probe(monkeypatch, *, status_code: int = 200, error: Exception | None = None) -> list[str]:
    """Stand in for the client the warm-up probe opens, and record what it reached."""
    reached: list[str] = []

    class AnsweringClient:
        def __init__(self, timeout=None) -> None:
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            reached.append(url)

            if error is not None:
                raise error

            return httpx.Response(status_code, request=httpx.Request("GET", url))

    monkeypatch.setattr(health.httpx, "AsyncClient", AnsweringClient)
    return reached


async def test_warmup_reports_both_services_up(client, monkeypatch):
    reached = mcp_probe(monkeypatch)

    response = await client.get("/warmup")

    assert response.status_code == 200
    assert response.json() == {"api": "ok", "mcp": "ok"}
    # The probe is what wakes a slept MCP server, so it has to be the MCP's own
    # liveness path and nothing else.
    assert reached == [f"{settings.mcp_internal_url}/health"]
    # A cached answer would report a service as up long after it went back to sleep.
    assert response.headers["cache-control"] == "no-store"


async def test_warmup_reports_an_mcp_that_has_not_answered_yet(client, monkeypatch):
    # A slept container shows up as a timeout: the platform holds the request
    # instead of refusing it.
    mcp_probe(monkeypatch, error=httpx.ConnectTimeout("the container is starting"))

    response = await client.get("/warmup")

    assert response.status_code == 200
    assert response.json() == {"api": "ok", "mcp": "waking"}


async def test_warmup_reports_an_mcp_that_answered_with_a_failure(client, monkeypatch):
    # The first request to a slept service can come back as a 502 from the edge.
    mcp_probe(monkeypatch, status_code=502)

    response = await client.get("/warmup")

    assert response.status_code == 200
    assert response.json() == {"api": "ok", "mcp": "waking"}
