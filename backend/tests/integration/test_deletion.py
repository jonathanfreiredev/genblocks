import pytest
from sqlalchemy import func, select

from app.components.models import ComponentAsset
from app.db.models import utcnow
from app.deletion import service as deletion
from app.generations.models import Generation
from app.harness.agent import ENTRY
from app.images.models import Image
from app.reports.models import Report, ReportReason, ReportStatus
from tests.helpers import BLOCK, create_category, create_component, create_image

pytestmark = pytest.mark.anyio


def _cloudinary(monkeypatch) -> list[tuple[str, bool]]:
    deleted: list[tuple[str, bool]] = []

    monkeypatch.setattr(deletion.cloudinary, "is_configured", lambda: True)

    async def destroy(path: str, *, invalidate: bool = False, client=None) -> None:
        deleted.append((path, invalidate))

    monkeypatch.setattr(deletion.cloudinary, "destroy", destroy)
    return deleted


@pytest.fixture(autouse=True)
def _forget_is_quiet(monkeypatch):
    async def forget(collection, *, ids):
        return None

    monkeypatch.setattr(deletion.vectors, "forget", forget)


async def test_deleting_an_image_removes_its_asset_and_leaves_the_block(db_session, monkeypatch):
    deleted = _cloudinary(monkeypatch)
    category = await create_category(db_session, slug="hero")
    image_category = await create_category(db_session, slug="scene", kind="image")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    image = await create_image(
        db_session, category_id=image_category.id, path="genblocks/images/picture"
    )
    db_session.add(ComponentAsset(component_id=component.id, image_id=image.id, slot="hero"))
    await db_session.commit()

    removed = await deletion.delete_image(db_session, image_id=image.id)
    assert removed is not None
    assert deleted == [("genblocks/images/picture", True)]
    assert (
        await db_session.scalar(
            select(Image).where(Image.id == image.id).execution_options(populate_existing=True)
        )
        is None
    )
    assert (
        await db_session.scalar(
            select(type(component))
            .where(type(component).id == component.id)
            .execution_options(populate_existing=True)
        )
        is not None
    )
    links = await db_session.scalar(select(func.count()).select_from(ComponentAsset))
    assert links == 0


async def test_deleting_a_component_removes_its_render_and_keeps_the_image(db_session, monkeypatch):
    deleted = _cloudinary(monkeypatch)
    category = await create_category(db_session, slug="hero")
    image_category = await create_category(db_session, slug="scene", kind="image")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    image = await create_image(
        db_session, category_id=image_category.id, path="genblocks/images/picture"
    )
    generation = Generation(
        component_id=component.id,
        attempt_no=1,
        files={ENTRY: BLOCK},
        entry=ENTRY,
        screenshot_path="genblocks/screenshots/render",
        thumbnail_path="genblocks/screenshots/render-thumb",
        verdict="published",
    )
    db_session.add(generation)
    await db_session.flush()
    component.winning_generation_id = generation.id
    db_session.add(ComponentAsset(component_id=component.id, image_id=image.id, slot="hero"))
    await db_session.commit()

    removed = await deletion.delete_component(db_session, component_id=component.id)
    assert removed is not None
    assert deleted == [
        ("genblocks/screenshots/render", True),
        ("genblocks/screenshots/render-thumb", True),
    ]
    assert (
        await db_session.scalar(
            select(type(component))
            .where(type(component).id == component.id)
            .execution_options(populate_existing=True)
        )
        is None
    )
    assert (
        await db_session.scalar(
            select(Generation)
            .where(Generation.id == generation.id)
            .execution_options(populate_existing=True)
        )
        is None
    )
    assert (
        await db_session.scalar(
            select(Image).where(Image.id == image.id).execution_options(populate_existing=True)
        )
        is not None
    )


async def test_a_hard_delete_keeps_the_report_snapshot(db_session, monkeypatch):
    _cloudinary(monkeypatch)
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    report = Report(
        component_id=component.id,
        target_kind="component",
        target_id=component.id,
        target_slug="alpha",
        target_title="Alpha",
        reason=ReportReason.MALWARE,
        status=ReportStatus.RESOLVED,
        resolution="removed",
        resolved_at=utcnow(),
    )
    db_session.add(report)
    await db_session.commit()

    await deletion.delete_component(db_session, component_id=component.id)
    kept = await db_session.scalar(
        select(Report).where(Report.id == report.id).execution_options(populate_existing=True)
    )
    assert kept is not None
    assert kept.component_id is None
    assert kept.target_kind == "component"
    assert kept.target_id == component.id
    assert kept.target_title == "Alpha"


async def test_a_cloudinary_failure_leaves_the_target_hidden(db_session, monkeypatch):
    _cloudinary(monkeypatch)
    category = await create_category(db_session, slug="scene", kind="image")
    image = await create_image(db_session, category_id=category.id, path="genblocks/images/x")

    async def refuse(path: str, *, invalidate: bool = False, client=None) -> None:
        raise deletion.cloudinary.StorageUnavailable("no")

    monkeypatch.setattr(deletion.cloudinary, "destroy", refuse)

    with pytest.raises(deletion.DeletionFailed):
        await deletion.delete_image(db_session, image_id=image.id)

    hidden = await db_session.get(Image, image.id)
    assert hidden is not None
    assert hidden.deleted_at is not None
