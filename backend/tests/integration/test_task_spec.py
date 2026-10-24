"""Which type of block a brief is, decided from the taxonomy and what resembles it.

The model is scripted: what is real here is the taxonomy it chooses from and what
happens to an answer the taxonomy does not contain.
"""

import pytest

from app.design import plan as design
from app.tasks import spec
from tests.helpers import create_category

pytestmark = pytest.mark.anyio


class ScriptedSpec:
    """A model that answers with a type, and remembers every call it was shown.

    It answers in the order it was scripted, and keeps answering with the last one:
    a model that keeps inventing a type is the case the second refusal is for.
    """

    def __init__(self, *categories: str, reason: str = "the brief is a pricing section") -> None:
        self.answers = [spec.CategoryAnswer(category=one, reason=reason) for one in categories]
        self.calls: list[list] = []
        self.shown: list = []

    async def ainvoke(self, messages):
        self.calls.append(messages)
        self.shown = messages
        said = self.answers[min(len(self.calls) - 1, len(self.answers) - 1)]

        return said


class ScriptedDesign:
    """A model that answers with a plan, and can be made to fail once."""

    def __init__(self, planned: design.DesignPlan | None = None, *, off_shelf_once=False) -> None:
        self.answer = planned or a_plan()
        self.off_shelf_once = off_shelf_once
        self.calls: list[list] = []
        self.shown: list = []

    async def ainvoke(self, messages):
        self.calls.append(messages)
        self.shown = messages
        if self.off_shelf_once and len(self.calls) == 1:
            # Exactly what the real structured output raises: pydantic refuses it.
            return a_plan(display_font="Comic Sans")

        return self.answer


def a_plan(**overrides) -> design.DesignPlan:
    defaults = {
        "direction": design.Direction.PRECISION,
        "composition": design.Composition.COLUMNAR,
        "hierarchy": ["price", "plan names", "billing note"],
        "display_font": "Geist",
        "body_font": "Inter",
        "accent": design.Accent.BLUE,
        "accent_reason": "the product measures water, and blue is its material",
        "surfaces": design.Surfaces.BORDERED,
        "density": design.Density.MODERATE,
        "signature": "the recommended plan is the only one with a rule above it",
        "rationale": "precision suits a utility, and nothing blue is filed here",
    }

    return design.DesignPlan(**{**defaults, **overrides})


async def test_the_type_is_chosen_from_the_taxonomy_not_invented(db_session):
    await create_category(db_session, slug="hero")
    await create_category(db_session, slug="pricing")
    model = ScriptedSpec("pricing")

    decided = await spec.build_spec(
        db_session,
        brief="A pricing table with three tiers",
        model=model,
        design_model=ScriptedDesign(),
    )

    assert decided.category_slug == "pricing"
    assert decided.title == "A pricing table with three tiers"
    assert decided.spec["source"] == "rag"
    assert decided.spec["category"] == "pricing"
    assert decided.spec["reason"] == "the brief is a pricing section"
    assert decided.spec["design"]["direction"] == "precision"
    assert decided.spec["design"]["typography"]["body"]["package"] == "@fontsource/inter"


async def test_the_prompt_names_every_type_and_the_brief(db_session):
    await create_category(db_session, slug="hero")
    await create_category(db_session, slug="pricing")
    model = ScriptedSpec("hero")

    await spec.build_spec(
        db_session,
        brief="A hero with one line of copy",
        model=model,
        design_model=ScriptedDesign(),
    )

    system, human = model.shown
    # The list is the whole answer space: a type that is not in it cannot be chosen.
    assert "- hero: Hero" in system.content
    assert "- pricing: Pricing" in system.content
    assert "A hero with one line of copy" in human.content


async def test_an_answer_outside_the_taxonomy_is_refused(db_session):
    await create_category(db_session, slug="hero")
    await create_category(db_session, slug="pricing")

    with pytest.raises(spec.UnreadableCategory, match="twice"):
        await spec.build_spec(
            db_session,
            brief="A pricing table",
            model=ScriptedSpec("spaceship"),
            design_model=ScriptedDesign(),
        )


async def test_a_taxonomy_with_no_types_is_a_setup_mistake(db_session):
    # Level 1 is the kind itself; a block is filed under a level-2 type.
    await create_category(db_session, slug="component", level=1)

    with pytest.raises(spec.CategoryNotSeeded, match="no types of block"):
        await spec.build_spec(
            db_session,
            brief="A hero",
            model=ScriptedSpec("hero"),
            design_model=ScriptedDesign(),
        )


async def test_the_planner_is_shown_the_brief_and_the_type_it_was_filed_under(db_session):
    await create_category(db_session, slug="pricing")
    planner = ScriptedDesign()

    await spec.build_spec(
        db_session,
        brief="A pricing table with three tiers",
        model=ScriptedSpec("pricing"),
        design_model=planner,
    )

    system, human = planner.shown
    assert "- precision:" in system.content
    assert "Instrument Serif" in system.content
    assert "filed under: pricing" in human.content


async def test_a_plan_off_the_shelf_fails_before_anything_is_built(db_session):
    await create_category(db_session, slug="pricing")

    class OffShelf:
        async def ainvoke(self, messages):
            return a_plan(display_font="Comic Sans")

    with pytest.raises(spec.UnreadableDesign, match="not a family on the type shelf"):
        await spec.build_spec(
            db_session,
            brief="A pricing table",
            model=ScriptedSpec("pricing"),
            design_model=OffShelf(),
        )


async def test_an_invented_type_is_asked_again_instead_of_failing_the_task(db_session):
    """A design studio's project list is a portfolio to a model, and not to us."""
    await create_category(db_session, slug="gallery")
    await create_category(db_session, slug="blog")
    model = ScriptedSpec("portfolio", "gallery")

    decided = await spec.build_spec(
        db_session,
        brief="A design studio's recent projects, with client and year",
        model=model,
        design_model=ScriptedDesign(),
    )

    assert decided.category_slug == "gallery"
    # Two calls: the wrong answer is not a run, and the correction is cheaper than
    # the person's month.
    assert len(model.calls) == 2
    correction = model.calls[1][-1].content
    assert "'portfolio'" in correction
    assert "blog, gallery" in correction
    assert "Never invent a type" in correction


async def test_a_plan_off_the_shelf_is_asked_again_once(db_session):
    await create_category(db_session, slug="pricing")
    planner = ScriptedDesign(off_shelf_once=True)

    decided = await spec.build_spec(
        db_session,
        brief="A pricing table",
        model=ScriptedSpec("pricing"),
        design_model=planner,
    )

    assert decided.spec["design"]["typography"]["display"]["family"] == "Geist"
    assert len(planner.calls) == 2
    assert "not one this registry can build" in planner.calls[1][-1].content
