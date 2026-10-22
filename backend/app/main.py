import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_v1_router
from app.authz.permissions import PermissionDenied
from app.db.session import async_session_maker
from app.health.router import health_router
from app.logging_config import configure_logging
from app.middleware.body_limit import BodyLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.observability import service as observability
from app.organizations.service import OrganizationSlugConflict
from app.settings import settings
from app.tasks.runner import run_worker
from app.tasks.service import interrupt_orphaned_tasks

# Structured logging for the whole process (app + uvicorn).
configure_logging()

logger = structlog.get_logger("app.main")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Own the task worker in development, and only there.

    In production the queue is drained by a Modal function (see
    ``app/tasks/modal_app.py``): it outlives a request, which a service that
    scales to zero cannot promise a background process, and it does not compete
    with the API for CPU while a block is being built. This process therefore
    claims nothing and reconciles nothing there — a boot that interrupted every
    running task would be interrupting another process's work.

    Locally it keeps the worker it has always had, so the whole loop runs with one
    command. Reconcile-before-claim is what makes a restart safe here: by the time
    this process is looking for work, it is the only thing that could be running
    any. Shutting down cancels the worker mid-flight on purpose. The task it was
    on stays ``running`` and the next boot reconciles it, which is the same path a
    crash takes — one recovery path, exercised on every deploy.
    """
    stop = asyncio.Event()
    worker: asyncio.Task[None] | None = None

    if settings.debug:
        async with async_session_maker() as session:
            interrupted = await interrupt_orphaned_tasks(session)

        if interrupted:
            logger.info("interrupted orphaned tasks", count=interrupted)

        worker = asyncio.create_task(run_worker(stop))

    try:
        yield
    finally:
        if worker is not None:
            stop.set()
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker

        # Whatever the SDK still has buffered goes out now. A task the worker was
        # on is already interrupted and will be reconciled next boot; its trace
        # ends here with what was written, which is the honest half of a cut run.
        observability.shutdown()


app = FastAPI(
    lifespan=lifespan,
    # The schema is useful while developing and a free map of the surface in
    # production. It stays off unless ENV explicitly says development.
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Domain errors carry no HTTP knowledge — the MCP tools call the same code — so
# they are translated here, at the edge.


@app.exception_handler(OrganizationSlugConflict)
async def _organization_slug_conflict(_: Request, exc: OrganizationSlugConflict) -> JSONResponse:
    """The generated slug was taken; a different name would work."""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(PermissionDenied)
async def _permission_denied(_: Request, exc: PermissionDenied) -> JSONResponse:
    """The caller's role does not grant what the endpoint requires."""
    return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": str(exc)})


# Unauthenticated probes for orchestrators and uptime monitors. Kept outside
# the versioned API so a new version never breaks them.
app.include_router(health_router)

# Versioned application API.
app.include_router(api_v1_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # The API authenticates with a bearer token, never a cookie, so it has no
    # credentials to allow and no reason to let a browser attach any.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_middleware(BodyLimitMiddleware)

# Added last so it is the outermost middleware: the request id is bound (and the
# access log emitted) around everything, including CORS.
app.add_middleware(RequestIdMiddleware)
