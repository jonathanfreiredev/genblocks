"""Give the seeded blocks the render their rows claim.

The seed plants blocks, attempts and scores but no screenshot: a screenshot is a
container and a browser, and the seed is meant to run without providers. This is
the other half — one look per block, through the same sandbox a real run uses, and
the light render kept in Cloudinary. The checks the sandbox reported are written
onto the winning attempt too, so the evidence panel is showing something that
happened rather than something the seed asserted.

One-off and idempotent: a block that already has a render is left alone, so running
it twice does not buy the same picture twice.
"""

import asyncio

import structlog
from sqlalchemy import select

from app.categories.models import Category  # noqa: F401  (register the tables the keys point at)
from app.components.models import Component
from app.db.session import async_session_maker
from app.generations.models import Generation
from app.harness import checks, cloudinary
from app.harness.schemas import SandboxFile
from app.tasks.models import Task  # noqa: F401  (generations point at it)
from app.users.models import User  # noqa: F401  (blocks point at it)

logger = structlog.get_logger("app.seed.screenshots")


async def main() -> None:
    """Render every seeded block that has no render yet, and store the light one."""
    rendered = 0
    skipped = 0

    async with async_session_maker() as session:
        components = list(
            await session.scalars(
                select(Component).where(Component.deleted_at.is_(None)).order_by(Component.slug)
            )
        )

        for component in components:
            if component.winning_generation_id is None:
                logger.warning("block has no winning attempt", slug=component.slug)
                continue

            generation = await session.get(Generation, component.winning_generation_id)
            if generation is None:
                logger.warning("winning attempt is gone", slug=component.slug)
                continue

            if generation.screenshot_path:
                logger.info("already rendered", slug=component.slug)
                skipped += 1
                continue

            found = await checks.check(
                [
                    SandboxFile(path=path, content=content)
                    for path, content in sorted(component.files.items())
                ]
            )
            if found.screenshot is None:
                # A fatal check refused it: the report says which one, and the row
                # keeps no render rather than a picture of an error page.
                logger.warning("nothing to keep", slug=component.slug, report=found.report())
                continue

            generation.screenshot_path = await cloudinary.store(
                found.screenshot, name=f"{cloudinary.SCREENSHOTS}/{component.slug}"
            )
            generation.checks = found.record()
            await session.commit()
            rendered += 1

            passed = sum(1 for check in found.checks if check.ok)
            logger.info("rendered", slug=component.slug, checks=f"{passed}/{len(found.checks)}")

    logger.info("screenshots done", rendered=rendered, skipped=skipped)


if __name__ == "__main__":
    asyncio.run(main())
