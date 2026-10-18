"""Reading what the judge answered, and deciding what it means.

The model call is not tested here: that would be a test of somebody else's
uptime. What is tested is everything up to it and after it — how the model is
configured for the answer, what the artifact handed to it looks like, which
dimensions an answer is refused for, what a threshold does, and which of two
attempts came closer.
"""

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.harness.schemas import SandboxCheck, SandboxResult
from app.judge.rubrics import COMPONENTS, IMAGES
from app.judge.schemas import DimensionScore, JudgeAnswer
from app.judge.scoring import (
    JudgeUnavailable,
    UnreadableVerdict,
    as_judge,
    judge_model,
    margin,
    missed,
    read,
    score_component,
    threshold_for,
)
from app.settings import settings

PNG = b"\x89PNG\r\n\x1a\n"
CODE = "export default function Block() { return null }\n"


def answer(**scores: int) -> JudgeAnswer:
    """A judge's answer, with one note per dimension it scored."""
    return JudgeAnswer(
        dimensions={
            name: DimensionScore(score=score, note=f"what earned {name}")
            for name, score in scores.items()
        },
        summary="A block, in one paragraph.",
    )


def every(scores: dict[str, int]) -> JudgeAnswer:
    return answer(**scores)


def test_an_answer_is_stored_in_the_rubric_s_order_with_its_version():
    judged = read(
        answer(compliance=93, render=91, accessibility=89, visual=84, copy=86), COMPONENTS
    )

    assert list(judged.scores) == list(COMPONENTS.dimensions)
    assert judged.notes["visual"] == "what earned visual"
    assert judged.version == COMPONENTS.version
    assert judged.summary == "A block, in one paragraph."


def test_clearing_every_bar_passes(monkeypatch):
    monkeypatch.setattr(settings, "rubric_thresholds", dict.fromkeys(COMPONENTS.dimensions, 80))
    judged = read(every(dict.fromkeys(COMPONENTS.dimensions, 90)), COMPONENTS)

    assert judged.passed is True
    assert judged.below == ()


def test_the_dimension_under_its_bar_is_what_fails_an_attempt(monkeypatch):
    monkeypatch.setattr(settings, "rubric_thresholds", {"visual": 90})
    judged = read(every({**dict.fromkeys(COMPONENTS.dimensions, 95), "visual": 89}), COMPONENTS)

    # Named in rubric order, and the one that failed: a high mean over the others
    # does not carry it (PLAN.md, section 7).
    assert judged.below == ("visual",)
    assert judged.passed is False


def test_a_dimension_with_no_threshold_is_scored_and_not_gated(monkeypatch):
    monkeypatch.setattr(settings, "rubric_thresholds", {})

    assert threshold_for("render") is None
    assert missed("render", 0) is False
    assert read(every(dict.fromkeys(COMPONENTS.dimensions, 3)), COMPONENTS).passed is True


def test_an_answer_that_forgets_a_dimension_is_refused():
    with pytest.raises(UnreadableVerdict) as refused:
        read(answer(render=90, accessibility=90, visual=90, copy=90), COMPONENTS)

    assert "compliance" in str(refused.value)


def test_an_answer_that_invents_a_dimension_is_refused():
    with pytest.raises(UnreadableVerdict) as refused:
        read(
            answer(render=90, accessibility=90, visual=90, copy=90, compliance=90, novelty=99),
            COMPONENTS,
        )

    assert "novelty" in str(refused.value)


def test_the_image_rubric_is_read_against_its_own_dimensions(monkeypatch):
    monkeypatch.setattr(
        settings, "rubric_thresholds", {"visual": 70, "prompt_fit": 70, "compliance": 80}
    )
    judged = read(answer(visual=88, prompt_fit=91, compliance=97), IMAGES)

    assert list(judged.scores) == list(IMAGES.dimensions)
    assert judged.passed is True


def test_the_margin_is_the_room_left_on_the_dimension_that_came_closest(monkeypatch):
    monkeypatch.setattr(settings, "rubric_thresholds", {"visual": 70, "copy": 70})

    # One attempt failed a dimension badly, the other only just: the second came
    # closer, whatever the two means say.
    assert margin({"visual": 60, "copy": 95}) == -10
    assert margin({"visual": 68, "copy": 71}) == -2


def test_with_nothing_gated_the_margin_falls_back_to_the_scores(monkeypatch):
    monkeypatch.setattr(settings, "rubric_thresholds", {})

    assert margin({"visual": 80, "copy": 90}) == 85
    assert margin({}) == 0


def test_every_shipped_threshold_names_a_dimension_a_rubric_scores():
    known = set(COMPONENTS.dimensions) | set(IMAGES.dimensions)

    # A key that matches nothing is a bar nobody clears and nobody misses: it
    # would read as a gate and never act as one.
    assert set(settings.rubric_thresholds) <= known


def test_a_deployment_with_no_key_is_told_what_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(JudgeUnavailable) as refused:
        judge_model()

    assert "OPENAI_API_KEY" in str(refused.value)


def test_the_judge_runs_on_the_configured_model(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "llm_model", "gpt-6-luna")

    model = judge_model()

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-6-luna"
    # No temperature: the rubric asks a model to score, and this deployment's
    # model refuses everything but its own default.
    assert model.temperature is None


def test_the_model_is_bound_before_it_is_asked(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")

    # What a test injects and what production calls have to be the same thing: a
    # runnable that answers with a ``JudgeAnswer``, rather than a model whose
    # prose somebody would have to parse.
    assert isinstance(as_judge(), Runnable)


class ScriptedJudge:
    """A judge that answers what it was told to, and keeps what it was shown."""

    def __init__(self, said: JudgeAnswer) -> None:
        self.said = said
        self.shown: list = []

    async def ainvoke(self, messages: list) -> JudgeAnswer:
        self.shown = messages

        return self.said


@pytest.mark.anyio
async def test_the_artifact_is_what_the_model_is_handed(monkeypatch):
    monkeypatch.setattr(settings, "rubric_thresholds", dict.fromkeys(COMPONENTS.dimensions, 80))
    scripted = ScriptedJudge(every(dict.fromkeys(COMPONENTS.dimensions, 88)))
    found = SandboxResult(checks=[SandboxCheck(name="render", ok=True)], screenshot=PNG)

    judged = await score_component(brief="A pricing page", code=CODE, found=found, model=scripted)

    system, human = scripted.shown
    # The rubric is the stable half, and the brief is not in it: the same prompt
    # is sent for every block (PLAN.md, section 5).
    assert isinstance(system, SystemMessage)
    assert COMPONENTS.text in system.text
    assert "A pricing page" not in system.text

    assert isinstance(human, HumanMessage)
    assert "A pricing page" in human.text
    assert CODE in human.text
    assert human.content[1]["image_url"]["url"].startswith("data:image/png;base64,")

    assert judged.scores["render"] == 88
    assert judged.version == COMPONENTS.version
