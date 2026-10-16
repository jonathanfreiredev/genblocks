import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category
from app.components.models import Component
from app.images.models import Image


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_category(
    session: AsyncSession,
    *,
    slug: str = "hero",
    kind: str = "component",
    level: int = 2,
) -> Category:
    """Insert a category directly, for tests that need the taxonomy but not the
    whole seed."""
    category = Category(kind=kind, slug=slug, name=slug.replace("-", " ").title(), level=level)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def create_component(
    session: AsyncSession,
    *,
    category_id: uuid.UUID,
    slug: str,
    title: str | None = None,
    description: str | None = None,
) -> Component:
    """Insert a published block directly, for tests that need a vault but not a run."""
    component = Component(
        slug=slug,
        title=title or slug.replace("-", " ").title(),
        description=description or f"{slug} block",
        category_id=category_id,
        code="export function Block() { return null }",
        delivery_prompt=f"Build a {slug}",
    )
    session.add(component)
    await session.commit()
    await session.refresh(component)
    return component


async def create_image(
    session: AsyncSession,
    *,
    category_id: uuid.UUID,
    path: str,
    prompt: str = "a serene landscape",
) -> Image:
    """Insert a stock image directly, for tests that need a library but not a run."""
    image = Image(prompt=prompt, path=path, width=1024, height=768, category_id=category_id)
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image
