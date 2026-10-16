from collections.abc import AsyncIterator
from typing import Annotated

import pytest
from fastapi import FastAPI, HTTPException, Query
from httpx import ASGITransport, AsyncClient
from sqlalchemy import column

from app.pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    OffsetPage,
    PaginationParams,
    SortParams,
)

pytestmark = pytest.mark.anyio

# Plain columns are enough to exercise the sorting logic without an ORM model.
ALLOWED_SORTS = {
    "created_at": column("created_at"),
    "name": column("name"),
    "id": column("id"),
}


def resolve_order_by(sort: str | None) -> list[str]:
    return [
        str(clause)
        for clause in SortParams(sort=sort).order_by(
            ALLOWED_SORTS, default="-created_at", tiebreaker=ALLOWED_SORTS["id"]
        )
    ]


def test_default_sort_is_used_when_absent():
    assert resolve_order_by(None) == ["created_at DESC", "id DESC"]


def test_sorts_ascending_by_default():
    assert resolve_order_by("name") == ["name ASC", "id ASC"]


def test_leading_minus_sorts_descending():
    assert resolve_order_by("-name") == ["name DESC", "id DESC"]


def test_multiple_fields_append_the_tiebreaker_in_the_primary_direction():
    assert resolve_order_by("name,-created_at") == ["name ASC", "created_at DESC", "id ASC"]


def test_duplicate_fields_are_ignored():
    assert resolve_order_by("name,name") == ["name ASC", "id ASC"]


def test_unknown_field_is_rejected():
    with pytest.raises(HTTPException) as error:
        resolve_order_by("password")

    assert error.value.status_code == 422


def test_empty_sort_is_rejected():
    with pytest.raises(HTTPException) as error:
        resolve_order_by("  ,  ")

    assert error.value.status_code == 422


def _params_app() -> FastAPI:
    app = FastAPI()

    @app.get("/items")
    async def list_items(page: Annotated[PaginationParams, Query()]) -> OffsetPage[int]:
        return OffsetPage[int](items=[], total=0, limit=page.limit, offset=page.offset)

    @app.get("/sorted")
    async def list_sorted(sort: Annotated[SortParams, Query()]) -> list[str]:
        clauses = sort.order_by(
            ALLOWED_SORTS, default="-created_at", tiebreaker=ALLOWED_SORTS["id"]
        )
        return [str(clause) for clause in clauses]

    return app


@pytest.fixture
async def params_client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=_params_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_pagination_uses_the_defaults(params_client: AsyncClient):
    response = await params_client.get("/items")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": DEFAULT_LIMIT, "offset": 0}


async def test_pagination_accepts_valid_values(params_client: AsyncClient):
    response = await params_client.get("/items?limit=5&offset=10")

    assert response.status_code == 200
    assert response.json()["limit"] == 5
    assert response.json()["offset"] == 10


@pytest.mark.parametrize("query", ["limit=0", f"limit={MAX_LIMIT + 1}", "offset=-1"])
async def test_pagination_rejects_invalid_values(params_client: AsyncClient, query: str):
    response = await params_client.get(f"/items?{query}")

    assert response.status_code == 422


async def test_sort_is_resolved_from_the_query_string(params_client: AsyncClient):
    response = await params_client.get("/sorted?sort=-name")

    assert response.status_code == 200
    assert response.json() == ["name DESC", "id DESC"]


async def test_sort_query_rejects_unknown_fields(params_client: AsyncClient):
    response = await params_client.get("/sorted?sort=password")

    assert response.status_code == 422
