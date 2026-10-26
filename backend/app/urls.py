"""The absolute addresses the vault publishes.

An asset is stored as a public id on purpose (PLAN.md, decision 11): the bytes are
kept untransformed and the delivery host stays the deployment's business. These
helpers are the one place an id becomes something a client can open, so the API,
the operator screens and the MCP server cannot spell the same address differently.

Two settings decide them. ``ASSET_BASE_URL`` is the public delivery base of the
storage account — public on purpose, since it signs nothing, which is what lets
the MCP process publish image addresses without holding the account's
credentials; it ships set, and a deployment points it elsewhere or empties it.
``FRONTEND_URL`` is the site a person opens. With no asset base the field comes
back null rather than as a link that 404s.
"""

import uuid

from app.settings import settings


def asset_url(public_id: str | None) -> str | None:
    """The URL a client reads an asset from, or ``None`` when none is published."""
    if not public_id or not settings.asset_base_url:
        return None

    return f"{settings.asset_base_url.rstrip('/')}/{public_id.lstrip('/')}"


def component_page_url(slug: str) -> str:
    """The item page of a block: what a person opens to see it and run it."""
    return f"{_site()}/blocks/{slug}"


def image_page_url(slug: str) -> str:
    """The item page of a picture."""
    return f"{_site()}/images/{slug}"


def task_page_url(task_id: uuid.UUID) -> str:
    """The owner's task page: the checklist while it runs, the result after."""
    return f"{_site()}/tasks/{task_id}"


def _site() -> str:
    return settings.frontend_url.rstrip("/")
