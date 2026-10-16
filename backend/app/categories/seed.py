"""The seed taxonomy, and the idempotent upsert that plants it.

Two levels, planted by hand rather than grown: the vault is meant to read as an
archive, so the types are a curated set, not whatever the generator happened to
produce. The generator picks one of these; it never invents a top-level kind.

Run it with::

    python -m app.categories.seed
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category, CategoryKind
from app.db.session import async_session_maker

# Level 2 of the "component" kind. Ordered as a gallery would read, not
# alphabetically.
COMPONENT_TYPES: tuple[tuple[str, str], ...] = (
    ("Hero", "hero"),
    ("Navbar", "navbar"),
    ("Footer", "footer"),
    ("Features", "features"),
    ("CTA", "cta"),
    ("Pricing", "pricing"),
    ("Testimonials", "testimonials"),
    ("Social proof", "social-proof"),
    ("Stats", "stats"),
    ("FAQ", "faq"),
    ("Contact", "contact"),
    ("Forms & Auth", "forms-auth"),
    ("Cards", "cards"),
    ("Gallery", "gallery"),
    ("Blog", "blog"),
    ("Team", "team"),
    ("Tables", "tables"),
    ("Dashboard", "dashboard"),
    ("Charts", "charts"),
    ("States", "states"),
    ("Onboarding", "onboarding"),
    ("Banners", "banners"),
    ("Integrations", "integrations"),
    ("Timeline", "timeline"),
    ("Newsletter & Waitlist", "newsletter-waitlist"),
)

# Level 2 of the "image" kind, the stock library's own taxonomy.
IMAGE_TYPES: tuple[tuple[str, str], ...] = (
    ("Illustration", "illustration"),
    ("Abstract & Background", "abstract-background"),
    ("Texture & Pattern", "texture-pattern"),
    ("Product & UI mockup", "product-mockup"),
    ("Photography", "photography"),
    ("Spot & Icon", "spot-icon"),
    ("Avatar", "avatar"),
    ("Scene", "scene"),
)

# Level 1 roots, each with the level 2 types that hang off it.
ROOTS: tuple[tuple[str, str, str, tuple[tuple[str, str], ...]], ...] = (
    (CategoryKind.COMPONENT, "Components", "components", COMPONENT_TYPES),
    (CategoryKind.IMAGE, "Images", "images", IMAGE_TYPES),
)


async def seed_categories(session: AsyncSession) -> int:
    """Upsert the roots and their types, keyed by slug, and return the total.

    Idempotent: re-running it renames or reparents a category whose seed entry
    changed, and leaves everything else alone.
    """
    existing = {category.slug: category for category in await session.scalars(select(Category))}

    for kind, root_name, root_slug, types in ROOTS:
        root = _upsert(
            session,
            existing,
            slug=root_slug,
            name=root_name,
            kind=kind,
            level=1,
            parent_id=None,
        )
        # The children need the root's id, which only exists after a flush.
        await session.flush()

        for name, slug in types:
            _upsert(
                session,
                existing,
                slug=slug,
                name=name,
                kind=kind,
                level=2,
                parent_id=root.id,
            )

    await session.commit()
    return len(existing)


def _upsert(
    session: AsyncSession,
    existing: dict[str, Category],
    *,
    slug: str,
    name: str,
    kind: str,
    level: int,
    parent_id: uuid.UUID | None,
) -> Category:
    category = existing.get(slug)

    if category is None:
        category = Category(slug=slug, name=name, kind=kind, level=level, parent_id=parent_id)
        session.add(category)
        existing[slug] = category
        return category

    category.name = name
    category.kind = kind
    category.level = level
    category.parent_id = parent_id
    return category


async def _main() -> None:
    async with async_session_maker() as session:
        total = await seed_categories(session)
    print(f"Seeded {total} categories")


if __name__ == "__main__":
    asyncio.run(_main())
