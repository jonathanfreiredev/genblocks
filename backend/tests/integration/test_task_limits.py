"""Ten blocks a month, counted where the rows are.

The quota is the only limit the product enforces by itself: the spend caps live in
the dashboards that bill, and this is what those dashboards cannot do — stop one
person from queueing a month's worth by accident.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.settings import settings
from app.tasks import limits, service
from app.tasks.models import Task, TaskStatus
from app.users.models import User

pytestmark = pytest.mark.anyio

OCTOBER = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)


async def _owner(session, email: str = "maker@example.com") -> User:
    user = User(supabase_user_id=uuid.uuid4(), email=email)
    session.add(user)
    await session.commit()

    return user


async def _queued(session, owner: User, *, when: datetime | None = None) -> Task:
    task = await service.create_task(session, brief="A pricing page", created_by=owner.id)
    if when is not None:
        task.created_at = when
        await session.commit()

    return task


async def test_a_month_is_a_window_and_its_edges_are_utc():
    assert limits.month_start(OCTOBER) == datetime(2026, 10, 1, tzinfo=UTC)
    assert limits.next_month(OCTOBER) == datetime(2026, 11, 1, tzinfo=UTC)


async def test_december_rolls_into_the_next_year():
    december = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)

    assert limits.next_month(december) == datetime(2027, 1, 1, tzinfo=UTC)


async def test_the_refusal_says_how_many_and_when_it_opens_again():
    reached = limits.MonthlyQuotaReached(
        used=10, limit=10, reopens=datetime(2026, 11, 1, tzinfo=UTC)
    )

    assert "10 of your 10 blocks" in str(reached)
    assert "1 November" in str(reached)


async def test_a_month_with_room_lets_the_brief_through(db_session):
    owner = await _owner(db_session)
    await _queued(db_session, owner, when=OCTOBER)

    assert await limits.admitted(db_session, user_id=owner.id, now=OCTOBER) is None


async def test_the_last_block_of_the_month_is_the_last(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 2)
    owner = await _owner(db_session)
    await _queued(db_session, owner, when=OCTOBER)
    await _queued(db_session, owner, when=OCTOBER)

    with pytest.raises(limits.MonthlyQuotaReached) as reached:
        await limits.admitted(db_session, user_id=owner.id, now=OCTOBER)

    assert reached.value.used == 2
    assert reached.value.limit == 2


async def test_a_task_from_last_month_does_not_count(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    await _queued(db_session, owner, when=OCTOBER - timedelta(days=40))

    # The same allowance, a new month: the old task is not this month's.
    assert await limits.admitted(db_session, user_id=owner.id, now=OCTOBER) is None


async def test_somebody_elses_tasks_do_not_count(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    another = await _owner(db_session, email="other@example.com")
    owner = await _owner(db_session)
    await _queued(db_session, another, when=OCTOBER)

    assert await limits.admitted(db_session, user_id=owner.id, now=OCTOBER) is None


async def test_a_deleted_task_gives_the_month_back(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    task = await _queued(db_session, owner, when=OCTOBER)
    task.deleted_at = datetime.now(UTC)
    await db_session.commit()

    assert await limits.admitted(db_session, user_id=owner.id, now=OCTOBER) is None


async def test_enqueue_checks_before_it_writes(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    await _queued(db_session, owner, when=OCTOBER)

    with pytest.raises(limits.MonthlyQuotaReached):
        await service.enqueue_task(db_session, brief="A hero", created_by=owner.id)

    # The refusal is not a row: a task left behind would be a task the worker runs.
    from sqlalchemy import func, select

    count = await db_session.scalar(
        select(func.count()).select_from(Task).where(Task.created_by == owner.id)
    )
    assert count == 1


async def test_enqueue_writes_a_pending_task_when_there_is_room(db_session):
    owner = await _owner(db_session)

    task = await service.enqueue_task(db_session, brief="A hero", created_by=owner.id)

    assert task.status == TaskStatus.PENDING
    assert task.created_by == owner.id
