"""One run's trace, when there is somewhere to send it.

Langfuse is a copy of what happened, never the source of truth: the task, its
attempt, its scores and its pictures are rows in Postgres, and what this module
records is written after those rows have committed. The SDK buffers events and
exports them from a background thread, so a slow or unreachable Langfuse costs a
line in the log, not a minute of a worker's time.

Without both keys nothing is built and every trace id stays ``None``: a
deployment that has not configured Langfuse is not a deployment with broken
tracing, and the panel's "not recorded" is the honest thing to show. A deployment
that has, but whose first span cannot be opened, ends up in the same place and
says so in the log — the alternative is a tracing feature that stops the product
it is supposed to observe.

What the trace keeps that the ledger does not: the judge's notes and summary, the
harness's rounds with the sandbox's own words, and the timing of each step. The
scores go both ways; the sentences only live here.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from langfuse import Langfuse

from app.settings import settings

logger = structlog.get_logger("app.observability")

# The client is built once and reused: the SDK owns the OpenTelemetry provider and
# its background threads, and a second one in the same process would export the
# same spans to two places.
_client: Langfuse | None = None


def configured() -> bool:
    """Whether both keys are set, which is the whole of "tracing is on"."""
    return bool(settings.langfuse_public_key and settings.langfuse_secret_key)


def start(*, name: str, input: Any, metadata: Any | None = None) -> Trace:
    """Begin a trace, or a trace that is not recorded.

    The id is ours: it is generated here, written to the task's row by the caller,
    and handed to the trace. That is what makes the link in the panel resolvable
    before the run has finished.
    """
    if not configured():
        return Trace.disabled()

    try:
        client = _get_client()
        trace_id = client.create_trace_id()
        root = client.start_observation(
            name=name,
            input=input,
            metadata=metadata,
            trace_context={"trace_id": trace_id},
        )
    except Exception as broke:  # noqa: BLE001 - observability must never end a run
        logger.warning("tracing is off", error=str(broke))
        return Trace.disabled()

    return Trace(id=trace_id, root=root, client=client)


def _get_client() -> Langfuse:
    global _client
    if _client is None:
        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_host,
            # The same word the rest of the service uses for its environment, so
            # "development" and "production" traces are told apart in one place.
            environment=settings.env,
        )

    return _client


class Span:
    """One step's observation, or nothing when tracing is off."""

    def __init__(self, span: Any | None = None) -> None:
        self._span = span

    def update(self, **fields: Any) -> None:
        if self._span is None:
            return

        try:
            self._span.update(**fields)
        except Exception as broke:  # noqa: BLE001 - a step must not fail over a span
            logger.warning("span not traced", error=str(broke))

    def end(self, *, error: str | None = None) -> None:
        if self._span is None:
            return

        try:
            if error is not None:
                self._span.update(level="ERROR", status_message=error)
            self._span.end()
        except Exception as broke:  # noqa: BLE001 - closing a span is never the point
            logger.warning("span not closed", error=str(broke))


class Trace:
    """A run's trace: a root observation, the steps inside it, and its scores."""

    def __init__(
        self, *, id: str | None, root: Any | None = None, client: Any | None = None
    ) -> None:
        self.id = id
        self._root = root
        self._client = client

    @classmethod
    def disabled(cls) -> Trace:
        """The trace of a deployment that is not tracing: every call is a no-op."""
        return cls(id=None)

    @asynccontextmanager
    async def step(self, name: str, *, input: Any | None = None) -> AsyncIterator[Span]:
        """One step, closed however it ends.

        A step that raises is the interesting one: the span keeps the error as its
        status message, which is how the trace explains a task that failed without
        anybody reading the task row first.
        """
        span = Span(self._root.start_observation(name=name, input=input) if self._root else None)

        try:
            yield span
        except BaseException as error:
            span.end(error=str(error) or type(error).__name__)
            raise
        else:
            span.end()

    def score(
        self,
        name: str,
        value: float,
        *,
        comment: str | None = None,
        data_type: str | None = None,
    ) -> None:
        """Attach one number to the trace, after the row that justifies it exists."""
        if self._client is None:
            return

        try:
            self._client.create_score(
                trace_id=self.id,
                name=name,
                value=value,
                comment=comment,
                data_type=data_type,
            )
        except Exception as broke:  # noqa: BLE001 - a score is a copy, not a result
            logger.warning("score not traced", score=name, error=str(broke))

    def finish(
        self, *, output: Any | None = None, metadata: Any | None = None, error: str | None = None
    ) -> None:
        """Close the root observation with the run's outcome."""
        if self._root is None:
            return

        try:
            if error is not None:
                self._root.update(level="ERROR", status_message=error)
            self._root.update(output=output, metadata=metadata)
        except Exception as broke:  # noqa: BLE001 - the run has already been written
            logger.warning("trace not finished", error=str(broke))

    def end(self) -> None:
        """End the root observation. Called after the task row has committed."""
        if self._root is None:
            return

        try:
            self._root.end()
        except Exception as broke:  # noqa: BLE001 - the row is the record, not this
            logger.warning("trace not closed", error=str(broke))


def shutdown() -> None:
    """Flush what is buffered and stop the client, once, at the end of the process.

    A worker that is being cancelled has a half-written trace; this is what sends
    the half that exists. Never raises: the process is ending either way.
    """
    global _client
    if _client is None:
        return

    try:
        _client.shutdown()
    except Exception as broke:  # noqa: BLE001 - shutdown is not the moment to fail
        logger.warning("tracing not flushed", error=str(broke))
    finally:
        _client = None
