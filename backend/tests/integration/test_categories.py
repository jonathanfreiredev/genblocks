import pytest
from sqlalchemy import func, select

from app.categories.models import Category
from app.categories.seed import COMPONENT_TYPES, IMAGE_TYPES, ROOTS, seed_categories
from app.categories.service import get_category_by_slug, list_categories

pytestmark = pytest.mark.anyio


async def test_seeding_plants_both_roots_and_their_types(db_session):
    total = await seed_categories(db_session)

    assert total == len(COMPONENT_TYPES) + len(IMAGE_TYPES) + len(ROOTS)


async def test_seeding_is_idempotent(db_session):
    await seed_categories(db_session)
    after_first = await db_session.scalar(select(func.count()).select_from(Category))

    await seed_categories(db_session)
    after_second = await db_session.scalar(select(func.count()).select_from(Category))

    assert after_first == after_second


async def test_roots_have_no_parent_and_types_point_at_their_root(db_session):
    await seed_categories(db_session)
    categories = await list_categories(db_session)

    roots = [category for category in categories if category.level == 1]
    types = [category for category in categories if category.level == 2]

    assert len(roots) == len(ROOTS)
    assert all(root.parent_id is None for root in roots)

    root_ids = {root.id for root in roots}
    assert all(category.parent_id in root_ids for category in types)


async def test_listing_can_be_filtered_by_kind(db_session):
    await seed_categories(db_session)

    components = await list_categories(db_session, kind="component")

    assert all(category.kind == "component" for category in components)
    assert {category.slug for category in components} >= {"components", "hero", "pricing"}


async def test_a_type_can_be_read_by_slug(db_session):
    await seed_categories(db_session)

    hero = await get_category_by_slug(db_session, slug="hero")

    assert hero is not None
    assert hero.name == "Hero"
    assert hero.level == 2
