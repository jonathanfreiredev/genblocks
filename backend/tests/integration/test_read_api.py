"""The read surface of the API, as the web app consumes it.

Every endpoint here is public: a visitor browses the vault, the library and the
taxonomy without signing in, and no call below carries a token.
"""

import uuid

import pytest

from app.generations.models import Generation
from app.harness.agent import ENTRY
from tests.helpers import create_category, create_component, create_image

pytestmark = pytest.mark.anyio


async def test_the_vault_reads_are_public(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    image = await create_image(db_session, category_id=category.id, path="images/landscape")

    urls = [
        "/v1/categories",
        "/v1/components",
        f"/v1/components/{component.id}",
        f"/v1/components/{component.id}/generations",
        "/v1/components/by-slug/alpha",
        "/v1/images",
        f"/v1/images/{image.id}",
    ]

    for url in urls:
        assert (await client.get(url)).status_code == 200, url


async def test_categories_come_back_as_a_tree(client, db_session):
    await create_category(db_session, slug="hero")
    await create_category(db_session, slug="avatar", kind="image")

    body = (await client.get("/v1/categories")).json()

    # ``parent_id`` and ``level`` travel with each node, so the tree is rebuilt
    # from this one response.
    assert {category["slug"] for category in body} == {"hero", "avatar"}
    assert all("parent_id" in category and "level" in category for category in body)


async def test_categories_can_be_narrowed_to_one_kind(client, db_session):
    await create_category(db_session, slug="hero")
    await create_category(db_session, slug="avatar", kind="image")

    body = (await client.get("/v1/categories", params={"kind": "image"})).json()

    assert [category["slug"] for category in body] == ["avatar"]


async def test_an_unknown_category_kind_is_rejected(client):
    assert (await client.get("/v1/categories", params={"kind": "color"})).status_code == 422


async def test_components_come_back_as_a_page_of_cards(client, db_session):
    category = await create_category(db_session, slug="hero")
    for slug in ("alpha", "bravo", "charlie"):
        await create_component(db_session, category_id=category.id, slug=slug)

    body = (await client.get("/v1/components", params={"limit": 2})).json()

    assert body["total"] == 3  # the total ignores pagination
    assert body["limit"] == 2
    assert len(body["items"]) == 2
    # A card needs no code: the full block is a separate read.
    assert "code" not in body["items"][0]


async def test_components_can_be_filtered_by_category_and_searched(client, db_session):
    heroes = await create_category(db_session, slug="hero")
    pricing = await create_category(db_session, slug="pricing")
    await create_component(db_session, category_id=heroes.id, slug="alpha", title="Sunset Hero")
    await create_component(db_session, category_id=pricing.id, slug="bravo", title="Simple Pricing")

    by_category = (
        await client.get("/v1/components", params={"category_id": str(heroes.id)})
    ).json()
    by_text = (await client.get("/v1/components", params={"search": "pricing"})).json()

    assert [item["slug"] for item in by_category["items"]] == ["alpha"]
    assert [item["slug"] for item in by_text["items"]] == ["bravo"]


async def test_a_component_is_read_in_full_by_id(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    body = (await client.get(f"/v1/components/{component.id}")).json()

    assert body["slug"] == "alpha"
    assert body["entry"] == component.entry
    assert body["files"] == component.files
    assert body["delivery_prompt"] == component.delivery_prompt
    assert body["license"] == "MIT"


async def test_a_component_is_read_in_full_by_slug(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    body = (await client.get("/v1/components/by-slug/alpha")).json()

    assert body["id"] == str(component.id)


async def test_an_unknown_component_is_not_found(client):
    assert (await client.get(f"/v1/components/{uuid.uuid4()}")).status_code == 404
    assert (await client.get("/v1/components/by-slug/nope")).status_code == 404


async def test_a_components_attempt_history_is_public_and_oldest_first(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    db_session.add_all(
        [
            Generation(
                component_id=component.id,
                attempt_no=2,
                files={ENTRY: "b"},
                entry=ENTRY,
                verdict="published",
            ),
            Generation(
                component_id=component.id,
                attempt_no=1,
                files={ENTRY: "a"},
                entry=ENTRY,
                verdict="rejected",
            ),
        ]
    )
    await db_session.commit()

    body = (await client.get(f"/v1/components/{component.id}/generations")).json()

    # The history is the product's argument, so it reads in the order it was made.
    assert [attempt["attempt_no"] for attempt in body] == [1, 2]
    assert [attempt["verdict"] for attempt in body] == ["rejected", "published"]
    assert body[1]["langfuse_trace_id"] is None


async def test_an_unknown_components_attempt_history_is_not_found(client):
    response = await client.get(f"/v1/components/{uuid.uuid4()}/generations")

    assert response.status_code == 404
    assert response.json()["detail"] == "Component not found."


async def test_a_typo_in_a_query_parameter_is_rejected(client):
    assert (await client.get("/v1/components", params={"limt": 2})).status_code == 422


async def test_an_unknown_sort_field_is_rejected(client):
    assert (await client.get("/v1/components", params={"sort": "nope"})).status_code == 422


async def test_images_come_back_with_their_generation_panel(client, db_session):
    scenes = await create_category(db_session, slug="scene", kind="image")
    image = await create_image(db_session, category_id=scenes.id, path="images/landscape")
    image.model = "flux-2-pro"
    image.scores = {"visual": 88, "prompt_fit": 91, "compliance": 100}
    image.rubric_version = "images-v1"
    await db_session.commit()

    body = (await client.get("/v1/images", params={"search": "landscape"})).json()

    assert body["total"] == 1
    # ``path`` is the Cloudinary public id, not a URL: the client picks the host.
    assert body["items"][0]["path"] == image.path
    assert body["items"][0]["scores"] == {"visual": 88, "prompt_fit": 91, "compliance": 100}


async def test_an_image_is_read_by_id(client, db_session):
    scenes = await create_category(db_session, slug="scene", kind="image")
    image = await create_image(db_session, category_id=scenes.id, path="images/landscape")

    assert (await client.get(f"/v1/images/{image.id}")).json()["id"] == str(image.id)
    assert (await client.get(f"/v1/images/{uuid.uuid4()}")).status_code == 404
