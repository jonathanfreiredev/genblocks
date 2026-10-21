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

    assert groq.asked["url"] == moderation.GROQ_ENDPOINT
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


async def test_without_a_key_the_check_is_off_in_development(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "env", "development")

    assert await moderation.refusal("Anything at all") is None


async def test_without_a_key_production_refuses_the_text(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "env", "production")

    with pytest.raises(moderation.ModerationUnavailable, match="moderation is off"):
        await moderation.refusal("Anything at all")


def test_the_moderation_endpoint_answer_is_read_as_categories():
    answer = httpx.Response(
        200,
        json={
            "results": [
                {
                    "flagged": True,
                    "categories": {"violence": True, "hate": False},
                }
            ]
        },
        request=httpx.Request("POST", moderation.OPENAI_MODERATION_ENDPOINT),
    )

    verdict = moderation._read_openai(answer)

    assert verdict.allowed is False
    assert verdict.reason == "violence"


class Images:
    """The image moderation endpoint, answered without a provider."""

    def __init__(self, *, flagged: bool = False) -> None:
        self.flagged = flagged
        self.asked: dict = {}

    async def post(self, url: str, *, headers: dict, json: dict) -> httpx.Response:
        self.asked = {"url": url, "headers": headers, "body": json}

        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "flagged": self.flagged,
                        "categories": {"sexual/minors": self.flagged},
                    }
                ]
            },
            request=httpx.Request("POST", url),
        )


async def test_an_image_that_clears_the_classifier_is_allowed(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-openai")
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "csam_scan_enabled", False)

    assert await moderation.image_refusal(b"jpeg-bytes", client=Images()) is None


async def test_an_image_the_classifier_flags_as_sexual_minors_is_blocked(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-openai")
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "csam_scan_enabled", False)

    with pytest.raises(moderation.SexualMinorsDetected, match="sexual content involving minors"):
        await moderation.image_refusal(b"jpeg-bytes", client=Images(flagged=True))


async def test_the_csam_gate_is_skipped_when_the_switch_is_off(monkeypatch):
    monkeypatch.setattr(settings, "csam_scan_enabled", False)
    monkeypatch.setattr(settings, "openai_api_key", "test-openai")

    async def never(data, *, media_type):
        raise AssertionError("the CSAM adapter must not run while disabled")

    monkeypatch.setattr(moderation, "_csam_refusal", never)

    assert await moderation.image_refusal(b"jpeg-bytes", client=Images()) is None


async def test_enabling_csam_without_a_url_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "csam_scan_enabled", True)
    monkeypatch.setattr(settings, "csam_scan_url", None)
    monkeypatch.setattr(settings, "openai_api_key", "test-openai")

    with pytest.raises(moderation.ModerationUnavailable, match="CSAM_SCAN_URL"):
        await moderation.image_refusal(b"jpeg-bytes", client=Images())


async def test_a_csam_match_stops_before_the_generic_classifier(monkeypatch):
    monkeypatch.setattr(settings, "csam_scan_enabled", True)
    monkeypatch.setattr(settings, "csam_scan_url", "https://csam.test/scan")

    async def matched(data, *, media_type):
        raise moderation.CSAMDetected("a known hash")

    class NeverAsked(Images):
        async def post(self, *args, **kwargs):
            raise AssertionError("a CSAM match must not reach the generic moderator")

    monkeypatch.setattr(moderation, "_csam_refusal", matched)

    with pytest.raises(moderation.CSAMDetected):
        await moderation.image_refusal(b"jpeg-bytes", client=NeverAsked())


def test_the_brief_refusal_says_what_it_is():
    refused = moderation.BriefRejected("it impersonates a real bank")

    assert str(refused) == "The brief cannot be built: it impersonates a real bank"


def test_only_the_copy_is_sent_to_the_moderator():
    files = {
        "src/Block.tsx": """
import { useState } from "react";

const shell = "mt-4 flex items-baseline justify-between gap-6 border-t";

export default function Block() {
  return (
    <section className={shell}>
      <h1>One headline, kept short</h1>
      <p>No sign-up · MIT licensed</p>
      <a href="/blocks">Browse the vault</a>
    </section>
  );
}
"""
    }

    text = moderation.copy_of(files)

    assert "One headline, kept short" in text
    assert "No sign-up · MIT licensed" in text
    assert "Browse the vault" in text
    # The machinery is not the question: no imports, no class lists, no paths.
    assert "useState" not in text
    assert "mt-4" not in text
    assert "/blocks" not in text


def test_copy_sitting_in_a_data_array_is_included():
    files = {
        "src/Block.tsx": (
            'const quotes = [{ author: "Marisol Vega", words: "It shipped in a day." }];'
        )
    }

    text = moderation.copy_of(files)

    assert "It shipped in a day." in text
    assert "Marisol Vega" in text


def test_the_same_line_twice_is_asked_once():
    files = {"src/Block.tsx": "<p>One line of copy.</p><p>One line of copy.</p>"}

    assert moderation.copy_of(files) == "One line of copy."


async def test_a_huge_copy_is_capped_before_it_is_sent():
    groq = Groq()

    await moderation.review("word " * 10_000, client=groq)

    sent = groq.asked["body"]["messages"][-1]["content"]
    assert len(sent) == moderation.MAX_CHARS


def test_the_image_rule_names_real_people_and_brands():
    from app.moderation.service import IMAGE_FRAME

    assert "identifiable people" in IMAGE_FRAME
    assert "company logos and trademarks" in IMAGE_FRAME
    assert "named living artist" in IMAGE_FRAME
