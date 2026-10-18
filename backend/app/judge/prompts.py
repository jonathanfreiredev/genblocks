"""What the judge is told, and how the artifact is put in front of it.

The stable half of the prompt — who the judge is, and the rubric it scores by —
is one system message, and everything about this attempt is in the message after
it. That order is not decoration: the model this deployment uses bills cached
input at a tenth of fresh input, and the rubric is the part that is the same
every time (PLAN.md, section 5).

The artifact arrives as a reader of it would see it: the brief it was written
from, the code as written, what the sandbox found when it built it, and the
render. The judge is told what the checks said rather than what they are worth:
whether a failed layout check matters is exactly the judgement being asked for.
"""

import base64

from app.harness.schemas import SandboxResult
from app.judge.rubrics import Rubric

JUDGE_FRAME = """\
You are the judge of GenBlocks: an independent reader of what somebody else
built. Score by the rubric below and by nothing else — not by whether you would
have chosen this direction, and not by how much effort the attempt looks like it
took.

For every dimension the rubric names, answer with:
- a score, in whole numbers, from 0 to 100;
- one sentence saying what earned it.

Answer with a summary as well: a short paragraph about the artifact for a reader
who will never see it. Name what decided the outcome. No encouragement, no
apology, no restating the numbers.
"""

# How the artifact is introduced. Sentence case, and the section names match the
# rubric's: a judge reading "what the sandbox found" knows which dimension it is
# evidence for.
BRIEF_HEADING = "The brief this block was written from:"
CODE_HEADING = "The block, as it was written:"
FOUND_HEADING = "What the sandbox found when it built it:"
RENDER_ATTACHED = "The render is attached."
RENDER_MISSING = (
    "There is no render: the sandbox never got as far as a page, so score `render` "
    "from what it did report."
)
PROMPT_HEADING = "The prompt this image was generated from:"
IMAGE_HEADING = "The image, as it came back:"

# What the code is fenced as. The language is a hint to the model, not a parser:
# the fence is closed on its own line whatever the tag was.
CODE_FENCE = "tsx"


def system_prompt(rubric: Rubric) -> str:
    """The half of the prompt that never changes for a rubric."""
    return f"{JUDGE_FRAME}\n{rubric.text}"


def about_component(
    *,
    brief: str,
    code: str,
    found: SandboxResult,
    screenshot: bytes | None,
) -> list[dict]:
    """One block, as the message the judge reads it in."""
    said = [
        BRIEF_HEADING,
        "",
        brief,
        "",
        CODE_HEADING,
        "",
        f"```{CODE_FENCE}",
        code,
        "```",
        "",
        FOUND_HEADING,
        "",
        report(found),
        "",
        RENDER_ATTACHED if screenshot is not None else RENDER_MISSING,
    ]

    parts: list[dict] = [{"type": "text", "text": "\n".join(said)}]
    if screenshot is not None:
        parts.append(render(screenshot))

    return parts


def about_image(
    *,
    prompt: str,
    image: bytes,
    width: int,
    height: int,
    media_type: str = "image/png",
) -> list[dict]:
    """One stock image, as the message the judge reads it in."""
    said = [
        PROMPT_HEADING,
        "",
        prompt,
        "",
        f"{IMAGE_HEADING} It was produced at {width}×{height}.",
    ]

    return [
        {"type": "text", "text": "\n".join(said)},
        render(image, media_type=media_type),
    ]


def report(found: SandboxResult) -> str:
    """The sandbox's findings, one line each, in the order it made them.

    Every check is named, passing or not: a judge that only hears about failures
    cannot tell a block that passed seven checks from one that was never asked.
    """
    lines = [
        f"- {check.name}: {'ok' if check.ok else 'failed'}"
        + (f" — {check.detail}" if check.detail else "")
        for check in found.checks
    ]
    lines.extend(
        f"- axe {violation.id} ({violation.impact or 'unknown impact'}, {violation.nodes} nodes): "
        f"{violation.help}"
        for violation in found.violations
    )

    return "\n".join(lines) if lines else "- the sandbox reported nothing"


def render(image: bytes, *, media_type: str = "image/png") -> dict:
    """Image bytes as a message part: a data URL, since nothing is hosted."""
    encoded = base64.b64encode(image).decode()

    return {
        "type": "image_url",
        "image_url": {"url": f"data:{media_type};base64,{encoded}"},
    }
