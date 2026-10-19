"""Whether a text may become a block, asked of a safety model.

Two doors ask the same question at different moments. The **brief** is asked before
it becomes a task, so a refusal costs nothing; the **copy** the block shows is asked
after the harness has written it, so a block that is unsafe never reaches the judge
or the registry. Neither replaces the other: a brief can be harmless and the copy it
grows can still be the thing that should not be published.

What the artifact door is sent is the copy, not the project: text nodes and the
quoted strings that read like prose. Sending the source would be sending mostly
code, and the free safety model is limited by the token (2,000 a minute on Groq's
free tier) — a request that large is refused before it is read, which is a gate
that never opens.

With no key the check is **off**, not guessed: the log says so on every call, and a
deployment that forgot the key is told rather than silently trusting everything. A
key that is set but cannot be reached is a different case — an unverified text is
not an allowed one, so it raises and the door fails closed. Safety is the one place
where "we could not check" and "it passed" must not look the same.
"""

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

import httpx
import structlog

from app.settings import settings

logger = structlog.get_logger("app.moderation")

ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SECONDS = 15.0

# How much of the copy is sent. The safety model's free tier allows 2,000 tokens a
# minute, and the frame below takes a couple of hundred of them; what is left is a
# few hundred words of copy, which is more than a block shows. The bound is also a
# bill: a runaway project cannot turn one call into a request the provider refuses.
MAX_CHARS = 2_500

# What a block says, rather than what it is written in: the text between tags, and
# the quoted strings that read like prose (copy in data arrays, alternates, labels).
TEXT_NODE = re.compile(r">([^<>{}]{2,})<")
QUOTED = re.compile(r"""["']([^"'\\\n]{3,})["']""")

# The question, worded once. A UI brief is ordinary: pricing, heroes, forms and
# dashboards are the product, and a classifier that refuses them is worse than no
# classifier at all.
FRAME = """\
You are a safety classifier for GenBlocks, a public library of interface blocks.

Decide whether the text below may be used to build a block that anyone can copy
into their own site. Refuse text that is sexual, hateful, harassing, violent,
encourages self-harm, describes illegal activity, or impersonates a real person or
brand in a deceptive way. Ordinary interface work — pricing pages, heroes, forms,
dashboards, menus, and marketing copy about products — is allowed.

Answer with JSON only, no prose around it:
{"allowed": true or false, "reason": "one sentence"}
"""


def copy_of(files: Mapping[str, str]) -> str:
    """The words a block shows, one per line, for the moderator.

    A JSX project is mostly machinery: imports, class lists, handlers. The part a
    safety model can judge is the copy that ends up on somebody's page, so that is
    what is extracted — text nodes, and quoted strings that read like sentences
    rather than like a Tailwind class list.
    """
    said: list[str] = []

    for content in files.values():
        said.extend(TEXT_NODE.findall(content))
        said.extend(part for part in QUOTED.findall(content) if _reads_like_copy(part))

    # The same line twice is the same question. Keep the order the block has.
    seen: set[str] = set()
    unique: list[str] = []
    for part in said:
        text = " ".join(part.split())
        if text and text not in seen:
            seen.add(text)
            unique.append(text)

    return "\n".join(unique)


def _reads_like_copy(text: str) -> bool:
    """A quoted string that is prose: not a class list, a path, or a URL."""
    return (
        " " in text
        and any(character.isupper() for character in text)
        and not text.startswith(("http://", "https://", "/", "./"))
    )


class ModerationUnavailable(Exception):
    """The safety model was asked and did not answer usably."""


class BriefRejected(Exception):
    """The brief was refused before it became a task, with the reason."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"The brief cannot be built: {reason}")


@dataclass(frozen=True)
class Verdict:
    """One answer: whether the text may pass, and why in a sentence."""

    allowed: bool
    reason: str


async def refusal(text: str, *, client: httpx.AsyncClient | None = None) -> str | None:
    """Why the text may not pass, or ``None`` when it may.

    ``client`` is how a test answers without a provider; production passes nothing.
    """
    if not settings.groq_api_key and client is None:
        # Loud on purpose: a deployment with moderation off should be able to find
        # that out from the log rather than from an incident.
        logger.warning("moderation is off", reason="set GROQ_API_KEY on the API")
        return None

    verdict = await review(text, client=client)

    return None if verdict.allowed else verdict.reason


async def review(text: str, *, client: httpx.AsyncClient | None = None) -> Verdict:
    """Ask the safety model about one text, and read its answer strictly."""
    if client is not None:
        return await _review(client, text=text)

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
        return await _review(http, text=text)


async def _review(client: httpx.AsyncClient, *, text: str) -> Verdict:
    try:
        answer = await client.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.moderation_model,
                "messages": [
                    {"role": "system", "content": FRAME},
                    {"role": "user", "content": text[:MAX_CHARS]},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
        )
    except httpx.HTTPError as broke:
        raise ModerationUnavailable(f"The moderator did not answer: {broke}") from broke

    if answer.status_code != 200:
        raise ModerationUnavailable(
            f"The moderator refused the request ({answer.status_code}): {answer.text[:200]}"
        )

    try:
        said = answer.json()["choices"][0]["message"]["content"]
        body = json.loads(said)
        allowed = body["allowed"]
        reason = body["reason"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as unreadable:
        raise ModerationUnavailable(
            f"The moderator answered something this service does not understand: {unreadable}"
        ) from unreadable

    if not isinstance(allowed, bool) or not isinstance(reason, str):
        raise ModerationUnavailable("The moderator answered without a verdict and a reason.")

    return Verdict(allowed=allowed, reason=reason)
