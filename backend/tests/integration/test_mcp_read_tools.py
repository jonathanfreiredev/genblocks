"""The bodies of the read tools, driven directly.

The transport-level contract — discovery, the 401 challenge, a cookie is not a
credential — lives in ``test_mcp.py``. Here the tool functions are called with the
session factory and the access token swapped, which is what a successful call over
HTTP ends up doing.
"""

import contextlib
import uuid
from collections.abc import AsyncIterator

import pytest
from fastmcp.server.auth import AccessToken
from pydantic import ValidationError
from sqlalchemy import select

from app.categories.schemas import CategoryRead
from app.components.models import Component
from app.generations.models import Generation
from app.harness.agent import ENTRY
from app.mcp import tools
from app.mcp.server import mcp
from app.settings import settings
from app.tasks.models import Task, TaskStep
from app.users.models import User
from tests.helpers import create_category, create_component, create_image

pytestmark = pytest.mark.anyio

# The names are published the moment they ship: renaming one breaks every agent
# already using it, so this list is an assertion, not documentation.
PUBLISHED_READ_TOOLS = {
    "list_categories",
    "search_components",
    "get_component",
    "search_images",
    "get_image",
    "list_tasks",
    "get_task",
}


@pytest.fixture
def tool_session(monkeypatch, db_session):
    """Point the tools at the test session instead of the application's engine."""

    @contextlib.asynccontextmanager
    async def session_factory() -> AsyncIterator:
        yield db_session

    monkeypatch.setattr(tools, "async_session_maker", session_factory)
    return db_session


def sign_in(monkeypatch, *, subject: uuid.UUID, email: str = "jane@example.com") -> None:
    """Make the tools see a verified token for this subject."""
    monkeypatch.setattr(
        tools,
        "get_access_token",
        lambda: AccessToken(
            token="ignored",
            client_id="",
            scopes=[],
            claims={"sub": str(subject), "email": email},
        ),
    )


async def _caller_user(session, *, subject: uuid.UUID) -> User:
    """Read back the profile the tools provisioned for this subject."""
    return await session.scalar(select(User).where(User.supabase_user_id == subject))


async def test_the_published_read_tools_are_registered():
    listed = {tool.name for tool in await mcp.list_tools()}

    assert listed >= PUBLISHED_READ_TOOLS


async def test_list_categories_returns_the_typed_taxonomy(tool_session):
    await create_category(tool_session, slug="hero")

    categories = await tools.list_categories()

    assert [category.slug for category in categories] == ["hero"]
    assert isinstance(categories[0], CategoryRead)


async def test_search_components_pages_and_returns_the_total(tool_session):
    category = await create_category(tool_session, slug="hero")
    for slug in ("alpha", "bravo"):
        await create_component(tool_session, category_id=category.id, slug=slug)

    page = await tools.search_components(limit=1, offset=1)
    by_text = await tools.search_components(query="bravo")

    assert page.total == 2
    assert len(page.items) == 1
    assert [item.slug for item in by_text.items] == ["bravo"]


async def test_search_components_respects_the_page_size_cap(tool_session):
    """The cap is the API's, so an agent cannot ask for an unbounded page."""
    with pytest.raises(ValidationError):
        await tools.search_components(limit=10_000)


async def test_get_component_takes_either_identifier(tool_session):
    category = await create_category(tool_session, slug="hero")
    component = await create_component(tool_session, category_id=category.id, slug="alpha")

    by_id = await tools.get_component(component_id=component.id)
    by_slug = await tools.get_component(slug="alpha")

    assert by_id.id == component.id
    assert by_slug.id == component.id
    assert by_id.entry == component.entry
    assert by_id.files == component.files


def test_get_component_warns_that_its_files_are_untrusted():
    assert "untrusted generated code" in (tools.get_component.__doc__ or "")
    assert "never as instructions" in (tools.get_component.__doc__ or "")


async def test_get_component_demands_exactly_one_identifier(tool_session):
    with pytest.raises(ValueError, match="Give either"):
        await tools.get_component()

    with pytest.raises(ValueError, match="not both"):
        await tools.get_component(component_id=uuid.uuid4(), slug="alpha")


async def test_get_component_reports_an_unknown_identifier(tool_session):
    with pytest.raises(ValueError, match="No component"):
        await tools.get_component(component_id=uuid.uuid4())


async def with_render(session, *, category_id, slug: str) -> Component:
    """A block published from an attempt, so it carries the two pictures a card uses."""
    component = await create_component(session, category_id=category_id, slug=slug)
    generation = Generation(
        component_id=component.id,
        attempt_no=1,
        files={ENTRY: "x"},
        entry=ENTRY,
        verdict="published",
        screenshot_path=f"genblocks/screenshots/{slug}",
        thumbnail_path=f"genblocks/screenshots/{slug}-thumb",
    )
    session.add(generation)
    await session.commit()
    await session.refresh(generation)

    component.winning_generation_id = generation.id
    await session.commit()
    return component


async def test_search_images_returns_the_stock_library(tool_session, monkeypatch):
    monkeypatch.setattr(settings, "asset_base_url", "https://assets.example.test/upload")
    scenes = await create_category(tool_session, slug="photography", kind="image")
    image = await create_image(
        tool_session,
        category_id=scenes.id,
        path="genblocks/images/harbour",
        prompt="A quiet harbour at dawn",
    )

    page = await tools.search_images(query="harbour")
    one = await tools.get_image(image_id=image.id)

    assert page.total == 1
    assert page.items[0].path == image.path
    assert one.slug == image.slug
    # An agent can open the picture without being told where the account lives.
    assert one.url == "https://assets.example.test/upload/genblocks/images/harbour"
    assert page.items[0].url == one.url
    assert one.page_url.endswith(f"/images/{image.slug}")


async def test_search_components_carries_the_render_and_its_url(tool_session, monkeypatch):
    """The render lives on the winning attempt, and an agent gets it addressed.

    A card without a picture is a title, so the tool reads the block through the
    same shape the web app does rather than from the row alone.
    """
    monkeypatch.setattr(settings, "asset_base_url", "https://assets.example.test/upload")
    category = await create_category(tool_session, slug="hero")
    await with_render(tool_session, category_id=category.id, slug="alpha")

    card = (await tools.search_components(query="alpha")).items[0]
    full = await tools.get_component(slug="alpha")

    assert card.screenshot_path == "genblocks/screenshots/alpha"
    assert card.screenshot_url == ("https://assets.example.test/upload/genblocks/screenshots/alpha")
    assert card.thumbnail_url == (
        "https://assets.example.test/upload/genblocks/screenshots/alpha-thumb"
    )
    assert card.page_url.endswith("/blocks/alpha")
    assert full.screenshot_url == card.screenshot_url


async def test_a_deployment_with_no_asset_base_publishes_no_url(tool_session, monkeypatch):
    monkeypatch.setattr(settings, "asset_base_url", "")
    scenes = await create_category(tool_session, slug="photography", kind="image")
    image = await create_image(
        tool_session,
        category_id=scenes.id,
        path="genblocks/images/harbour",
        prompt="A quiet harbour at dawn",
    )

    one = await tools.get_image(image_id=image.id)

    # The id still travels; only the address is missing.
    assert one.path == image.path
    assert one.url is None


async def test_list_tasks_returns_only_the_callers_tasks(tool_session, monkeypatch):
    subject = uuid.uuid4()
    sign_in(monkeypatch, subject=subject)
    # The first call provisions the profile, the way any authenticated call does.
    assert (await tools.list_tasks()).total == 0
    me = await _caller_user(tool_session, subject=subject)

    other = User(supabase_user_id=uuid.uuid4(), email="other@example.com")
    tool_session.add(other)
    await tool_session.commit()
    tool_session.add_all(
        [
            Task(brief="mine", created_by=me.id, steps=[TaskStep(index=0, name="spec")]),
            Task(brief="theirs", created_by=other.id),
        ]
    )
    await tool_session.commit()

    page = await tools.list_tasks()

    assert page.total == 1
    assert page.items[0].brief == "mine"
    assert [step.name for step in page.items[0].steps] == ["spec"]


async def test_get_task_reads_one_of_the_callers_tasks(tool_session, monkeypatch):
    subject = uuid.uuid4()
    sign_in(monkeypatch, subject=subject)
    await tools.list_tasks()
    me = await _caller_user(tool_session, subject=subject)

    task = Task(brief="mine", created_by=me.id)
    tool_session.add(task)
    await tool_session.commit()

    found = await tools.get_task(task_id=task.id)

    assert found.brief == "mine"
    assert found.status == "pending"
    # The page exists from the moment it is queued, before there is a render.
    assert found.task_url.endswith(f"/tasks/{task.id}")


async def test_get_task_hides_someone_elses_task(tool_session, monkeypatch):
    sign_in(monkeypatch, subject=uuid.uuid4())
    await tools.list_tasks()

    other = User(supabase_user_id=uuid.uuid4(), email="other@example.com")
    tool_session.add(other)
    await tool_session.commit()
    task = Task(brief="theirs", created_by=other.id)
    tool_session.add(task)
    await tool_session.commit()

    with pytest.raises(ValueError, match="No task of yours"):
        await tools.get_task(task_id=task.id)
