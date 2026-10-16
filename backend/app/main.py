from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_v1_router
from app.authz.permissions import PermissionDenied
from app.health.router import health_router
from app.logging_config import configure_logging
from app.middleware.request_id import RequestIdMiddleware
from app.organizations.service import OrganizationSlugConflict
from app.settings import settings

# Structured logging for the whole process (app + uvicorn).
configure_logging()

app = FastAPI()

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
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Added last so it is the outermost middleware: the request id is bound (and the
# access log emitted) around everything, including CORS.
app.add_middleware(RequestIdMiddleware)
