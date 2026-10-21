from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.body_limit import MAX_BODY_BYTES, BodyLimitMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodyLimitMiddleware)

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    return app


def test_a_normal_json_body_reaches_the_route():
    response = TestClient(_app()).post("/echo", json={"brief": "a pricing table"})

    assert response.status_code == 200
    assert response.json() == {"brief": "a pricing table"}


def test_a_body_over_the_transport_bound_is_refused_before_parsing():
    response = TestClient(_app()).post(
        "/echo",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert str(MAX_BODY_BYTES) in response.json()["detail"]
