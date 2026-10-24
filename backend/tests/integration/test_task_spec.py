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
    """A model that answers with a type, and remembers what it was shown."""

    def __init__(self, category: str, reason: str = "the brief is a pricing section") -> None:
        self.answer = spec.CategoryAnswer(category=category, reason=reason)
        self.shown: list = []

    async def ainvoke(self, messages):
        self.shown = messages

        return self.answer


class ScriptedDesign:
    """A model that answers with a plan, and remembers what it was shown."""

    def __init__(self, planned: design.DesignPlan | None = None) -> None:
        self.answer = planned or a_plan()
        self.shown: list = []

    async def ainvoke(self, messages):
        self.shown = messages

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

    with pytest.raises(spec.UnreadableCategory, match="not a type of block"):
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
