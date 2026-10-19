"""How many blocks one person may ask the registry for.

The window is a calendar month because what it protects is a bill somebody reads
once a month, not a queue that needs to be fair within the hour. The number is a
product decision, not a calibration: it moves when the product does, so it lives
in settings and is stated in the refusal rather than discovered.

There is deliberately no global breaker here. The spend that could run away is
Modal and OpenAI, and both are capped where they are billed; a second cap in code
would be a number nobody could keep true, sitting next to the real one and
pretending to be it. What this module guarantees is the one thing the dashboards
cannot: that no single person can queue a tenth of a thousand by accident.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import utcnow
from app.settings import settings
from app.tasks.models import Task


class MonthlyQuotaReached(Exception):
    """This person has queued every block their month allows.

    Says how many, out of how many, and when the door opens again — a limit that
    only says "no" leaves the reader to guess whether it is a day or a year.
    """

    def __init__(self, *, used: int, limit: int, reopens: datetime) -> None:
        self.used = used
        self.limit = limit
        self.reopens = reopens
        super().__init__(
            f"You have queued {used} of your {limit} blocks this month. "
            f"Your next one opens on {reopens:%-d %B}."
        )


async def admitted(
    session: AsyncSession, *, user_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Let the brief through, or say why it cannot be queued.

    ``now`` is how a test asks about December without waiting for it; production
    passes nothing and gets the clock.
    """
    moment = now or utcnow()
    used = await _queued_this_month(session, user_id=user_id, since=month_start(moment))

    if used >= settings.tasks_per_month:
        raise MonthlyQuotaReached(
            used=used,
            limit=settings.tasks_per_month,
            reopens=next_month(moment),
        )


def month_start(moment: datetime) -> datetime:
    """The first instant of the month ``moment`` falls in, in UTC."""
    return datetime(moment.year, moment.month, 1, tzinfo=UTC)


def next_month(moment: datetime) -> datetime:
    """The first instant of the month after the one ``moment`` falls in."""
    if moment.month == 12:
        return datetime(moment.year + 1, 1, 1, tzinfo=UTC)

    return datetime(moment.year, moment.month + 1, 1, tzinfo=UTC)


async def _queued_this_month(session: AsyncSession, *, user_id: uuid.UUID, since: datetime) -> int:
    """How many tasks this person queued since ``since``."""
    return await session.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.created_by == user_id,
            Task.deleted_at.is_(None),
            Task.created_at >= since,
            # A cached brief queued no work: it costs nothing, so it spends no
            # quota (PLAN.md, decision 44).
            Task.cached.is_(False),
        )
    )
