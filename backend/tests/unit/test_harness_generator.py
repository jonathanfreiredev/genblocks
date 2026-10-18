"""The one call that writes a block, read the way the runner reads it.

No network here: the model is a script (``tests/agent_stub.py``) and what is
tested is the seam that matters, which is what the runner gets back. A model
answers with prose around a file, and a run that kept the prose would put it in
the registry.
"""

import pytest
from langchain_core.messages import AIMessage

from app.harness import generator
from app.settings import settings
from tests.agent_stub import ScriptedChatModel

pytestmark = pytest.mark.anyio

CODE = """export default function Block() {
  return (
    <section className="px-6 py-24">
      <h1>Pricing for developers</h1>
    </section>
  );
}"""


def model(answer: str) -> ScriptedChatModel:
    """A model that answers with one message, cut into a few chunks."""
    return ScriptedChatModel(turns=[AIMessage(content=answer)])


def test_a_fenced_answer_becomes_the_file():
    answer = f"Here is the block:\n\n```tsx\n{CODE}\n```\n\nIt is responsive and self-contained."

    assert generator.read_component(answer) == CODE


def test_a_fence_without_a_tag_is_still_a_fence():
    assert generator.read_component(f"```\n{CODE}\n```") == CODE


def test_an_unfenced_answer_is_taken_as_it_stands():
    # A model that ignores the instruction to fence is still answering.
    assert generator.read_component(CODE) == CODE


def test_an_answer_with_no_component_is_a_failure():
    for answer in ("I would build a pricing page.", "```tsx\n```", "```tsx\nconst x = 1;\n```"):
        with pytest.raises(generator.NothingWritten):
            generator.read_component(answer)


def test_the_question_carries_the_brief_and_what_the_registry_decided():
    asked = generator.asked(brief="A pricing page", category="pricing")

    assert "pricing" in asked
    assert "A pricing page" in asked


def test_a_first_attempt_has_nothing_to_answer_for():
    asked = generator.asked(brief="A pricing page", category="pricing")

    assert generator.FEEDBACK_HEADING not in asked


def test_a_second_attempt_is_told_what_was_wrong_with_the_first():
    asked = generator.asked(
        brief="A pricing page",
        category="pricing",
        feedback="- copy (41, below 70): the buttons say Click here",
    )

    assert "A pricing page" in asked
    assert generator.FEEDBACK_HEADING in asked
    # In the words it was given: the report is the sandbox's or the judge's, and
    # the writer is the only reader that can act on it.
    assert "the buttons say Click here" in asked
    assert "Write the block again" in asked


async def test_the_writer_returns_what_the_model_wrote():
    written = await generator.write_component(
        brief="A pricing page",
        category="pricing",
        model=model(f"```tsx\n{CODE}\n```"),
    )

    assert written == CODE


async def test_a_deployment_with_no_key_says_what_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(generator.GeneratorUnavailable) as refused:
        generator.writer_model()

    assert "OPENAI_API_KEY" in str(refused.value)
