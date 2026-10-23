import pytest

from app.harness.network import UnsafeProviderUrl, checked_provider_url
from app.settings import settings


def test_a_safe_provider_url_is_returned():
    url = "https://api.bfl.ai/v1/get_result?id=req-1"

    assert checked_provider_url(url, hosts=("api.bfl.ai",), what="polling") == url


@pytest.mark.parametrize(
    "url",
    [
        "http://api.bfl.ai/v1/get_result",
        "https://api.bfl.ai.evil.test/v1/get_result",
        "https://user:pass@api.bfl.ai/v1/get_result",
        "https://api.bfl.ai:8443/v1/get_result",
        "https://127.0.0.1/v1/get_result",
        "https://169.254.169.254/latest/meta-data",
    ],
)
def test_an_unsafe_provider_url_is_refused(url):
    with pytest.raises(UnsafeProviderUrl):
        checked_provider_url(url, hosts=("api.bfl.ai",), what="polling")


def test_a_provider_answer_that_is_not_a_string_is_refused():
    with pytest.raises(UnsafeProviderUrl, match="did not answer"):
        checked_provider_url(None, hosts=("api.bfl.ai",), what="polling")


def test_the_configured_hosts_are_read_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "bfl_base_url", "https://bfl.internal/v1")
    monkeypatch.setattr(settings, "bfl_asset_hosts", "delivery.bfl.ai, cdn.bfl.ai")

    assert "bfl.internal" in settings.bfl_polling_hosts
    assert settings.bfl_asset_host_list == ("delivery.bfl.ai", "cdn.bfl.ai")


def test_a_domain_admits_its_own_subdomains():
    """BFL names a regional host in its polling URL, and it is still BFL's."""
    url = "https://api.us7.bfl.ai/v1/get_result?id=req-1"

    assert checked_provider_url(url, hosts=(), domains=("bfl.ai",), what="polling") == url


def test_a_domain_admits_itself():
    url = "https://bfl.ai/v1/get_result"

    assert checked_provider_url(url, hosts=(), domains=("bfl.ai",), what="polling") == url


@pytest.mark.parametrize(
    "url",
    [
        "https://evilbfl.ai/v1/get_result",
        "https://bfl.ai.evil.test/v1/get_result",
        "http://api.us7.bfl.ai/v1/get_result",
    ],
)
def test_a_domain_admits_nothing_that_merely_looks_like_it(url):
    with pytest.raises(UnsafeProviderUrl):
        checked_provider_url(url, hosts=(), domains=("bfl.ai",), what="polling")


def test_the_allowed_domains_are_read_from_settings(monkeypatch):
    monkeypatch.setattr(settings, "bfl_allowed_domains", " BFL.ai , .delivery.bfl.ai ")

    assert settings.bfl_allowed_domain_list == ("bfl.ai", "delivery.bfl.ai")
