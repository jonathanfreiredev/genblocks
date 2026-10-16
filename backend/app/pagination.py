"""List conventions: offset pagination and sorting.

List endpoints paginate with ``limit``/``offset`` and return an ``OffsetPage``
envelope. Ordering goes through a per-endpoint allowlist, so a client can never
sort by an arbitrary column.

The parameter objects are Pydantic models; a list endpoint receives them with
``Annotated[ListParams, Query()]``. FastAPI expands a single model into query
parameters but only handles one per endpoint — given two, it treats each as a
scalar and rejects every request — so pagination and sorting are combined in
``ListParams``.

Keyset (cursor) pagination is the documented alternative for large, high-churn
feeds; it is not implemented here because there is no collection endpoint yet.
See the "Pagination and sorting" section of the README.
"""

from collections.abc import Mapping

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ColumnElement

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PaginationParams(BaseModel):
    """Validated ``limit``/``offset`` query parameters for a list endpoint."""

    limit: int = Field(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(0, ge=0)


class OffsetPage[T](BaseModel):
    """Response envelope for an offset-paginated list.

    ``total`` is the number of rows matching the filters, ignoring pagination,
    so a client can render "page X of Y". It costs an extra ``COUNT`` query.
    """

    items: list[T]
    total: int
    limit: int
    offset: int


class SortParams(BaseModel):
    """The ``sort`` query parameter, resolved into ``ORDER BY`` clauses.

    The syntax is a comma-separated list of fields where a leading ``-`` means
    descending, e.g. ``?sort=-created_at,name``.
    """

    sort: str | None = None

    def order_by(
        self,
        allowed: Mapping[str, ColumnElement],
        *,
        default: str,
        tiebreaker: ColumnElement,
    ) -> list[ColumnElement]:
        """Return the clauses to pass to ``select(...).order_by(...)``.

        ``allowed`` maps each client-visible field to a column; an unknown field
        is rejected with a 422. A unique ``tiebreaker`` is always appended so the
        order is total and rows cannot repeat or disappear between pages.
        """
        specs = _parse_sort(default if self.sort is None else self.sort, allowed)
        if not specs:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="The sort parameter must name at least one field.",
            )

        clauses: list[ColumnElement] = [
            allowed[name].desc() if descending else allowed[name].asc()
            for name, descending in specs
        ]

        # The tiebreaker follows the primary direction: ORDER BY x DESC, id DESC.
        primary_descending = specs[0][1]
        clauses.append(tiebreaker.desc() if primary_descending else tiebreaker.asc())
        return clauses


class ListParams(PaginationParams, SortParams):
    """The query parameters a list endpoint accepts, as one model.

    Pagination and sorting are kept as separate classes because they are separate
    concerns, but FastAPI expands only one model per endpoint, so endpoints take
    this combination: ``Annotated[ListParams, Query()]``.

    Unknown query parameters are rejected instead of silently ignored, so a typo
    like ``?limt=2`` is a 422 rather than a surprise page size.
    """

    model_config = ConfigDict(extra="forbid")


def _parse_sort(raw: str, allowed: Mapping[str, ColumnElement]) -> list[tuple[str, bool]]:
    """Parse ``-field,field`` into ``(field, descending)`` pairs, deduplicated."""
    specs: list[tuple[str, bool]] = []
    seen: set[str] = set()

    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue

        descending = token.startswith("-")
        name = token[1:] if descending else token
        if name not in allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Unknown sort field: {name!r}",
            )

        if name in seen:
            continue
        seen.add(name)
        specs.append((name, descending))

    return specs
