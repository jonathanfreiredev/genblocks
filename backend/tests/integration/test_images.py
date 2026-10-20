import pytest

from app.images.models import Image
from app.images.service import get_image, get_image_by_slug, list_images
from app.pagination import ListParams
from tests.helpers import create_category

pytestmark = pytest.mark.anyio


async def _image(session, *, category_id, path: str, prompt: str = "a serene landscape") -> Image:
    image = Image(
        prompt=prompt,
        path=path,
        width=1024,
        height=768,
        category_id=category_id,
    )
    session.add(image)
    await session.commit()
    await session.refresh(image)
    return image


async def test_listing_filters_by_category_and_prompt(db_session):
    scenes = await create_category(db_session, slug="scene", kind="image")
    avatars = await create_category(db_session, slug="avatar", kind="image")
    landscape = await _image(
        db_session,
        category_id=scenes.id,
        path="images/landscape",
        prompt="a serene landscape",
    )
    await _image(
        db_session,
        category_id=avatars.id,
        path="images/portrait",
        prompt="a studio portrait",
    )

    by_category, _ = await list_images(db_session, params=ListParams(), category_id=scenes.id)
    by_prompt, _ = await list_images(db_session, params=ListParams(), search="portrait")

    assert [image.path for image in by_category] == [landscape.path]
    assert [image.path for image in by_prompt] == ["images/portrait"]


async def test_an_image_can_be_read_by_id(db_session):
    scenes = await create_category(db_session, slug="scene", kind="image")
    image = await _image(db_session, category_id=scenes.id, path="images/landscape")

    loaded = await get_image(db_session, image_id=image.id)

    assert loaded is not None
    assert loaded.license == "MIT"


async def test_an_image_can_be_read_by_slug(db_session):
    scenes = await create_category(db_session, slug="scene", kind="image")
    image = await _image(db_session, category_id=scenes.id, path="images/landscape")

    loaded = await get_image_by_slug(db_session, slug=image.slug)

    assert loaded is not None
    assert loaded.id == image.id
    assert loaded.slug == "landscape"


async def test_an_image_carries_its_generation_panel(db_session):
    """The same panel a component shows: model, scores, rubric and trace."""
    scenes = await create_category(db_session, slug="scene", kind="image")
    image = await _image(db_session, category_id=scenes.id, path="images/landscape")
    image.model = "flux-2-pro"
    image.scores = {"visual": 88, "prompt_fit": 91, "compliance": 100}
    image.rubric_version = "images-v1"
    image.langfuse_trace_id = "trace-123"
    await db_session.commit()

    loaded = await get_image(db_session, image_id=image.id)

    assert loaded.model == "flux-2-pro"
    assert loaded.scores["prompt_fit"] == 91
    assert loaded.rubric_version == "images-v1"
    assert loaded.langfuse_trace_id == "trace-123"
