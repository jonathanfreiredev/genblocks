"""Give every block the render, the card crop and the live page its views need.

The seed plants blocks, attempts and scores but no pictures: a render is a
container and a browser, and the seed is meant to run without providers. This is
the other half — one look per block, through the same sandbox a real run uses,
with the desktop render and the card-width thumbnail kept in Cloudinary and the
built page kept as one document. The checks the sandbox reported are written onto
the winning attempt too, so the evidence panel is showing something that happened
rather than something the seed asserted.

It reads every block, not only the seeded ones: a block published before any of
these existed gets one here as well. One-off and idempotent — a block that already
has all three is left alone, so running it twice does not pay for the same build
twice. A thumbnail is cosmetic and its absence falls back to the render, so a
block that the newer gates would refuse is not made fatal by this script.
"""

import asyncio
import hashlib

import structlog
from sqlalchemy import select

from app.categories.models import Category  # noqa: F401  (register the tables the keys point at)
from app.components.models import Component, ComponentPreview
from app.db.session import async_session_maker
from app.generations.models import Generation
from app.harness import checks, cloudinary
from app.harness.schemas import SandboxFile
from app.tasks.models import Task  # noqa: F401  (generations point at it)
from app.users.models import User  # noqa: F401  (blocks point at it)

logger = structlog.get_logger("app.seed.screenshots")


async def main() -> None:
    """Build, render and publish the missing artifacts of every block."""
    rendered = 0
    previewed = 0
    thumbnailed = 0
    skipped = 0
    refused: list[str] = []

    async with async_session_maker() as session:
        components = list(
            await session.scalars(
                select(Component).where(Component.deleted_at.is_(None)).order_by(Component.slug)
            )
        )
        with_preview = set(await session.scalars(select(ComponentPreview.component_id)))

        for component in components:
            if component.winning_generation_id is None:
                logger.warning("block has no winning attempt", slug=component.slug)
                continue

            generation = await session.get(Generation, component.winning_generation_id)
            if generation is None:
                logger.warning("winning attempt is gone", slug=component.slug)
                continue

            wants_render = generation.screenshot_path is None
            wants_preview = component.id not in with_preview
            wants_thumbnail = generation.thumbnail_path is None

            if not wants_render and not wants_preview and not wants_thumbnail:
                logger.info("already built", slug=component.slug)
                skipped += 1
                continue

            found = await checks.check(
                [
                    SandboxFile(path=path, content=content)
                    for path, content in sorted(component.files.items())
                ]
            )
            if found.blocked:
                # A fatal check refused it: the report says which one, and the row
                # keeps what it had rather than a picture of an error page.
                logger.warning("the build was refused", slug=component.slug, report=found.report())
                # Only a missing picture of either kind leaves a hole. A block
                # that already has its render and its preview but not the crop is
                # complete enough; the crop is cosmetic, so keep the one the run
                # made and leave the published checks alone. A block that is
                # missing a render or a preview is a hole, and the run stops here.
                if wants_render or wants_preview:
                    refused.append(component.slug)
                    continue

            if wants_render and found.screenshot is not None:
                generation.screenshot_path = await cloudinary.store(
                    found.screenshot, name=f"{cloudinary.SCREENSHOTS}/{component.slug}"
                )
                rendered += 1

            if wants_preview and found.preview is not None:
                session.add(
                    ComponentPreview(
                        component_id=component.id,
                        html=found.preview,
                        bytes=len(found.preview.encode("utf-8")),
                    )
                )
                previewed += 1

            if wants_thumbnail and found.thumbnail is not None:
                # Named after its own bytes: a backfill that improves the crop
                # writes a new address, so no CDN or image optimizer can keep
                # serving the old one under the same path.
                generation.thumbnail_path = await cloudinary.store(
                    found.thumbnail,
                    name=(
                        f"{cloudinary.SCREENSHOTS}/{component.slug}-thumb-"
                        f"{hashlib.sha256(found.thumbnail).hexdigest()[:8]}"
                    ),
                    media_type=found.screenshot_media_type,
                )
                thumbnailed += 1

            # A run made only to fill a missing crop is not new evidence for the
            # panel: the checks from the run that published the block stay.
            if wants_render or wants_preview:
                generation.checks = found.record()

            await session.commit()

            passed = sum(1 for check in found.checks if check.ok)
            logger.info("built", slug=component.slug, checks=f"{passed}/{len(found.checks)}")

    logger.info(
        "renders, thumbnails and previews done",
        rendered=rendered,
        previewed=previewed,
        thumbnailed=thumbnailed,
        skipped=skipped,
        refused=len(refused),
    )

    if refused:
        # A block without a preview cannot be shown as a block. Leaving that as a
        # line in a log somebody may not read is how a library ends up with holes.
        raise SystemExit(f"These blocks could not be built: {', '.join(refused)}")


if __name__ == "__main__":
    asyncio.run(main())
