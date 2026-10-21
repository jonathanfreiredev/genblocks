"""A standalone image is checked before it can become a task."""

import pytest

from app.image_policy import prompt as prompt_policy
from app.images import planning
from app.moderation import service as moderation
from app.settings import settings
from tests.helpers import create_category

pytestmark = pytest.mark.anyio

PROMPT = "A quiet harbour at dawn with fishing boats"


def decision(
    *,
    status: str = "ready",
    role: str = "none",
    suggested: str | None = None,
) -> prompt_policy.PromptDecision:
    return prompt_policy.PromptDecision(
        status=status,
        has_people=role != "none",
        people_role=role,
        reason="the policy reason",
        suggested_prompt=suggested,
    )


async def test_a_valid_prompt_is_ready(db_session, monkeypatch):
    category = await create_category(db_session, slug="photography", kind="image")

    async def ready(prompt, *, client=None):
        return decision()

    monkeypatch.setattr(prompt_policy, "evaluate", ready)

    plan = await planning.plan_image(
        db_session,
        prompt=PROMPT,
        width=1024,
        height=768,
        category="photography",
    )

    assert plan.ready
    assert plan.category_id == category.id
    assert plan.prompt == PROMPT


async def test_incidental_people_get_a_rewrite(db_session, monkeypatch):
    await create_category(db_session, slug="photography", kind="image")

    async def needs_rewrite(prompt, *, client=None):
        return decision(
            status="needs_image_confirmation",
            role="incidental",
            suggested="A pottery wheel with clay, no hands",
        )

    monkeypatch.setattr(prompt_policy, "evaluate", needs_rewrite)

    plan = await planning.plan_image(
        db_session,
        prompt="Hands shaping clay on a pottery wheel",
        width=1024,
        height=1024,
        category="photography",
    )

    assert plan.needs_confirmation
    assert plan.suggested_prompt == "A pottery wheel with clay, no hands"


async def test_a_person_as_the_subject_is_rejected(db_session, monkeypatch):
    await create_category(db_session, slug="photography", kind="image")

    async def central(prompt, *, client=None):
        return decision(status="rejected", role="central")

    monkeypatch.setattr(prompt_policy, "evaluate", central)

    plan = await planning.plan_image(
        db_session,
        prompt="A portrait of a woman",
        width=1024,
        height=1024,
        category="photography",
    )

    assert plan.status == "rejected"
    assert plan.suggested_prompt is None


async def test_the_final_prompt_gate_still_runs(db_session, monkeypatch):
    await create_category(db_session, slug="photography", kind="image")

    async def ready(prompt, *, client=None):
        return decision()

    async def refused(prompt, *, client=None):
        return "it names a real brand"

    monkeypatch.setattr(prompt_policy, "evaluate", ready)
    monkeypatch.setattr(moderation, "image_prompt_refusal", refused)

    plan = await planning.plan_image(
        db_session,
        prompt="A can of a real cola on a table",
        width=1024,
        height=1024,
        category="photography",
    )

    assert plan.status == "rejected"
    assert "brand" in plan.reason


async def test_a_size_the_provider_cannot_make_is_rejected_before_any_model(db_session):
    plan = await planning.plan_image(
        db_session,
        prompt=PROMPT,
        width=1000,
        height=768,
        category="photography",
    )

    assert plan.status == "rejected"
    assert "multiple of 32" in plan.reason


async def test_an_unknown_image_category_is_rejected(db_session):
    plan = await planning.plan_image(
        db_session,
        prompt=PROMPT,
        width=1024,
        height=768,
        category="not-a-category",
    )

    assert plan.status == "rejected"
    assert "image category" in plan.reason


async def test_the_same_quota_counts_image_tasks(db_session, monkeypatch):
    from app.tasks import service as tasks

    category = await create_category(db_session, slug="photography", kind="image")

    async def ready(prompt, *, client=None):
        return decision()

    monkeypatch.setattr(prompt_policy, "evaluate", ready)
    monkeypatch.setattr(settings, "tasks_per_month", 1)

    first = await tasks.enqueue_image_task(
        db_session,
        prompt=PROMPT,
        width=1024,
        height=768,
        category=category.slug,
        created_by=(await _owner(db_session)).id,
    )

    assert first.image_category_id == category.id

    with pytest.raises(tasks.limits.MonthlyQuotaReached):
        await tasks.enqueue_image_task(
            db_session,
            prompt="A second harbour",
            width=1024,
            height=768,
            category=category.slug,
            created_by=first.created_by,
        )


async def _owner(session):
    import uuid

    from app.users.models import User

    user = User(supabase_user_id=uuid.uuid4(), email="image-maker@example.com")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
