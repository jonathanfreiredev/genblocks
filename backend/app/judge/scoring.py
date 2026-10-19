"""Scoring a candidate, and reading what came back.

One call, one rubric, one answer. The judge has no tools and no loop: what it is
asked for is to look at an artifact that is already finished and say what it is
worth. Its independence is the product's claim (PLAN.md, decision 7) and it is
structural rather than promised: it never sees the conversation that produced the
brief, it cannot change the artifact, and it runs after the sandbox has closed
the attempt.

What it is *not* told is the thresholds. A judge that knows where the bar is
scores to the bar, and then the verdict is not an independent reading any more.
It writes numbers; :func:`read` is what decides whether they clear.
"""

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.harness.schemas import SandboxResult
from app.judge.prompts import about_component, about_image, system_prompt
from app.judge.rubrics import COMPONENTS, IMAGES, Rubric
from app.judge.schemas import JudgeAnswer, Judged
from app.settings import settings


class JudgeUnavailable(Exception):
    """There is no model to judge with. The deployment has no key."""


class UnreadableVerdict(Exception):
    """The judge answered about something other than what it was asked.

    Not a bad score and not a low one: an answer that does not line up with the
    rubric, which is a run that has to stop rather than a block that gets
    published with a row missing.
    """


# How the judge is asked for its answer: tool calling, with the answer's shape as
# the tool's arguments. Not the strict JSON-schema mode, which is the default and
# refuses this shape — the answer is a map keyed by dimension name, and a strict
# schema wants a fixed list of keys, which is the one thing a rubric cannot have
# without the schema and the rubric stating the same dimensions twice. What comes
# back is validated against ``JudgeAnswer`` all the same, so a judge answering
# about the wrong dimension fails here rather than in a regex.
ASKING = "function_calling"


def judge_model() -> BaseChatModel:
    """The model that scores, or a refusal saying what is missing.

    No temperature and no other knob, for the same reason the writer asks for
    none: this deployment's model refuses everything but its own default, and
    asking for one would fail a run over a setting nobody could honour.
    """
    if not settings.openai_api_key:
        raise JudgeUnavailable("The judge has no model configured: set OPENAI_API_KEY on the API.")

    return ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key)


def as_judge(model: BaseChatModel | None = None) -> Runnable:
    """A model bound to the shape its answer has to take."""
    return (model or judge_model()).with_structured_output(JudgeAnswer, method=ASKING)


async def score_component(
    *,
    brief: str,
    files: dict[str, str],
    found: SandboxResult,
    model: Runnable | None = None,
) -> Judged:
    """Score one block from the artifacts the sandbox left behind.

    ``model`` is there so a test can answer with a script instead of paying for a
    completion; production passes nothing and gets the configured model.
    """
    answer: JudgeAnswer = await (model or as_judge()).ainvoke(
        [
            SystemMessage(system_prompt(COMPONENTS)),
            HumanMessage(
                about_component(
                    brief=brief,
                    files=files,
                    found=found,
                    screenshot=found.screenshot,
                )
            ),
        ]
    )

    return read(answer, COMPONENTS)


async def score_image(
    *,
    prompt: str,
    image: bytes,
    width: int,
    height: int,
    media_type: str = "image/png",
    model: Runnable | None = None,
) -> Judged:
    """Score one stock image, by the shorter rubric images are held to."""
    answer: JudgeAnswer = await (model or as_judge()).ainvoke(
        [
            SystemMessage(system_prompt(IMAGES)),
            HumanMessage(
                about_image(
                    prompt=prompt,
                    image=image,
                    width=width,
                    height=height,
                    media_type=media_type,
                )
            ),
        ]
    )

    return read(answer, IMAGES)


def read(answer: JudgeAnswer, rubric: Rubric) -> Judged:
    """The answer as the registry keeps it, or a refusal naming what was wrong."""
    answered = set(answer.dimensions)
    expected = set(rubric.dimensions)
    if answered != expected:
        raise UnreadableVerdict(_mismatch(answered, expected, rubric))

    # Built in the rubric's order rather than the answer's: the stored scores are
    # read by a panel and by a person, and neither should get the model's order.
    scores = {name: answer.dimensions[name].score for name in rubric.dimensions}
    notes = {name: answer.dimensions[name].note for name in rubric.dimensions}

    return Judged(
        scores=scores,
        notes=notes,
        summary=answer.summary,
        version=rubric.version,
        below=tuple(name for name in rubric.dimensions if missed(name, scores[name])),
    )


def threshold_for(dimension: str) -> int | None:
    """The bar one dimension has to clear, or ``None`` where there is none.

    A dimension with no threshold is scored and shown, and passes whatever it
    scores: a setting that is not there is a decision not to gate on it, not an
    oversight to fail a task over.
    """
    return settings.rubric_thresholds.get(dimension)


def missed(dimension: str, score: int) -> bool:
    """Whether one dimension came in under its bar."""
    threshold = threshold_for(dimension)

    return threshold is not None and score < threshold


def _mismatch(answered: set[str], expected: set[str], rubric: Rubric) -> str:
    """What was wrong with an answer, in the words of the rubric that refused it."""
    missing = ", ".join(sorted(expected - answered)) or "nothing"
    invented = ", ".join(sorted(answered - expected)) or "nothing"

    return (
        f"The judge answered about the wrong dimensions of the {rubric.name} rubric: "
        f"missing {missing}; not in the rubric: {invented}."
    )
