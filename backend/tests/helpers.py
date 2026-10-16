from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category


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
