"""The operator's item view and the deletion audit."""

import pytest

from app.settings import settings
from tests.auth_stub import mint_token
from tests.helpers import auth_header, create_category, create_component, create_image

pytestmark = pytest.mark.anyio


async def test_the_item_list_is_operator_only_and_includes_public_items(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    denied = await client.get(
        "/v1/admin/components",
        headers=auth_header(mint_token(email="jane@example.com")),
    )
    allowed = await client.get(
        "/v1/admin/components",
        headers=auth_header(mint_token(email="operator@example.com")),
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["items"][0]["id"] == str(component.id)


async def test_an_operator_can_delete_an_item_and_the_audit_remembers_it(
    client, db_session, monkeypatch
):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    operator = auth_header(mint_token(email="operator@example.com"))

    deleted = await client.delete(f"/v1/admin/components/{component.id}", headers=operator)
    audit = await client.get("/v1/admin/deletions", headers=operator)

    assert deleted.status_code == 204
    assert (await client.get(f"/v1/components/{component.id}")).status_code == 404
    assert audit.status_code == 200
    entry = audit.json()[0]
    assert entry["kind"] == "component"
    assert entry["target_id"] == str(component.id)
    assert entry["slug"] == "alpha"
    assert entry["result"] == "deleted"
    assert entry["actor"] == "Jane Doe"


async def test_an_image_delete_is_audited_and_leaves_the_block(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    component_category = await create_category(db_session, slug="hero")
    image_category = await create_category(db_session, slug="scene", kind="image")
    component = await create_component(db_session, category_id=component_category.id, slug="alpha")
    image = await create_image(db_session, category_id=image_category.id, path="genblocks/images/x")
    operator = auth_header(mint_token(email="operator@example.com"))

    deleted = await client.delete(f"/v1/admin/images/{image.id}", headers=operator)

    assert deleted.status_code == 204
    assert (await client.get(f"/v1/images/{image.id}")).status_code == 404
    assert (await client.get(f"/v1/components/{component.id}")).status_code == 200
    entry = (await client.get("/v1/admin/deletions", headers=operator)).json()[0]
    assert entry["kind"] == "image"
    assert entry["target_id"] == str(image.id)


async def test_only_an_operator_can_delete_an_item(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    denied = await client.delete(
        f"/v1/admin/components/{component.id}",
        headers=auth_header(mint_token(email="jane@example.com")),
    )

    assert denied.status_code == 403
    assert (await client.get(f"/v1/components/{component.id}")).status_code == 200
