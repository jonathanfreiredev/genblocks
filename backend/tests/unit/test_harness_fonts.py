"""The type shelf, read against the scaffold it installs.

A family in the catalog is a promise that the block can import it, and a family in
the scaffold's dependencies that the catalog does not list is an import the agent
will never be told about. Both directions are checked here, together with the
generated table in the skill: the agent reads the document, the image installs the
packages, and the two have to be the same shelf.
"""

import json
from pathlib import Path

import pytest

from app.harness import fonts, skills

SCAFFOLD = Path(__file__).resolve().parents[2] / "app" / "harness" / "scaffold"
LATIN_WEIGHTS = {str(weight) for weight in range(100, 1000, 100)}


def scaffold_dependencies() -> dict[str, str]:
    package = json.loads((SCAFFOLD / "package.json").read_text(encoding="utf-8"))

    return package["dependencies"]


def test_every_catalog_family_is_installed_by_the_scaffold():
    installed = scaffold_dependencies()

    missing = [family.package for family in fonts.FAMILIES if family.package not in installed]

    assert missing == []


def test_no_font_package_is_missing_from_the_catalog():
    listed = {family.package for family in fonts.FAMILIES}
    installed = {name for name in scaffold_dependencies() if name.startswith("@fontsource/")}

    assert installed - listed == set()


def test_the_groups_are_the_ones_the_catalog_uses():
    slugs = [group.slug for group in fonts.GROUPS]

    assert len(slugs) == len(set(slugs))
    assert {family.group for family in fonts.FAMILIES} == set(slugs)


def test_a_family_says_which_weights_it_ships():
    for family in fonts.FAMILIES:
        assert family.weights, family.package
        assert set(family.weights) <= LATIN_WEIGHTS, family.package
        assert list(family.weights) == sorted(family.weights, key=int), family.package


def test_no_family_or_package_is_listed_twice():
    packages = [family.package for family in fonts.FAMILIES]
    names = [family.family for family in fonts.FAMILIES]

    assert len(packages) == len(set(packages))
    assert len(names) == len(set(names))


def test_weights_read_as_a_range_only_when_the_family_fills_it():
    filled = fonts.Family(
        "@fontsource/geist", "Geist", "neutral-sans", ("300", "400", "500"), True, ""
    )
    sparse = fonts.Family("@fontsource/geist", "Geist", "neutral-sans", ("400", "700"), False, "")
    gapped = fonts.Family(
        "@fontsource/geist", "Geist", "neutral-sans", ("400", "500", "700"), False, ""
    )

    assert fonts.weights_text(filled) == "300-500"
    assert fonts.weights_text(sparse) == "400 700"
    assert fonts.weights_text(gapped) == "400 500 700"


def test_the_document_is_the_catalog_and_nothing_else():
    document = fonts.current()

    assert fonts.render(document) == document


def test_a_document_without_markers_is_a_mistake_not_a_rewrite():
    with pytest.raises(ValueError, match="families:begin"):
        fonts.render("# Type\n\nno markers here\n")


def test_the_skill_is_on_the_shelf():
    assert skills.read("fonts").startswith("# Type on this shelf")
    assert "fonts" in skills.index()
    assert "Instrument Serif" in skills.read("fonts")
