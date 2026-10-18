"""The harness, driven the way a model drives it.

The model is a script (``tests/agent_stub.py``) and the sandbox is a fake; what is
real here is the loop. When does it look, what is it shown when it does, what does
it refuse to do, and what does it hand back when it stops — those are the questions
a run's cost and its quality both come down to.
"""

import uuid

import pytest
from langchain_core.messages import AIMessage

from app.harness import agent, images, skills
from app.harness.schemas import SandboxCheck, SandboxFile, SandboxResult
from app.settings import settings
from tests.agent_stub import ScriptedChatModel

pytestmark = pytest.mark.anyio

PNG = b"\x89PNG\r\n\x1a\n"
BRIEF = "A hero for a developer tool: one headline, one line of copy, one button"
FIRST = "export default function Block() {\n  return <h1>One</h1>;\n}\n"
FIXED = "export default function Block() {\n  return <h1>One</h1>;\n  // fixed\n}\n"


def calls(tool: str, **arguments) -> AIMessage:
    """A turn that reaches for a tool."""
    return AIMessage(
        content="",
        tool_calls=[{"name": tool, "args": arguments, "id": f"call_{uuid.uuid4().hex[:8]}"}],
    )


def says(text: str) -> AIMessage:
    """A turn that answers in words: how the agent finishes."""
    return AIMessage(content=text)


class Sandbox:
    """The sandbox, answered without a Modal account.

    It remembers the project it was handed on every call, because what matters
    about a look is *when* it happened and *what* had been written by then.
    """

    def __init__(self) -> None:
        self.seen: list[dict[str, str]] = []

    async def check(self, files: list[SandboxFile]) -> SandboxResult:
        self.seen.append({one.path: one.content for one in files})

        return SandboxResult(
            checks=[
                SandboxCheck(name="typecheck", ok=True),
                SandboxCheck(name="render", ok=True),
            ],
            screenshot=PNG,
        )


@pytest.fixture
def sandbox(monkeypatch) -> Sandbox:
    fake = Sandbox()
    monkeypatch.setattr(agent.sandbox, "check", fake.check)

    return fake


@pytest.fixture
def pictures(monkeypatch) -> list[dict]:
    """The image library, answered without a provider or a cloud."""
    made: list[dict] = []

    async def generate(*, prompt: str, width: int, height: int, client=None) -> images.Generated:
        made.append({"prompt": prompt, "width": width, "height": height})

        return images.Generated(
            prompt=prompt,
            path="genblocks/images/abc123",
            url="https://cdn.test/genblocks/images/abc123",
            width=width,
            height=height,
            media_type="image/jpeg",
            data=b"jpeg-bytes",
        )

    monkeypatch.setattr(images, "generate", generate)

    return made


def scripted(*turns: AIMessage) -> ScriptedChatModel:
    return ScriptedChatModel(turns=list(turns))


def said_by_tools(model: ScriptedChatModel) -> str:
    """Everything the tools answered, as text, in the last turn the model took."""
    said = []

    for message in model.seen[-1]:
        if type(message).__name__ != "ToolMessage":
            continue

        if isinstance(message.content, str):
            said.append(message.content)
        else:
            said.extend(
                part.get("text", "") for part in message.content if part.get("type") == "text"
            )

    return "\n".join(said)


def attached_an_image(model: ScriptedChatModel) -> bool:
    """Whether the render came back with a tool's answer."""
    for message in model.seen[-1]:
        if type(message).__name__ != "ToolMessage" or isinstance(message.content, str):
            continue

        if any(part.get("type") == "image_url" for part in message.content):
            return True

    return False


async def test_the_builder_writes_looks_and_fixes_what_it_saw(sandbox):
    model = scripted(
        calls("read_skill", name="composition"),
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls("write_file", path=agent.ENTRY, content=FIXED),
        calls("look"),
        says("A hero, with the copy it needed."),
    )

    built = await agent.build(brief=BRIEF, category="hero", model=model)

    assert built.files == {agent.ENTRY: FIXED}
    assert built.iterations == 2
    assert built.skills == skills.version()
    # It looked at the version it had written, and then at the fixed one: the loop
    # is what makes the second look worth anything.
    assert [project[agent.ENTRY] for project in sandbox.seen] == [FIRST, FIXED]

    # The render came back with the findings, and the skill it asked for came back
    # as the document it is.
    assert attached_an_image(model) is True
    assert "render: ok" in said_by_tools(model)
    assert "# Composition" in said_by_tools(model)


async def test_the_builder_is_given_the_brief_and_the_shelf(sandbox):
    model = scripted(says("Nothing to build."))

    with pytest.raises(agent.NothingWritten):
        await agent.build(brief=BRIEF, category="pricing", model=model)

    system, ask = model.seen[-1][0], model.seen[-1][1]
    assert "read_skill" in system.content
    assert skills.index() in system.content
    assert BRIEF in ask.content
    assert "pricing" in ask.content


async def test_a_look_at_an_unchanged_project_does_not_build_it_again(sandbox):
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls("look"),
        says("Done."),
    )

    built = await agent.build(brief=BRIEF, category="hero", model=model)

    assert built.iterations == 2
    assert len(sandbox.seen) == 1
    assert "Nothing has changed" in said_by_tools(model)


async def test_the_budget_is_looks_and_it_is_said_out_loud(sandbox, monkeypatch):
    monkeypatch.setattr(settings, "harness_max_iterations", 1)
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls("write_file", path=agent.ENTRY, content=FIXED),
        calls("look"),
        says("Done with what I had."),
    )

    built = await agent.build(brief=BRIEF, category="hero", model=model)

    assert built.iterations == 1
    assert len(sandbox.seen) == 1
    assert "used your 1 looks" in said_by_tools(model)


async def test_only_the_projects_own_source_is_writable(sandbox):
    model = scripted(
        calls("write_file", path="src/Block.json", content="{}"),
        calls("write_file", path="../outside.tsx", content="x"),
        calls("write_file", path="/etc/passwd", content="x"),
        calls("write_file", path="vite.config.ts", content="x"),
        says("I could not write anything."),
    )

    with pytest.raises(agent.NothingWritten):
        await agent.build(brief=BRIEF, category="hero", model=model)

    said = said_by_tools(model)
    assert "Only .tsx, .ts, .css" in said
    assert "not a path inside the project" in said
    assert "belong to the block" in said


async def test_a_picture_before_a_look_is_refused(sandbox, pictures):
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls(
            "generate_image",
            slot="hero",
            prompt="a road at dawn",
            category="photography",
            width=1024,
            height=768,
        ),
        calls("look"),
        says("Built it without pictures."),
    )

    built = await agent.build(
        brief=BRIEF, category="hero", image_categories=["photography"], model=model
    )

    assert built.images == []
    assert pictures == []
    assert "Look at the block first" in said_by_tools(model)


async def test_a_picture_is_filed_under_a_type_the_library_has(sandbox, pictures):
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls(
            "generate_image",
            slot="hero",
            prompt="a road at dawn",
            category="mood",
            width=1024,
            height=768,
        ),
        calls(
            "generate_image",
            slot="hero",
            prompt="a road at dawn",
            category="photography",
            width=1024,
            height=768,
        ),
        calls("look"),
        calls(
            "generate_image",
            slot="hero",
            prompt="the same slot again",
            category="photography",
            width=1024,
            height=768,
        ),
        says("A hero with a photograph."),
    )

    built = await agent.build(
        brief=BRIEF, category="hero", image_categories=["photography", "illustration"], model=model
    )

    assert [one.slot for one in built.images] == ["hero"]
    assert [one.category for one in built.images] == ["photography"]
    assert len(pictures) == 1
    assert "no 'mood' type of image" in said_by_tools(model)
    assert "already a picture in slot" in said_by_tools(model)
    # The address it was given is in the conversation, because the block has to
    # put it in its own markup.
    assert "https://cdn.test/genblocks/images/abc123" in said_by_tools(model)


async def test_a_picture_asked_for_twice_is_refused(sandbox, pictures):
    """The library answers a prompt with the picture it describes: twice is a duplicate."""
    same = "a wide photograph of an empty road at dawn"
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls(
            "generate_image",
            slot="hero",
            prompt=same,
            category="photography",
            width=512,
            height=512,
        ),
        calls(
            "generate_image",
            slot="card",
            prompt=f"{same} ",
            category="photography",
            width=512,
            height=512,
        ),
        says("One picture, then."),
    )

    built = await agent.build(
        brief=BRIEF, category="hero", image_categories=["photography"], model=model
    )

    assert [one.slot for one in built.images] == ["hero"]
    assert len(pictures) == 1
    assert "say what is different about this one" in said_by_tools(model)


async def test_a_block_asks_for_no_more_pictures_than_it_is_allowed(sandbox, pictures, monkeypatch):
    monkeypatch.setattr(settings, "images_per_block", 1)
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls(
            "generate_image",
            slot="hero",
            prompt="a road at dawn",
            category="photography",
            width=512,
            height=512,
        ),
        calls(
            "generate_image",
            slot="card",
            prompt="a bridge at dusk",
            category="photography",
            width=512,
            height=512,
        ),
        says("One is enough."),
    )

    built = await agent.build(
        brief=BRIEF, category="hero", image_categories=["photography"], model=model
    )

    assert [one.slot for one in built.images] == ["hero"]
    assert "which is the limit" in said_by_tools(model)


async def test_a_block_with_nowhere_to_file_a_picture_builds_without_one(sandbox, pictures):
    model = scripted(
        calls("write_file", path=agent.ENTRY, content=FIRST),
        calls("look"),
        calls(
            "generate_image",
            slot="hero",
            prompt="a road at dawn",
            category="photography",
            width=512,
            height=512,
        ),
        says("Built it without pictures."),
    )

    built = await agent.build(brief=BRIEF, category="hero", image_categories=[], model=model)

    assert built.images == []
    assert pictures == []
    assert "no types to file a picture under" in said_by_tools(model)


async def test_the_loop_stops_itself_when_it_runs_out_of_turns(sandbox):
    """The recursion limit is the net under the budget, and it is under it."""
    model = scripted(*[calls("write_file", path=agent.ENTRY, content=FIRST) for _ in range(40)])

    built = await agent.build(brief=BRIEF, category="hero", model=model)

    assert built.files == {agent.ENTRY: FIRST}
    assert built.iterations == 0


def test_a_deployment_with_no_key_is_told_what_is_missing(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)

    with pytest.raises(agent.HarnessUnavailable) as refused:
        agent.harness_model()

    assert "OPENAI_API_KEY" in str(refused.value)
