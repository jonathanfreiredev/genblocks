"""How many generations one person may ask the registry for.

The window is a calendar month because what it protects is a bill somebody reads
once a month, not a queue that needs to be fair within the hour. The number is a
product decision, not a calibration: it moves when the product does, so it lives
in settings and is stated in the refusal rather than discovered.

There is deliberately no global breaker here. The spend that could run away is
Modal and OpenAI, and both are capped where they are billed; a second cap in code
would be a number nobody could keep true, sitting next to the real one and
pretending to be it. What this module guarantees is the one thing the dashboards
cannot: that no single person can queue more than their month allows, even when
two requests arrive at the same time.

The operators named in ``ADMIN_EMAILS`` are the exception, because the person the
quota protects the bill from is not the person who fills the catalogue: seeding
thirty blocks is the registry's own work, and it should not take three months.
They are the same list that already decides who may take content down, so the
exemption inherits a decision that exists rather than inventing one. For an
operator the boundary is the provider spend caps, exactly as it is for everybody
else past their tenth generation.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import service as admin_service
from app.db.models import utcnow
from app.settings import settings
from app.tasks.models import Task
from app.users.models import User


class MonthlyQuotaReached(Exception):
    """This person has queued every generation their month allows.

    Says how many, out of how many, and when the door opens again — a limit that
    only says "no" leaves the reader to guess whether it is a day or a year.
    """

    def __init__(self, *, used: int, limit: int, reopens: datetime) -> None:
        self.used = used
        self.limit = limit
        self.reopens = reopens
        super().__init__(
            f"You have queued {used} of your {limit} generations this month. "
            f"Your next one opens on {reopens:%-d %B}."
        )


async def admitted(
    session: AsyncSession, *, user_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Let the brief through, or say why it cannot be queued.

    This is a read, not a reservation: two requests can both read the same free
    slot. Use it for a cheap early refusal, then call :func:`reserve` for the
    check that actually decides.

    An operator is let through unconditionally: the month's allowance is a guard
    on a person's spend, not on the catalogue's own seeding.

    ``now`` is how a test asks about December without waiting for it; production
    passes nothing and gets the clock.
    """
    if await _is_operator(session, user_id=user_id):
        return

    moment = now or utcnow()
    used = await _queued_this_month(session, user_id=user_id, since=month_start(moment))

    if used >= settings.tasks_per_month:
        raise MonthlyQuotaReached(
            used=used,
            limit=settings.tasks_per_month,
            reopens=next_month(moment),
        )


async def reserve(
    session: AsyncSession, *, user_id: uuid.UUID, now: datetime | None = None
) -> None:
    """Admit one task atomically, or say why it cannot be queued.

    The user's row is the mutex for this month. Taking it before the count is
    what makes the count a decision instead of a guess: a second request waits
    here, then counts the row the first one committed. The lock lasts until the
    caller commits the task insert, so the two statements must share this
    transaction and nothing between them may leave the process.

    A refusal rolls back, because it has nothing to keep and the lock must not
    outlive the answer.
    """
    await session.scalar(select(User.id).where(User.id == user_id).with_for_update())

    try:
        await admitted(session, user_id=user_id, now=now)
    except MonthlyQuotaReached:
        await session.rollback()
        raise


def month_start(moment: datetime) -> datetime:
    """The first instant of the month ``moment`` falls in, in UTC."""
    return datetime(moment.year, moment.month, 1, tzinfo=UTC)


def next_month(moment: datetime) -> datetime:
    """The first instant of the month after the one ``moment`` falls in."""
    if moment.month == 12:
        return datetime(moment.year + 1, 1, 1, tzinfo=UTC)

    return datetime(moment.year, moment.month + 1, 1, tzinfo=UTC)


async def _is_operator(session: AsyncSession, *, user_id: uuid.UUID) -> bool:
    """Whether this person is one of the configured operators.

    The role is decided by email, and the email lives on the row, so it is read
    here rather than trusted from the caller: a router or a tool that forgot to
    pass the flag would be a router or a tool that hands out free generations.
    """
    user = await session.get(User, user_id)

    return user is not None and admin_service.is_admin(user)


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
