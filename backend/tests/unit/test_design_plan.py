"""The plan: closed vocabulary, real packages, and a rendering both readers share."""

import pytest
from pydantic import ValidationError

from app.design import plan as design


def a_plan(**overrides) -> design.DesignPlan:
    """A plan that follows the rules, so a test can break exactly one of them."""
    defaults = {
        "direction": design.Direction.EDITORIAL,
        "composition": design.Composition.ASYMMETRIC,
        "hierarchy": ["headline", "price", "details"],
        "display_font": "Instrument Serif",
        "body_font": "Geist",
        "mono_font": None,
        "accent": design.Accent.ORANGE,
        "accent_reason": "the subject is fired clay and the page should feel worked",
        "surfaces": design.Surfaces.DIVIDED,
        "density": design.Density.SPARSE,
        "signature": "prices set at display size",
        "avoid": ["identical cards", "decorative gradients"],
        "rationale": "editorial suits a craft product; the last pricings were precision",
    }

    return design.DesignPlan(**{**defaults, **overrides})


def test_a_family_that_is_not_on_the_shelf_is_refused():
    with pytest.raises(ValidationError, match="not a family on the type shelf"):
        a_plan(display_font="Comic Sans")


def test_a_family_name_is_resolved_case_insensitively():
    planned = a_plan(display_font="instrument serif")

    assert planned.display_font == "Instrument Serif"


def test_the_plan_keeps_the_package_the_visitor_installs():
    stored = design.as_dict(a_plan())

    assert stored["typography"]["display"] == {
        "family": "Instrument Serif",
        "package": "@fontsource/instrument-serif",
    }
    assert stored["typography"]["mono"] is None


def test_a_mono_is_kept_when_the_plan_names_one():
    stored = design.as_dict(a_plan(mono_font="JetBrains Mono"))

    assert stored["typography"]["mono"]["package"] == "@fontsource/jetbrains-mono"


def test_a_hierarchy_needs_at_least_two_stops():
    with pytest.raises(ValidationError):
        a_plan(hierarchy=["only one thing"])


def test_the_render_names_every_decision_the_builder_must_follow():
    said = design.render(design.as_dict(a_plan()))

    for expected in (
        "Direction: editorial",
        "Composition: asymmetric",
        "Hierarchy: headline > price > details",
        "Instrument Serif",
        "Geist",
        "accent orange",
        "surfaces divided",
        "Density: sparse",
        "Signature: prices set at display size",
        "Avoid: identical cards; decorative gradients",
    ):
        assert expected in said


def test_a_block_without_a_plan_says_so_rather_than_inventing_one():
    assert "No design plan" in design.render(None)


def test_the_vocabulary_names_every_value_the_schema_accepts():
    said = design.vocabulary()

    for value in design.Direction:
        assert f"- {value.value}:" in said
    for value in design.Density:
        assert f"- {value.value}:" in said
    for value in design.Accent:
        assert value.value in said


def test_the_planner_is_shown_every_family_on_the_shelf():
    said = design.shelf()

    for family in design.SHELF:
        assert family.family in said


def test_an_unpolished_brief_has_a_direction_to_choose():
    """Brutalist and industrial requests are a temper, not a missing skill."""
    assert design.Direction.INDUSTRIAL.value == "industrial"
    assert "- industrial:" in design.vocabulary()


def test_the_planner_is_shown_one_plan_that_decides_and_one_that_does_not():
    said = design.examples()

    assert "accent: sky" in said
    assert "What goes wrong" in said
    # The vague one is the point: it is what the fields exist to rule out.
    assert "a tasteful colour" in said


def test_the_example_warns_against_copying_its_answers():
    """Few-shot anchors; the closing line is what keeps it from becoming a template."""
    assert "Copy the shape of that decision, not its answers" in design.examples()
