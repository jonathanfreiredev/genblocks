"""Turning an id into an address.

A block or a picture is stored as a public id (PLAN.md, decision 11), so the
address a client opens is built here and nowhere else. These tests pin the two
things a reader depends on: the id is appended to the configured base, and a
deployment that publishes no base answers with nothing rather than with a link
that 404s.
"""

import uuid

import pytest

from app import urls
from app.settings import settings


@pytest.fixture
def configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "asset_base_url", "https://assets.example.test/upload")
    monkeypatch.setattr(settings, "frontend_url", "https://genblocks.example.test")


def test_an_id_is_appended_to_the_delivery_base(configured):
    assert (
        urls.asset_url("genblocks/images/dawn")
        == "https://assets.example.test/upload/genblocks/images/dawn"
    )


def test_a_base_with_a_trailing_slash_does_not_double_it(monkeypatch):
    monkeypatch.setattr(settings, "asset_base_url", "https://assets.example.test/upload/")

    assert urls.asset_url("genblocks/images/dawn") == (
        "https://assets.example.test/upload/genblocks/images/dawn"
    )


def test_an_id_with_a_leading_slash_does_not_double_it(configured):
    assert urls.asset_url("/genblocks/images/dawn") == (
        "https://assets.example.test/upload/genblocks/images/dawn"
    )


def test_an_absent_id_has_no_address(configured):
    assert urls.asset_url(None) is None
    assert urls.asset_url("") is None


def test_a_deployment_with_no_delivery_base_publishes_no_asset_url(monkeypatch):
    monkeypatch.setattr(settings, "asset_base_url", None)

    assert urls.asset_url("genblocks/images/dawn") is None


def test_the_shipped_base_is_a_usable_delivery_address():
    """It ships set, so nothing has to be configured to publish a URL.

    The account is a deployment's own, but the shape is Cloudinary's: an https
    origin under the delivery host, ending in the upload path an id is appended
    to.
    """
    base = settings.asset_base_url

    assert base.startswith("https://res.cloudinary.com/")
    assert base.endswith("/image/upload")


def test_each_kind_has_its_own_page(configured):
    task_id = uuid.UUID("0123456789abcdef0123456789abcdef")

    assert urls.component_page_url("pricing-table") == (
        "https://genblocks.example.test/blocks/pricing-table"
    )
    assert urls.image_page_url("harbour-at-dawn") == (
        "https://genblocks.example.test/images/harbour-at-dawn"
    )
    assert urls.task_page_url(task_id) == (
        "https://genblocks.example.test/tasks/01234567-89ab-cdef-0123-456789abcdef"
    )


def test_a_site_url_with_a_trailing_slash_does_not_double_it(monkeypatch):
    monkeypatch.setattr(settings, "frontend_url", "https://genblocks.example.test/")

    assert urls.component_page_url("alpha") == "https://genblocks.example.test/blocks/alpha"
