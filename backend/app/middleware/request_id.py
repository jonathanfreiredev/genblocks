import time
import uuid

import structlog
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = structlog.get_logger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"
_MAX_REQUEST_ID_LENGTH = 128
# Health probes run every few seconds; keep them out of the default log level.
_QUIET_PATHS = frozenset({"/health", "/health/ready"})


def resolve_request_id(raw: str | None) -> str:
    """Return a usable request id: the inbound one if valid, else a new one."""
    if raw is not None:
        candidate = raw.strip()
        if 0 < len(candidate) <= _MAX_REQUEST_ID_LENGTH:
            return candidate

    return uuid.uuid4().hex


def _inbound_request_id(scope: Scope) -> str | None:
    for name, value in scope["headers"]:
        if name == b"x-request-id":
            return value.decode("latin-1")

    return None


class RequestIdMiddleware:
    """Bind a request id to the log context and echo it back to the client.

    Every log line emitted while handling the request carries the id, so
    incidents can be followed across the request without passing it around by
    hand.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = resolve_request_id(_inbound_request_id(scope))
        structlog.contextvars.bind_contextvars(request_id=request_id)

        method = scope["method"]
        path = scope["path"]
        status_code = 500
        start = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            log = logger.debug if path in _QUIET_PATHS else logger.info
            log(
                "request",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            structlog.contextvars.clear_contextvars()
