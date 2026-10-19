"""What the judge is asked, and what it is shown.

The rubric is the whole of the judge's standard, so it is worth reading as text:
who it is and what it scores by in the stable half, and this attempt — brief,
every file, findings, render — in the half that changes. The findings are tested
here too, because they are the only thing the judge hears about the sandbox, and
both readers of them (the builder and the judge) read the same rendering.
"""

from app.harness.schemas import SandboxCheck, SandboxResult, SandboxViolation
from app.judge.prompts import about_component, about_image, system_prompt
from app.judge.rubrics import COMPONENTS

PNG = b"\x89PNG\r\n\x1a\n"
PNG_DARK = b"\x89PNG\r\n\x1a\ndark"
ENTRY = "src/Block.tsx"
PART = "src/parts/Rule.tsx"
CODE = "export default function Block() {\n  return <section>Hi</section>;\n}"
RULE = "export default function Rule() {\n  return <hr />;\n}"


def found(**overrides) -> SandboxResult:
    """What a sandbox that built a page and found two things reports."""
    defaults = {
        "checks": [
            SandboxCheck(name="typecheck", ok=True),
            SandboxCheck(name="layout:phone", ok=False, detail="The block is 40px wider."),
        ],
        "violations": [
            SandboxViolation(
                id="color-contrast", impact="serious", help="Enough contrast.", nodes=3
            )
        ],
        "screenshot": PNG,
        "screenshot_dark": PNG_DARK,
    }

    return SandboxResult(**{**defaults, **overrides})


def text_of(parts: list[dict]) -> str:
    return parts[0]["text"]


def test_the_stable_half_is_who_the_judge_is_and_the_rubric():
    prompt = system_prompt(COMPONENTS)

    assert "independent reader" in prompt
    assert COMPONENTS.text in prompt


def test_the_artifact_arrives_with_the_brief_every_file_and_the_findings():
    parts = about_component(
        brief="A pricing page",
        files={PART: RULE, ENTRY: CODE},
        found=found(),
    )

    said = text_of(parts)
    assert "A pricing page" in said
    # Every file, named by its path: a judge that only saw the entry point would be
    # scoring a fragment of a project.
    assert ENTRY in said
    assert PART in said
    assert CODE in said
    assert RULE in said
    # Every check is named, passing or not: a judge that only hears about
    # failures cannot tell a block that passed one from one that was never asked.
    assert "- typecheck: ok" in said
    assert "- layout:phone: failed — The block is 40px wider." in said
    assert "- axe color-contrast (serious, 3 nodes): Enough contrast." in said


def test_the_render_is_attached_twice_and_named_by_ground():
    parts = about_component(brief="b", files={ENTRY: CODE}, found=found())

    # Light, then dark, each said out loud: the judge has to know which picture it
    # is scoring, and a palette that only holds on one of them is half a design.
    images = [part for part in parts if part["type"] == "image_url"]
    assert len(images) == 2
    assert all(one["image_url"]["url"].startswith("data:image/png;base64,") for one in images)

    said = " ".join(part["text"] for part in parts if part["type"] == "text")
    assert "On the light page:" in said
    assert "On the dark page:" in said


def test_a_run_with_no_render_says_so_instead_of_looking_like_a_good_one():
    parts = about_component(
        brief="b", files={ENTRY: CODE}, found=found(screenshot=None, screenshot_dark=None)
    )

    assert len(parts) == 1
    assert "There is no render" in text_of(parts)


def test_a_sandbox_that_reported_nothing_still_reports_that():
    assert SandboxResult().report() == "- the sandbox reported nothing"


def test_a_sandbox_with_nothing_to_complain_about_still_lists_its_checks():
    quiet = SandboxResult(checks=[SandboxCheck(name="render", ok=True)])

    assert quiet.report() == "- render: ok"


def test_an_image_arrives_with_the_prompt_that_asked_for_it():
    parts = about_image(prompt="An abstract blue field", image=PNG, width=1536, height=1024)

    assert "An abstract blue field" in text_of(parts)
    assert "1536×1024" in text_of(parts)
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_an_image_can_arrive_in_the_format_it_came_in():
    parts = about_image(prompt="p", image=PNG, width=1, height=1, media_type="image/webp")

    assert parts[1]["image_url"]["url"].startswith("data:image/webp;base64,")
