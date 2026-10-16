import pytest

from app.categories.models import CategoryKind
from app.categories.seed import COMPONENT_TYPES, IMAGE_TYPES, ROOTS


def _all_slugs() -> list[str]:
    slugs: list[str] = []
    for _, _, root_slug, types in ROOTS:
        slugs.append(root_slug)
        slugs.extend(slug for _, slug in types)
    return slugs


def test_there_is_one_root_per_kind():
    assert [kind for kind, _, _, _ in ROOTS] == [CategoryKind.COMPONENT, CategoryKind.IMAGE]


def test_the_seed_matches_the_planned_taxonomy():
    # The counts are a contract: the gallery is sized by them, so a change here
    # should be deliberate.
    assert len(COMPONENT_TYPES) == 25
    assert len(IMAGE_TYPES) == 8


def test_every_slug_is_unique():
    slugs = _all_slugs()
    assert len(slugs) == len(set(slugs))


@pytest.mark.parametrize("slug", _all_slugs())
def test_slugs_are_url_safe(slug: str):
    assert slug == slug.lower()
    assert slug.strip("-") == slug
    assert all(character.isalnum() or character == "-" for character in slug)


def test_every_type_has_a_name():
    for _, _, _, types in ROOTS:
        for name, _ in types:
            assert name.strip()
