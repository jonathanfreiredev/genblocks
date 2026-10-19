import pytest
from fastapi import HTTPException

from app.components.models import Component
from app.components.service import already_built, get_component_by_slug, list_components
from app.harness.agent import ENTRY
from app.pagination import ListParams
from app.vectors import service as vectors
from tests.helpers import BLOCK, create_category, create_component

pytestmark = pytest.mark.anyio


async def _component(
    session,
    *,
    category_id,
    slug: str,
    title: str | None = None,
    description: str | None = None,
) -> Component:
    component = Component(
        slug=slug,
        title=title or slug.title(),
        description=description or f"{slug} block",
        category_id=category_id,
        files={ENTRY: BLOCK},
        entry=ENTRY,
        delivery_prompt=f"Build a {slug}",
    )
    session.add(component)
    await session.commit()
    await session.refresh(component)
    return component


async def test_listing_returns_a_page_and_the_total(db_session):
    category = await create_category(db_session, slug="hero")
    for slug in ("alpha", "bravo", "charlie"):
        await _component(db_session, category_id=category.id, slug=slug)

    components, total = await list_components(db_session, params=ListParams(limit=2))

    assert total == 3  # total ignores pagination
    assert len(components) == 2


async def test_listing_filters_by_category(db_session):
    heroes = await create_category(db_session, slug="hero")
    pricing = await create_category(db_session, slug="pricing")
    await _component(db_session, category_id=heroes.id, slug="alpha")
    await _component(db_session, category_id=pricing.id, slug="bravo")

    components, total = await list_components(
        db_session, params=ListParams(), category_id=heroes.id
    )

    assert total == 1
    assert components[0].slug == "alpha"


async def test_search_matches_the_title_or_the_description_case_insensitively(db_session):
    category = await create_category(db_session, slug="hero")
    await _component(db_session, category_id=category.id, slug="alpha", title="Sunset Hero")
    await _component(
        db_session,
        category_id=category.id,
        slug="bravo",
        title="Other",
        description="A MARKDOWN pricing block",
    )

    by_title, _ = await list_components(db_session, params=ListParams(), search="sunset")
    by_description, _ = await list_components(db_session, params=ListParams(), search="markdown")

    assert [component.slug for component in by_title] == ["alpha"]
    assert [component.slug for component in by_description] == ["bravo"]


async def test_a_component_can_be_read_by_slug(db_session):
    category = await create_category(db_session, slug="hero")
    await _component(db_session, category_id=category.id, slug="alpha")

    component = await get_component_by_slug(db_session, slug="alpha")

    assert component is not None
    # The license is filled in by the model's default, not by the caller.
    assert component.license == "MIT"


async def test_an_unknown_sort_field_is_rejected(db_session):
    with pytest.raises(HTTPException):
        await list_components(db_session, params=ListParams(sort="nope"))


async def test_a_brief_that_repeats_a_block_is_recognised(db_session, monkeypatch):
    """The duplicate guard: retrieval says how near, and the bar says how near is near."""
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    await _closest(monkeypatch, component.id, distance=0.42)

    found = await already_built(db_session, brief="A hero with a headline and one action")

    assert found is not None
    assert found[0].id == component.id
    assert found[1] == 0.42


async def test_a_brief_that_only_resembles_one_is_not(db_session, monkeypatch):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    await _closest(monkeypatch, component.id, distance=0.77)

    assert await already_built(db_session, brief="A login form with two buttons") is None


async def test_an_empty_registry_matches_nothing(db_session, monkeypatch):
    async def nothing(text, *, limit=5):
        return []

    monkeypatch.setattr(vectors, "find_components", nothing)

    assert await already_built(db_session, brief="A hero") is None


async def _closest(monkeypatch, component_id, *, distance: float) -> None:
    """Retrieval, answered with one match at a known distance."""

    async def found(text, *, limit=5):
        return [vectors.Match(id=component_id, distance=distance)]

    monkeypatch.setattr(vectors, "find_components", found)
