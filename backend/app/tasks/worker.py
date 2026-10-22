"""One drain of the task queue, then exit.

Run from the backend directory:

    python -m app.tasks.worker

This is the entrypoint the deployed worker calls, on demand and on a schedule.
It claims queued tasks until the queue is empty and returns, because the
container is billed for every second it lives: a loop that waits for work would
be a loop that pays for nothing. Exiting while work is still arriving loses
nothing — the queue is Postgres, and the next run picks it up.

Reconciliation happens here rather than at API boot. Runs overlap: the schedule
fires every minute and one run can last for minutes, so "a task is running and
no process could be working on it" is no longer something a boot can decide. Age
decides it, and ``settings.worker_stale_seconds`` is how long it waits.
"""

from __future__ import annotations

import asyncio
import sys

import structlog

from app.db.session import async_session_maker
from app.logging_config import configure_logging
from app.observability import service as observability
from app.settings import settings
from app.tasks import service
from app.tasks.runner import drain_once

logger = structlog.get_logger("app.tasks.worker")


async def main() -> int:
    """Drain the queue, and say how much of it was worked through."""
    configure_logging()

    async with async_session_maker() as session:
        interrupted = await service.interrupt_orphaned_tasks(
            session, older_than_seconds=settings.worker_stale_seconds
        )
    if interrupted:
        logger.info("interrupted orphaned tasks", count=interrupted)

    drained = 0
    try:
        while await drain_once():
            drained += 1
    finally:
        # Whatever the SDK still has buffered goes out now: this process does
        # not get a second chance to flush it.
        observability.shutdown()

    logger.info("drained the queue", tasks=drained)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
