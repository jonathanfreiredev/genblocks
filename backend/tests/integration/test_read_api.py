"""The read surface of the API, as the web app consumes it.

Every endpoint here is public: a visitor browses the vault, the library and the
taxonomy without signing in, and no call below carries a token.
"""

import uuid

import pytest

from app.components.models import ComponentPreview
from app.deletion import service as deletion
from app.generations.models import Generation
from app.harness.agent import ENTRY
from app.users.models import User
from tests.helpers import create_category, create_component, create_image

pytestmark = pytest.mark.anyio


async def test_the_vault_reads_are_public(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    urls = [
        "/v1/categories",
        "/v1/components",
        f"/v1/components/{component.id}",
        f"/v1/components/{component.id}/generations",
        "/v1/components/by-slug/alpha",
    ]

    for url in urls:
        assert (await client.get(url)).status_code == 200, url


async def test_the_image_library_is_public_again(client, db_session):
    scenes = await create_category(db_session, slug="photography", kind="image")
    image = await create_image(
        db_session,
        category_id=scenes.id,
        path="genblocks/images/dawn",
        prompt="A quiet harbour at dawn",
    )

    page = (await client.get("/v1/images", params={"search": "harbour"})).json()
    by_slug = await client.get(f"/v1/images/by-slug/{image.slug}")
    by_id = await client.get(f"/v1/images/{image.id}")

    assert page["total"] == 1
    assert page["items"][0]["prompt"] == "A quiet harbour at dawn"
    assert by_slug.status_code == 200
    assert by_id.status_code == 200


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


async def test_a_card_carries_the_maker_and_the_render(client, db_session):
    category = await create_category(db_session, slug="hero")
    user = User(supabase_user_id=uuid.uuid4(), full_name="Marisol Vega")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    component = await create_component(db_session, category_id=category.id, slug="alpha")
    component.created_by = user.id
    generation = Generation(
        component_id=component.id,
        attempt_no=1,
        files={ENTRY: "x"},
        entry=ENTRY,
        verdict="published",
        screenshot_path="genblocks/screenshots/alpha",
    )
    db_session.add(generation)
    await db_session.commit()
    await db_session.refresh(generation)

    component.winning_generation_id = generation.id
    await db_session.commit()

    card = (await client.get("/v1/components")).json()["items"][0]
    full = (await client.get(f"/v1/components/{component.id}")).json()

    # The wall needs a picture and a name, and neither lives on the block's row.
    assert card["author"] == "Marisol Vega"
    assert card["screenshot_path"] == "genblocks/screenshots/alpha"
    assert full["author"] == "Marisol Vega"
    assert full["screenshot_path"] == "genblocks/screenshots/alpha"


async def test_an_unclaimed_card_has_no_author(client, db_session):
    category = await create_category(db_session, slug="hero")
    await create_component(db_session, category_id=category.id, slug="alpha")

    card = (await client.get("/v1/components")).json()["items"][0]

    assert card["author"] is None
    assert card["screenshot_path"] is None


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
    assert "provenance" in body


async def test_a_components_preview_is_public_and_says_so_on_the_block(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    document = "<!doctype html><html><body><section>Sunset</section></body></html>"
    db_session.add(
        ComponentPreview(
            component_id=component.id,
            html=document,
            bytes=len(document.encode("utf-8")),
        )
    )
    await db_session.commit()

    full = (await client.get(f"/v1/components/{component.id}")).json()
    preview = await client.get(f"/v1/components/{component.id}/preview")

    # The block says it has a page to run without carrying the page: the item
    # view asks for the document separately.
    assert full["has_preview"] is True
    assert preview.status_code == 200
    # A document, not a page: the web app is the only place it is served as HTML.
    assert preview.headers["content-type"].startswith("text/plain")
    assert preview.text == document
    # Not cached by anything between the API and the visitor: a takedown has to
    # reach the document, not only the row.
    assert preview.headers["cache-control"] == "no-store"


async def test_a_block_without_a_preview_says_so_and_answers_nothing(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    body = (await client.get(f"/v1/components/{component.id}")).json()
    preview = await client.get(f"/v1/components/{component.id}/preview")

    assert body["has_preview"] is False
    assert preview.status_code == 404


async def test_an_unknown_blocks_preview_is_not_found(client):
    assert (await client.get(f"/v1/components/{uuid.uuid4()}/preview")).status_code == 404


async def test_a_deleted_blocks_preview_is_not_served(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    db_session.add(ComponentPreview(component_id=component.id, html="<html></html>", bytes=13))
    await db_session.commit()

    await deletion.delete_component(db_session, component_id=component.id)

    assert (await client.get(f"/v1/components/{component.id}/preview")).status_code == 404


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
