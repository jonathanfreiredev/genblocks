import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db_session
from app.settings import settings

logger = logging.getLogger(__name__)

health_router = APIRouter(tags=["health"])

# How long the warm-up probe waits for the MCP server before calling it not up yet.
# Deliberately shorter than the boot of a slept container: the caller is polling, so
# giving up early costs nothing and the next round arrives long before that boot
# would have finished.
MCP_PROBE_TIMEOUT_SECONDS = 8.0


@health_router.get("/health", summary="Liveness probe")
async def liveness() -> dict[str, str]:
    """Report that the process is running.

    Checks nothing external on purpose: if this fails, the orchestrator should
    restart the container, not merely stop routing traffic to it.
    """
    return {"status": "ok"}


@health_router.get("/health/ready", summary="Readiness probe")
async def readiness(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> dict[str, str]:
    """Report whether the service can serve traffic (the database is reachable)."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        # Probes run frequently, so log at debug to avoid flooding when the
        # database is down. The 503 response is the signal itself.
        logger.debug("Readiness check failed", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}

    return {"status": "ok", "database": "up"}


@health_router.get("/warmup", summary="Wake the demo and report what is up")
async def warmup(response: Response) -> dict[str, str]:
    """Bring the demo's two services up, and say which of them answered.

    The playground's page calls this the moment it is opened. On a platform that
    sleeps an idle service, that moves the wait for a cold container to while the
    visitor is still reading, instead of to the moment they press a button.

    It answers 200 either way, and always with a body: the caller polls it, and a
    status code meaning "not yet" would tell it no more than ``mcp`` does. Nothing
    here needs a token, and probing the MCP is the only work it does, so a wake-up
    never touches the database.
    """
    response.headers["Cache-Control"] = "no-store"

    return {"api": "ok", "mcp": "ok" if await _mcp_answers() else "waking"}


async def _mcp_answers() -> bool:
    """Whether the MCP server answers right now, waking it as a side effect.

    A slept service does not refuse the connection: the platform holds the request
    until the container is up, so a slow one shows up here as a timeout. That is the
    same answer — not up yet — and the request has done its waking either way.
    """
    probe = f"{settings.mcp_internal_url.rstrip('/')}/health"

    try:
        async with httpx.AsyncClient(timeout=MCP_PROBE_TIMEOUT_SECONDS) as client:
            answer = await client.get(probe)
    except httpx.HTTPError:
        logger.debug("The MCP server did not answer the warm-up probe", exc_info=True)
        return False

    return answer.status_code == status.HTTP_200_OK
