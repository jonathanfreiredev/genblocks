"""The two HTTP doors for a standalone image, and the chat confirmation."""

import pytest
from sqlalchemy import func, select

from app.image_policy import prompt as prompt_policy
from app.tasks.models import Task
from tests.auth_stub import mint_token
from tests.helpers import auth_header, create_category

pytestmark = pytest.mark.anyio

PROMPT = "A quiet harbour at dawn with fishing boats"


async def _signed_in(client) -> dict[str, str]:
    token = mint_token()
    assert (await client.get("/v1/users/me", headers=auth_header(token))).status_code == 200
    return auth_header(token)


async def test_the_plan_endpoint_answers_without_queueing(client, db_session):
    headers = await _signed_in(client)
    await create_category(db_session, slug="photography", kind="image")

    response = await client.post(
        "/v1/images/plan",
        headers=headers,
        json={
            "prompt": PROMPT,
            "width": 1024,
            "height": 768,
            "category": "photography",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert await db_session.scalar(select(func.count()).select_from(Task)) == 0


async def test_generate_queues_an_image_task(client, db_session):
    headers = await _signed_in(client)
    category = await create_category(db_session, slug="photography", kind="image")

    response = await client.post(
        "/v1/images/generate",
        headers=headers,
        json={
            "prompt": PROMPT,
            "width": 1024,
            "height": 768,
            "category": "photography",
        },
    )

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["kind"] == "generate_image"
    assert body["image_width"] == 1024
    assert body["image_height"] == 768
    assert body["image_category_id"] == str(category.id)


async def test_generate_returns_the_no_person_rewrite(client, db_session, monkeypatch):
    headers = await _signed_in(client)
    await create_category(db_session, slug="photography", kind="image")

    async def rewrite(prompt, *, client=None):
        return prompt_policy.PromptDecision(
            status="needs_image_confirmation",
            has_people=True,
            people_role="incidental",
            reason="people are not allowed",
            suggested_prompt="A pottery wheel with clay, no hands",
        )

    monkeypatch.setattr(prompt_policy, "evaluate", rewrite)

    response = await client.post(
        "/v1/images/generate",
        headers=headers,
        json={
            "prompt": "Hands shaping clay on a pottery wheel",
            "width": 1024,
            "height": 1024,
            "category": "photography",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["suggested_prompt"] == ("A pottery wheel with clay, no hands")


async def test_the_chat_confirm_queues_an_image_proposal(client, db_session):
    headers = await _signed_in(client)
    await create_category(db_session, slug="photography", kind="image")

    response = await client.post(
        "/v1/agent/confirm",
        headers=headers,
        json={
            "kind": "image",
            "brief": PROMPT,
            "force": False,
            "width": 1024,
            "height": 768,
            "category": "photography",
        },
    )

    assert response.status_code == 202, response.text
    assert response.json()["kind"] == "generate_image"
    assert response.json()["image_width"] == 1024


async def test_an_image_proposal_needs_its_size_and_category(client):
    headers = await _signed_in(client)

    response = await client.post(
        "/v1/agent/confirm",
        headers=headers,
        json={
            "kind": "image",
            "brief": PROMPT,
            "force": False,
        },
    )

    assert response.status_code == 422


async def test_a_brief_cannot_be_requeued_as_an_image_by_accident(client, db_session):
    headers = await _signed_in(client)
    await create_category(db_session, slug="photography", kind="image")

    response = await client.post(
        "/v1/agent/confirm",
        headers=headers,
        json={
            "kind": "image",
            "brief": PROMPT,
            "width": 1024,
            "height": 768,
            "category": "not-an-image-category",
        },
    )

    assert response.status_code == 422
    assert await db_session.scalar(select(func.count()).select_from(Task)) == 0
