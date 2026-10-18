"""The one call that writes a block.

The harness grows an agent later (Fase 9). Here it is a single call with the
whole brief in front of it, and that is the point worth keeping when it grows:
the writer decides what the block is, the sandbox decides whether it exists, and
neither knows how the other is built.

What comes back is a model's answer, so it is read rather than trusted: the file
is taken out of its fence, and an answer with no component in it is a failure
with a message rather than an empty attempt.

A second attempt at the same brief arrives with the reason the first one did not
publish (the loop is ``app.tasks.runner``). That report is the only thing a retry
has that a first attempt did not, and without it a retry buys a second sandbox
run for another roll of the same dice.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.harness.prompts import WRITER_PROMPT
from app.settings import settings

# Below this, an answer is a sentence about a block rather than a block.
MIN_CODE_LENGTH = 60

# Answers arrive fenced. The tag is whatever the model felt like writing, so the
# opening fence is read as a fence and the tag thrown away.
FENCE = "```"

# How a previous attempt's report is introduced. The heading says what the
# paragraph under it is for: the message is otherwise all brief.
FEEDBACK_HEADING = "Why the last attempt at this brief was not published:"


class GeneratorUnavailable(Exception):
    """There is no model to write with. The deployment has no key."""


class NothingWritten(Exception):
    """The model answered, and no component came out of it."""


def writer_model() -> BaseChatModel:
    """The model that writes blocks, or a refusal saying what is missing.

    No temperature and no other knob: the model this deployment is configured
    with refuses everything but its own default, and asking for one would fail a
    task over a setting nobody could honour.
    """
    if not settings.openai_api_key:
        raise GeneratorUnavailable(
            "The generator has no model configured: set OPENAI_API_KEY on the API."
        )

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
    )


async def write_component(
    *,
    brief: str,
    category: str,
    feedback: str | None = None,
    model: BaseChatModel | None = None,
) -> str:
    """Write one block for a brief, and return its source.

    ``feedback`` is what a previous attempt at the same brief was told was wrong
    with it, or ``None`` on a first attempt. ``model`` is there so a test can
    write a script instead of paying for a completion; production passes nothing
    and gets the configured model.
    """
    answer = await (model or writer_model()).ainvoke(
        [
            SystemMessage(WRITER_PROMPT),
            HumanMessage(asked(brief=brief, category=category, feedback=feedback)),
        ]
    )

    return read_component(str(answer.text))


def asked(*, brief: str, category: str, feedback: str | None = None) -> str:
    """The brief, with what the registry already decided about it.

    A retry arrives with the reason the attempt before it did not publish, in the
    words of whoever turned it down — the sandbox's failing checks or the judge's
    own notes. A second attempt without it would be another roll of the same
    dice, at the price of another sandbox run.
    """
    said = f"The registry files this under: {category}\n\nThe brief:\n{brief}"
    if not feedback:
        return said

    return (
        f"{said}\n\n{FEEDBACK_HEADING}\n{feedback}\n\n"
        "Write the block again. Fix what is named above, and keep what was not."
    )


def read_component(answer: str) -> str:
    """The component out of a model's answer.

    The file is the answer, and everything else in it — the sentence before the
    fence, the fence itself, the prose after it — is packaging.
    """
    code = _fenced(answer).strip()

    if len(code) < MIN_CODE_LENGTH or "export" not in code:
        raise NothingWritten(
            "The model's answer held no component: no fenced file, and nothing that exports one."
        )

    return code


def _fenced(answer: str) -> str:
    """What is inside the first fence, or the whole answer when there is none.

    The first fence rather than the last: a model that explains itself afterwards
    has already written the file by the time it starts explaining.
    """
    opening = answer.find(FENCE)
    if opening == -1:
        return answer

    body = answer[opening + len(FENCE) :]
    # The tag the model put on the fence ("tsx", "typescript", …) runs to the end
    # of its line and is not code.
    _, _, body = body.partition("\n")

    closing = body.find(FENCE)
    return body if closing == -1 else body[:closing]
