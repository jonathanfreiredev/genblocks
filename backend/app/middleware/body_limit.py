"""Refuse a request body that is too large before FastAPI parses it.

The domain schemas bound every field, but they run after the body has been read
into memory. This is the coarse guard in front of that: JSON endpoints here carry
a brief or a message, never a file, so a megabyte is already generous.
"""

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

MAX_BODY_BYTES = 1_000_000


class BodyLimitMiddleware:
    """Reject an oversized ``Content-Length`` with a small JSON answer."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        raw = Headers(scope=scope).get("content-length")

        if raw is not None:
            try:
                length = int(raw)
            except ValueError:
                await self._refuse(
                    scope, receive, send, status=400, detail="Invalid Content-Length."
                )
                return

            if length < 0:
                await self._refuse(
                    scope, receive, send, status=400, detail="Invalid Content-Length."
                )
                return

            if length > MAX_BODY_BYTES:
                await self._refuse(
                    scope,
                    receive,
                    send,
                    status=413,
                    detail=f"The request body may be at most {MAX_BODY_BYTES} bytes.",
                )
                return

        await self.app(scope, receive, send)

    async def _refuse(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        *,
        status: int,
        detail: str,
    ) -> None:
        response = JSONResponse({"detail": detail}, status_code=status)
        await response(scope, receive, send)
