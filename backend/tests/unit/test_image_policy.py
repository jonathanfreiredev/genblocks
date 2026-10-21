"""The brief-level image policy: people are a product rule, not a suggestion."""

import json

import httpx
import pytest

from app.image_policy import service

pytestmark = pytest.mark.anyio


class PolicyModel:
    def __init__(self, body: dict) -> None:
        self.body = body
        self.asked: dict = {}

    async def post(self, url: str, *, headers: dict, json: dict) -> httpx.Response:
        self.asked = {"url": url, "headers": headers, "body": json}
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(self.body),
                        }
                    }
                ]
            },
            request=httpx.Request("POST", url),
        )


json_module = json

# Captured before the autouse fixture stubs the policy for the rest of the suite.
ORIGINAL_EVALUATE = service.evaluate


def answer(*, status: str, role: str, proposed: str | None = None) -> dict:
    return {
        "has_image_direction": True,
        "has_people": role != "none",
        "people_role": role,
        "status": status,
        "reason": "the policy reason",
        "proposed_brief": proposed,
    }


async def test_a_brief_without_an_image_direction_is_ready(monkeypatch):
    monkeypatch.setattr(service, "evaluate", ORIGINAL_EVALUATE)
    model = PolicyModel(
        {
            "has_image_direction": False,
            "has_people": False,
            "people_role": "none",
            "status": "ready",
            "reason": "no image direction",
            "proposed_brief": None,
        }
    )

    decision = await service.evaluate("A pricing table", client=model)

    assert decision.ready
    assert decision.has_image_direction is False
    assert decision.proposed_brief is None


async def test_incidental_people_need_confirmation_and_a_rewrite(monkeypatch):
    monkeypatch.setattr(service, "evaluate", ORIGINAL_EVALUATE)
    model = PolicyModel(
        answer(
            status="needs_image_confirmation",
            role="incidental",
            proposed="A pottery wheel with clay, no hands",
        )
    )

    decision = await service.evaluate("Hands shaping clay", client=model)

    assert decision.needs_confirmation
    assert decision.proposed_brief == "A pottery wheel with clay, no hands"


async def test_a_person_as_the_subject_is_rejected(monkeypatch):
    monkeypatch.setattr(service, "evaluate", ORIGINAL_EVALUATE)
    model = PolicyModel(answer(status="rejected", role="central"))

    decision = await service.evaluate("A portrait of a woman", client=model)

    assert decision.status == "rejected"
    assert decision.people_role == "central"
    assert decision.proposed_brief is None


async def test_an_unknown_status_is_unreadable_not_a_pass(monkeypatch):
    monkeypatch.setattr(service, "evaluate", ORIGINAL_EVALUATE)
    model = PolicyModel(answer(status="maybe", role="none"))

    with pytest.raises(service.ImagePolicyUnavailable):
        await service.evaluate("A hero", client=model)
