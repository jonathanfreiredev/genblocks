"""Whether a text may pass, read strictly.

The safety model is one call and one JSON document. What is tested here is that a
document it did not mean to send — prose around the JSON, a missing verdict, a
provider that answered 500 — is a refusal to check rather than a pass. "We could
not ask" and "it is fine" are the same shape only if nobody looks.
"""

import json

import httpx
import pytest

from app.moderation import service as moderation
from app.settings import settings

pytestmark = pytest.mark.anyio

KEY = "test-groq-key"


class Groq:
    """The moderator, answered without a provider."""

    def __init__(
        self, *, body: dict | None = None, status: int = 200, broke: Exception | None = None
    ):
        self.body = body if body is not None else _said(allowed=True, reason="ordinary UI work")
        self.status = status
        self.broke = broke
        self.asked: dict = {}

    async def post(self, url: str, *, headers: dict, json: dict) -> httpx.Response:
        self.asked = {"url": url, "headers": headers, "body": json}
        if self.broke is not None:
            raise self.broke

        return httpx.Response(self.status, json=self.body, request=httpx.Request("POST", url))


def _said(*, allowed: bool, reason: str) -> dict:
    return {
        "choices": [{"message": {"content": json.dumps({"allowed": allowed, "reason": reason})}}]
    }


@pytest.fixture(autouse=True)
def no_moderation():
    """This module tests the decision itself, so the suite's stub is overridden.

    Every call below passes a fake client, which is what keeps it off the network.
    """
    return None


@pytest.fixture(autouse=True)
def with_key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", KEY)


async def test_an_allowed_text_comes_back_allowed():
    groq = Groq(body=_said(allowed=True, reason="a pricing page is ordinary"))

    verdict = await moderation.review("A pricing page", client=groq)

    assert verdict.allowed is True
    assert verdict.reason == "a pricing page is ordinary"


async def test_a_refused_text_carries_the_reason():
    groq = Groq(body=_said(allowed=False, reason="it impersonates a real bank"))

    verdict = await moderation.review("A clone of a bank's login", client=groq)

    assert verdict.allowed is False
    assert verdict.reason == "it impersonates a real bank"


async def test_the_question_carries_the_model_and_the_key():
    groq = Groq()

    await moderation.review("A hero", client=groq)

    assert groq.asked["url"] == moderation.ENDPOINT
    assert groq.asked["headers"]["Authorization"] == f"Bearer {KEY}"
    assert groq.asked["body"]["model"] == settings.moderation_model
    assert groq.asked["body"]["messages"][-1]["content"] == "A hero"


async def test_an_answer_that_is_not_json_is_not_a_pass():
    groq = Groq(body={"choices": [{"message": {"content": "Sure, looks fine to me!"}}]})

    with pytest.raises(moderation.ModerationUnavailable, match="does not understand"):
        await moderation.review("A hero", client=groq)


async def test_an_answer_without_a_verdict_is_not_a_pass():
    groq = Groq(body={"choices": [{"message": {"content": json.dumps({"allowed": "yes"})}}]})

    with pytest.raises(moderation.ModerationUnavailable):
        await moderation.review("A hero", client=groq)


async def test_a_provider_that_answers_an_error_is_not_a_pass():
    groq = Groq(status=500, body={"error": "boom"})

    with pytest.raises(moderation.ModerationUnavailable, match="500"):
        await moderation.review("A hero", client=groq)


async def test_a_provider_that_cannot_be_reached_is_not_a_pass():
    groq = Groq(broke=httpx.ConnectError("no route"))

    with pytest.raises(moderation.ModerationUnavailable, match="did not answer"):
        await moderation.review("A hero", client=groq)


async def test_refusal_is_none_when_the_text_passes():
    groq = Groq()

    assert await moderation.refusal("A pricing page", client=groq) is None


async def test_refusal_is_the_reason_when_it_does_not():
    groq = Groq(body=_said(allowed=False, reason="it describes a weapon"))

    assert await moderation.refusal("A weapon", client=groq) == "it describes a weapon"


async def test_without_a_key_the_check_is_off_and_says_so(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)

    assert await moderation.refusal("Anything at all") is None


def test_the_brief_refusal_says_what_it_is():
    refused = moderation.BriefRejected("it impersonates a real bank")

    assert str(refused) == "The brief cannot be built: it impersonates a real bank"
