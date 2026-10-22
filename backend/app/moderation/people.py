"""The one visual rule a generated picture cannot break: it may not contain a person.

A prompt filter is not enough. A model can put a hand, a reflection, a crowd or a
humanoid figure into a scene that never asked for one. This gate reads the bytes
the provider actually returned and refuses anything with a human or human-like
subject before the generic moderation call, the judge or Cloudinary sees it.

The classifier deliberately treats ambiguity as a person. A false positive costs
one refused picture; the other mistake is not one this product is willing to
price.
"""

import base64
import json
from dataclasses import dataclass

import httpx

from app.settings import settings

TIMEOUT_SECONDS = 15.0
CHAT_COMPLETIONS_ENDPOINT = "https://api.openai.com/v1/chat/completions"

FRAME = """\
You are a strict visual policy classifier for GenBlocks, a library of interface
blocks and stock images. A picture may belong to a block or stand on its own;
either way the rule is the same.

The only question is whether the picture contains a human or a human-like figure.
Refuse any person, face, head, body, hand, arm, leg, skin, silhouette, crowd,
humanoid character, realistic mannequin, statue of a person or costume that
implies a person. Objects, animals, food, landscapes, interiors, plants,
machines and abstract shapes are allowed.

When the answer is ambiguous, answer that a human is present. Answer with JSON
only, no prose:
{"has_human": true or false, "reason": "one short sentence"}
"""


class PeopleCheckUnavailable(Exception):
    """The person detector was asked and did not answer usably."""


@dataclass(frozen=True)
class PeopleVerdict:
    """Whether a picture contains a human, and why the classifier says so."""

    has_human: bool
    reason: str


async def people_refusal(
    data: bytes,
    *,
    media_type: str = "image/png",
    client: httpx.AsyncClient | None = None,
) -> str | None:
    """Why the picture contains a person, or ``None`` when it does not."""
    if not data:
        raise PeopleCheckUnavailable("The picture is empty.")

    verdict = await _review(data, media_type=media_type, client=client)
    return verdict.reason if verdict.has_human else None


async def _review(
    data: bytes,
    *,
    media_type: str,
    client: httpx.AsyncClient | None,
) -> PeopleVerdict:
    if client is None and not settings.openai_api_key:
        if settings.env == "production":
            raise PeopleCheckUnavailable(
                "The person detector is off in production: set OPENAI_API_KEY."
            )

        return PeopleVerdict(has_human=False, reason="the person detector is off in development")

    encoded = base64.b64encode(data).decode()
    body = {
        "model": settings.people_detection_model,
        "messages": [
            {"role": "system", "content": FRAME},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{encoded}"},
                    }
                ],
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }

    try:
        if client is not None:
            answer = await client.post(
                CHAT_COMPLETIONS_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json=body,
            )
        else:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
                answer = await http.post(
                    CHAT_COMPLETIONS_ENDPOINT,
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json=body,
                )
    except httpx.HTTPError as broke:
        raise PeopleCheckUnavailable(f"The person detector did not answer: {broke}") from broke

    if answer.status_code != 200:
        raise PeopleCheckUnavailable(
            f"The person detector refused the request ({answer.status_code})."
        )

    try:
        said = answer.json()["choices"][0]["message"]["content"]
        body = json.loads(said)
        has_human = body["has_human"]
        reason = body["reason"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as unreadable:
        raise PeopleCheckUnavailable(
            f"The person detector answered something this service does not understand: {unreadable}"
        ) from unreadable

    if not isinstance(has_human, bool) or not isinstance(reason, str):
        raise PeopleCheckUnavailable("The person detector answered without a verdict.")

    return PeopleVerdict(has_human=has_human, reason=reason)
