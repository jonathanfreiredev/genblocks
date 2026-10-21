"""The image policy is enforced at the one door every brief comes through."""

import uuid

import pytest
from sqlalchemy import func, select

from app.components.planning import ImageConfirmationRequired
from app.image_policy import service as image_policy
from app.moderation import service as moderation
from app.tasks import service as tasks_service
from app.tasks.models import Task
from app.users.models import User

pytestmark = pytest.mark.anyio


async def _owner(session) -> User:
    user = User(supabase_user_id=uuid.uuid4(), email="maker@example.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


def decision(*, status: str, role: str, proposed: str | None = None):
    return image_policy.ImagePolicyDecision(
        status=status,
        has_image_direction=True,
        has_people=role != "none",
        people_role=role,
        reason="the policy reason",
        proposed_brief=proposed,
    )


async def test_a_brief_with_incidental_people_waits_for_a_rewrite(db_session, monkeypatch):
    owner = await _owner(db_session)

    async def needs_rewrite(brief, *, client=None):
        return decision(
            status="needs_image_confirmation",
            role="incidental",
            proposed="A pottery wheel with clay, no hands",
        )

    monkeypatch.setattr(image_policy, "evaluate", needs_rewrite)

    with pytest.raises(ImageConfirmationRequired) as raised:
        await tasks_service.enqueue_task(
            db_session, brief="A hero with hands shaping clay", created_by=owner.id
        )

    assert raised.value.proposed_brief == "A pottery wheel with clay, no hands"
    assert await db_session.scalar(select(func.count()).select_from(Task)) == 0


async def test_a_brief_with_a_person_as_subject_is_refused(db_session, monkeypatch):
    owner = await _owner(db_session)

    async def rejected(brief, *, client=None):
        return decision(status="rejected", role="central")

    monkeypatch.setattr(image_policy, "evaluate", rejected)

    with pytest.raises(moderation.BriefRejected):
        await tasks_service.enqueue_task(
            db_session, brief="A portrait of a woman for the hero", created_by=owner.id
        )

    assert await db_session.scalar(select(func.count()).select_from(Task)) == 0
