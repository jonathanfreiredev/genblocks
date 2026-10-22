"""Wake the queue's worker, without ever letting a wake-up fail a request.

The queue is Postgres and the worker is a Modal function (see
``app/tasks/modal_app.py``). A run claims its first task in about a second, so
the run is started the moment a row is committed rather than waiting for the
schedule to come round.

Nothing here may raise. The row is already committed by the time this is called
and the schedule is the net underneath it, so a person who queued a block should
never be told their brief failed because Modal was slow.
"""

from __future__ import annotations

import asyncio

import modal
import structlog

from app.settings import settings

logger = structlog.get_logger("app.tasks")

# How long a wake-up may take before it is abandoned. It sits on the request's
# path, so it is bounded: a Modal that has not answered in this long is not going
# to answer soon enough to be worth the person waiting.
WAKE_TIMEOUT_SECONDS = 5.0

# The looked-up function, kept because the lookup is a round trip to Modal and
# one process queues many tasks. A redeployed worker is picked up by the next
# process, which is the same deploy that restarts this one.
_function: modal.Function | None = None


async def _worker() -> modal.Function | None:
    """The function to run, or ``None`` when this deployment has no worker."""
    global _function

    configured = (settings.worker_function or "").strip()
    if not configured:
        return None

    if _function is None:
        app_name, _, function_name = configured.partition(".")
        if not function_name:
            raise ValueError(f"WORKER_FUNCTION must read 'app.function', not {configured!r}")
        # The lookup is synchronous, so it is handed to a thread rather than
        # stalling the event loop that is answering the request.
        _function = await asyncio.to_thread(modal.Function.from_name, app_name, function_name)

    return _function


async def wake_worker() -> None:
    """Start one run of the worker. Never raises, and never waits long."""
    try:
        async with asyncio.timeout(WAKE_TIMEOUT_SECONDS):
            function = await _worker()
            if function is None:
                return
            await function.spawn.aio()
    except Exception:  # noqa: BLE001 - the schedule is the net, this call is not
        logger.warning("the worker could not be woken", exc_info=True)
