"""Reporting a public artifact, and the operator queue that acts on it."""

import pytest

from app.settings import settings
from tests.auth_stub import mint_token
from tests.helpers import auth_header, create_category, create_component

pytestmark = pytest.mark.anyio


async def test_a_signed_in_visitor_can_report_a_block(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    response = await client.post(
        "/v1/reports",
        headers=auth_header(mint_token()),
        json={
            "target_kind": "component",
            "target_id": str(component.id),
            "reason": "brand",
            "details": "It uses a real logo.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["target_slug"] == "alpha"
    assert body["status"] == "open"
    assert body["reporter"] == "Jane Doe"


async def test_a_report_notifies_the_queue_without_gating_the_report(
    client, db_session, monkeypatch
):
    from app.notifications import email as notifications

    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")
    sent: list[object] = []

    async def notify(report):
        sent.append(report)
        return True

    monkeypatch.setattr(notifications, "report_created", notify)

    response = await client.post(
        "/v1/reports",
        headers=auth_header(mint_token()),
        json={
            "target_kind": "component",
            "target_id": str(component.id),
            "reason": "other",
        },
    )

    assert response.status_code == 201
    assert len(sent) == 1
    assert sent[0].target_slug == "alpha"


async def test_a_report_for_an_unknown_target_is_a_404(client):
    response = await client.post(
        "/v1/reports",
        headers=auth_header(mint_token()),
        json={
            "target_kind": "component",
            "target_id": "00000000-0000-0000-0000-000000000000",
            "reason": "other",
        },
    )

    assert response.status_code == 404


async def test_an_anonymous_visitor_cannot_report(client, db_session):
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    response = await client.post(
        "/v1/reports",
        json={
            "target_kind": "component",
            "target_id": str(component.id),
            "reason": "other",
        },
    )

    assert response.status_code == 401


async def test_only_a_configured_operator_can_read_the_queue(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")

    denied = await client.get(
        "/v1/admin/reports", headers=auth_header(mint_token(email="jane@example.com"))
    )
    allowed = await client.get(
        "/v1/admin/reports", headers=auth_header(mint_token(email="operator@example.com"))
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200


async def test_an_operator_can_take_a_reported_block_down(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    created = await client.post(
        "/v1/reports",
        headers=auth_header(mint_token()),
        json={
            "target_kind": "component",
            "target_id": str(component.id),
            "reason": "malware",
        },
    )
    report_id = created.json()["id"]

    resolved = await client.patch(
        f"/v1/admin/reports/{report_id}",
        headers=auth_header(mint_token(email="operator@example.com")),
        json={
            "status": "resolved",
            "resolution": "removed after review",
            "take_down": True,
        },
    )

    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    # The audit trail keeps the title even though the public row is gone.
    assert resolved.json()["target_title"] == "Alpha"
    assert (await client.get(f"/v1/components/{component.id}")).status_code == 404
    assert (await client.get("/v1/components")).json()["total"] == 0


async def test_an_operator_can_mark_a_report_as_reviewing(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    created = await client.post(
        "/v1/reports",
        headers=auth_header(mint_token()),
        json={
            "target_kind": "component",
            "target_id": str(component.id),
            "reason": "other",
        },
    )

    reviewing = await client.patch(
        f"/v1/admin/reports/{created.json()['id']}",
        headers=auth_header(mint_token(email="operator@example.com")),
        json={"status": "reviewing", "take_down": False},
    )

    assert reviewing.status_code == 200
    assert reviewing.json()["status"] == "reviewing"
    assert reviewing.json()["resolved_at"] is None
    assert (await client.get(f"/v1/components/{component.id}")).status_code == 200


async def test_a_dismissed_report_leaves_the_block_public(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "operator@example.com")
    category = await create_category(db_session, slug="hero")
    component = await create_component(db_session, category_id=category.id, slug="alpha")

    created = await client.post(
        "/v1/reports",
        headers=auth_header(mint_token()),
        json={
            "target_kind": "component",
            "target_id": str(component.id),
            "reason": "other",
        },
    )
    report_id = created.json()["id"]

    resolved = await client.patch(
        f"/v1/admin/reports/{report_id}",
        headers=auth_header(mint_token(email="operator@example.com")),
        json={"status": "dismissed", "resolution": "no issue", "take_down": False},
    )

    assert resolved.status_code == 200
    assert (await client.get(f"/v1/components/{component.id}")).status_code == 200
