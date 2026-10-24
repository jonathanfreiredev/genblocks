"""Ten blocks a month, counted where the rows are.

The quota is the only limit the product enforces by itself: the spend caps live in
the dashboards that bill, and this is what those dashboards cannot do — stop one
person from queueing a month's worth by accident.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.moderation import service as moderation
from app.settings import settings
from app.tasks import limits, service
from app.tasks.models import StepStatus, Task, TaskStatus, TaskStep
from app.tasks.steps import IMAGE_STEP_NAMES, STEP_NAMES
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


async def _failed_at(session, task, *, index: int, names=STEP_NAMES) -> None:
    """The checklist the runner leaves when the step at ``index`` failed."""
    for position, name in enumerate(names):
        status = StepStatus.PENDING
        if position < index:
            status = StepStatus.SUCCEEDED
        elif position == index:
            status = StepStatus.FAILED
        session.add(TaskStep(task_id=task.id, index=position, name=name, status=status))

    task.status = TaskStatus.FAILED
    task.error = "The step that failed says why."
    await session.commit()


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

    assert "10 of your 10 generations" in str(reached)
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
    count = await db_session.scalar(
        select(func.count()).select_from(Task).where(Task.created_by == owner.id)
    )
    assert count == 1


async def test_enqueue_writes_a_pending_task_when_there_is_room(db_session):
    owner = await _owner(db_session)

    task = await service.enqueue_task(db_session, brief="A hero", created_by=owner.id)

    assert task.status == TaskStatus.PENDING
    assert task.created_by == owner.id


async def test_two_requests_cannot_spend_the_same_last_block(db_session, monkeypatch):
    """The count and the insert have to be one decision.

    Both requests get past the cheap early count — that is the point of the
    barrier — and then meet the lock. One inserts; the other counts that row and
    is refused. Without the lock both would see zero and both would insert.
    """
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    factory = async_sessionmaker(bind=db_session.bind, expire_on_commit=False)
    both_past_the_early_check = asyncio.Barrier(2)

    async def wait_at_the_door(text, *, client=None):
        await both_past_the_early_check.wait()
        return None

    monkeypatch.setattr(moderation, "refusal", wait_at_the_door)

    async def enqueue(brief: str):
        async with factory() as session:
            try:
                return await service.enqueue_task(session, brief=brief, created_by=owner.id)
            except limits.MonthlyQuotaReached as reached:
                return reached

    first, second = await asyncio.wait_for(
        asyncio.gather(enqueue("A hero"), enqueue("A pricing page")), timeout=5
    )

    tasks = [answer for answer in (first, second) if isinstance(answer, Task)]
    refusals = [
        answer for answer in (first, second) if isinstance(answer, limits.MonthlyQuotaReached)
    ]

    assert len(tasks) == 1
    assert len(refusals) == 1
    assert refusals[0].used == 1
    assert (
        await db_session.scalar(
            select(func.count()).select_from(Task).where(Task.created_by == owner.id)
        )
        == 1
    )


async def test_an_operator_is_not_held_by_the_month(db_session, monkeypatch):
    """Filling the catalogue is the registry's work, not a person's tenth block."""
    monkeypatch.setattr(settings, "admin_emails", "maker@example.com")
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    operator = await _owner(db_session)
    await _queued(db_session, operator, when=OCTOBER)

    assert await limits.admitted(db_session, user_id=operator.id, now=OCTOBER) is None


async def test_the_operator_list_ignores_case_and_spaces(db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", " Maker@Example.com ")
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    operator = await _owner(db_session)
    await _queued(db_session, operator, when=OCTOBER)

    assert await limits.admitted(db_session, user_id=operator.id, now=OCTOBER) is None


async def test_enqueue_lets_an_operator_past_the_month(db_session, monkeypatch):
    """The exemption holds at the door, not only at the bare check."""
    monkeypatch.setattr(settings, "admin_emails", "maker@example.com")
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    operator = await _owner(db_session)
    await _queued(db_session, operator)

    task = await service.enqueue_task(db_session, brief="A pricing page", created_by=operator.id)

    assert task.status == TaskStatus.PENDING


async def test_somebody_outside_the_operator_list_still_has_a_month(db_session, monkeypatch):
    """Naming somebody else an operator must not open the door for everyone."""
    monkeypatch.setattr(settings, "admin_emails", "someone@example.com")
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    await _queued(db_session, owner, when=OCTOBER)

    with pytest.raises(limits.MonthlyQuotaReached):
        await limits.admitted(db_session, user_id=owner.id, now=OCTOBER)


async def test_a_failure_before_the_block_is_generated_gives_the_slot_back(db_session, monkeypatch):
    """A brief refused at the spec never hired a sandbox: it is a defect, not a run."""
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    task = await _queued(db_session, owner, when=OCTOBER)
    await _failed_at(db_session, task, index=0)

    assert await limits.admitted(db_session, user_id=owner.id, now=OCTOBER) is None


async def test_an_image_that_never_generated_gives_the_slot_back(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    task = await _queued(db_session, owner, when=OCTOBER)
    await _failed_at(db_session, task, index=0, names=IMAGE_STEP_NAMES)

    assert await limits.admitted(db_session, user_id=owner.id, now=OCTOBER) is None


async def test_a_failure_during_generation_still_spends_the_month(db_session, monkeypatch):
    """The sandbox and the model turns were paid for, whatever came out."""
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    task = await _queued(db_session, owner, when=OCTOBER)
    await _failed_at(db_session, task, index=1)

    with pytest.raises(limits.MonthlyQuotaReached):
        await limits.admitted(db_session, user_id=owner.id, now=OCTOBER)


async def test_a_block_the_judge_rejected_still_spends_the_month(db_session, monkeypatch):
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    task = await _queued(db_session, owner, when=OCTOBER)
    await _failed_at(db_session, task, index=2)

    with pytest.raises(limits.MonthlyQuotaReached):
        await limits.admitted(db_session, user_id=owner.id, now=OCTOBER)


async def test_work_still_in_the_queue_counts(db_session, monkeypatch):
    """Counting only what already ran would let a stopped worker be free storage."""
    monkeypatch.setattr(settings, "tasks_per_month", 1)
    owner = await _owner(db_session)
    await _queued(db_session, owner, when=OCTOBER)

    with pytest.raises(limits.MonthlyQuotaReached):
        await limits.admitted(db_session, user_id=owner.id, now=OCTOBER)
