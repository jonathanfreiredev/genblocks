import uuid
from datetime import UTC, datetime

import httpx
import pytest

from app.notifications import email
from app.reports.models import ReportReason, ReportStatus, ReportTarget
from app.reports.schemas import ReportRead
from app.settings import settings

pytestmark = pytest.mark.anyio


def report() -> ReportRead:
    return ReportRead(
        id=uuid.uuid4(),
        target_kind=ReportTarget.COMPONENT,
        target_id=uuid.uuid4(),
        target_slug="a-pricing-page",
        target_title="A pricing page",
        reason=ReportReason.BRAND,
        details="It uses a real logo.\nPlease look.",
        status=ReportStatus.OPEN,
        resolution=None,
        reporter="Jane Doe",
        created_at=datetime.now(UTC),
        resolved_at=None,
    )


@pytest.fixture
def configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "resend_from_email", "GenBlocks <reports@example.com>")
    monkeypatch.setattr(settings, "report_notification_emails", "ops@example.com")
    monkeypatch.setattr(settings, "frontend_url", "https://genblocks.test")


async def test_no_key_means_no_request(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", None)

    async def fail(*args, **kwargs):  # pragma: no cover - must not run
        pytest.fail("Resend was called without a key")

    client = httpx.AsyncClient(transport=httpx.MockTransport(fail))

    assert await email.report_created(report(), client=client) is False


async def test_a_configured_report_sends_one_message(configured):
    sent: dict = {}

    async def handle(request: httpx.Request) -> httpx.Response:
        sent["headers"] = dict(request.headers)
        sent["body"] = request.read().decode()
        return httpx.Response(200, json={"id": "email-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))

    assert await email.report_created(report(), client=client) is True

    assert sent["headers"]["authorization"] == "Bearer re_test"
    assert "ops@example.com" in sent["body"]
    assert "A pricing page" in sent["body"]
    assert "It uses a real logo." in sent["body"]
    # The item link is the public page, not the API's `/components` address.
    assert "https://genblocks.test/blocks/a-pricing-page" in sent["body"]
    assert "https://genblocks.test/admin/reports?status=open" in sent["body"]


async def test_recipients_fall_back_to_the_operators(configured, monkeypatch):
    monkeypatch.setattr(settings, "report_notification_emails", "")
    monkeypatch.setattr(settings, "admin_emails", "owner@example.com,other@example.com")

    sent: dict = {}

    async def handle(request: httpx.Request) -> httpx.Response:
        sent["body"] = request.read().decode()
        return httpx.Response(200, json={"id": "email-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))

    assert await email.report_created(report(), client=client) is True
    assert "owner@example.com" in sent["body"]
    assert "other@example.com" in sent["body"]


async def test_a_provider_failure_is_not_a_failed_report(configured):
    async def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="resend is down")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))

    assert await email.report_created(report(), client=client) is False


async def test_no_recipients_is_a_missing_notification(monkeypatch):
    monkeypatch.setattr(settings, "resend_api_key", "re_test")
    monkeypatch.setattr(settings, "report_notification_emails", "")
    monkeypatch.setattr(settings, "admin_emails", "")

    assert await email.report_created(report()) is False


async def test_html_escapes_a_note_instead_of_rendering_it(configured):
    import json

    sent: dict = {}

    async def handle(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.read().decode()))
        return httpx.Response(200, json={"id": "email-1"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
    item = report().model_copy(update={"details": "<script>alert(1)</script>"})

    assert await email.report_created(item, client=client) is True
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in sent["html"]
    assert "<script>alert(1)</script>" not in sent["html"]
    # The plain-text alternative is not HTML; the same characters are safe there.
    assert "<script>alert(1)</script>" in sent["text"]
