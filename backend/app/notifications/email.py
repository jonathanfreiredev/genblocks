"""The email this product sends when a person needs to look at something.

A report is a request for a person to look, and a newly generated item is a
request for the operator's review before it becomes public. Neither email is a
gate: the row is committed before this runs, and a provider outage means a
missing notification, not a lost report or a failed generation.

The messages contain only what the operator needs to decide whether to open the
admin page. They deliberately carry no attachment and no public image URL: mail
gets forwarded, and a picture before publication should not travel with it.
"""

import html
import uuid

import httpx
import structlog

from app.reports.schemas import ReportRead
from app.settings import settings

logger = structlog.get_logger("app.notifications")

RESEND_ENDPOINT = "https://api.resend.com/emails"
TIMEOUT_SECONDS = 5.0


async def report_created(report: ReportRead, *, client: httpx.AsyncClient | None = None) -> bool:
    """Tell the operators about a new report, if Resend is configured.

    Returns whether a message was accepted by the provider. A failure is logged
    and deliberately swallowed: the caller has already saved the report, and a
    notification is not worth turning a successful report into a 500.
    """
    if not settings.resend_api_key:
        logger.debug("report notification is off", reason="RESEND_API_KEY is unset")
        return False

    recipients = settings.report_notification_recipients
    if not recipients:
        logger.warning(
            "report notification has no recipients",
            reason="set REPORT_NOTIFICATION_EMAILS or ADMIN_EMAILS",
        )
        return False

    subject, text, markup = _message(report)
    return await _send(
        subject=subject,
        text=text,
        markup=markup,
        client=client,
        failure="report notification could not be sent",
    )


async def item_created(
    *,
    kind: str,
    item_id: uuid.UUID,
    title: str,
    slug: str,
    author: str | None,
    client: httpx.AsyncClient | None = None,
) -> bool:
    """Tell the operators that a generated item is waiting for review.

    This is intentionally metadata only: the picture is not attached and its
    public URL is not included. The admin page is authenticated and is the place
    where the operator looks at the bytes.
    """
    if not settings.resend_api_key:
        logger.debug("item notification is off", reason="RESEND_API_KEY is unset")
        return False

    recipients = settings.report_notification_recipients
    if not recipients:
        logger.warning(
            "item notification has no recipients",
            reason="set REPORT_NOTIFICATION_EMAILS or ADMIN_EMAILS",
        )
        return False

    label = "block" if kind == "component" else "image"
    safe_title = title.strip()[:160] or f"a new {label}"
    who = author or "an unknown maker"
    admin_url = f"{settings.frontend_url.rstrip('/')}/admin/items?kind={kind}"
    subject = f"New GenBlocks {label} awaiting review: {safe_title}"
    text = "\n".join(
        [
            f"A new {label} is waiting for review.",
            "",
            f"Title: {safe_title}",
            f"Slug: {slug}",
            f"Maker: {who}",
            f"ID: {item_id}",
            "",
            f"Review it: {admin_url}",
        ]
    )
    markup = (
        '<h1 style="font-family: sans-serif; font-size: 18px;">'
        f"New {html.escape(label)} awaiting review</h1>"
        '<dl style="font-family: sans-serif;">'
        f"<dt><strong>Title</strong></dt><dd>{html.escape(safe_title)}</dd>"
        f"<dt><strong>Slug</strong></dt><dd>{html.escape(slug)}</dd>"
        f"<dt><strong>Maker</strong></dt><dd>{html.escape(who)}</dd>"
        f"<dt><strong>ID</strong></dt><dd>{html.escape(str(item_id))}</dd>"
        "</dl>"
        f'<p style="font-family: sans-serif;"><a href="{html.escape(admin_url)}">'
        "Open the review queue</a></p>"
    )

    return await _send(
        subject=subject,
        text=text,
        markup=markup,
        client=client,
        failure="item notification could not be sent",
    )


async def _send(
    *,
    subject: str,
    text: str,
    markup: str,
    client: httpx.AsyncClient | None,
    failure: str,
) -> bool:
    """Send one Resend message, swallowing provider failures."""
    payload = {
        "from": settings.resend_from_email,
        "to": list(settings.report_notification_recipients),
        "subject": subject,
        "text": text,
        "html": markup,
    }

    try:
        if client is not None:
            answer = await client.post(
                RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
        else:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as http:
                answer = await http.post(
                    RESEND_ENDPOINT,
                    headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                    json=payload,
                )
    except httpx.HTTPError as broke:
        logger.warning(failure, error=str(broke))
        return False

    if answer.status_code >= 400:
        logger.warning(
            "resend refused the notification",
            status=answer.status_code,
            detail=answer.text[:200],
        )
        return False

    return True


def _message(report: ReportRead) -> tuple[str, str, str]:
    """The subject, plain text and HTML for one report."""
    reason = report.reason.replace("_", " ")
    title = report.target_title or "a removed item"
    kind = report.target_kind.value
    section = "blocks" if report.target_kind.value == "component" else "images"
    target_path = f"{section}/{report.target_slug or report.target_id}"
    target_url = f"{settings.frontend_url.rstrip('/')}/{target_path}"
    queue_url = f"{settings.frontend_url.rstrip('/')}/admin/reports?status=open"
    reporter = report.reporter or "an unnamed visitor"
    details = report.details or "No note was left."

    subject = f"New GenBlocks report: {reason} — {title}"
    text = "\n".join(
        [
            f"A {kind} was reported.",
            "",
            f"Target: {title}",
            f"Reason: {reason}",
            f"Reporter: {reporter}",
            f"Note: {details}",
            "",
            f"Item: {target_url}",
            f"Queue: {queue_url}",
        ]
    )
    markup = (
        '<h1 style="font-family: sans-serif; font-size: 18px;">'
        "New GenBlocks report</h1>"
        '<p style="font-family: sans-serif;">'
        f"A {html.escape(kind)} was reported.</p>"
        '<dl style="font-family: sans-serif;">'
        f"<dt><strong>Target</strong></dt><dd>{html.escape(title)}</dd>"
        f"<dt><strong>Reason</strong></dt><dd>{html.escape(reason)}</dd>"
        f"<dt><strong>Reporter</strong></dt><dd>{html.escape(reporter)}</dd>"
        f"<dt><strong>Note</strong></dt><dd>{html.escape(details).replace(chr(10), '<br>')}</dd>"
        "</dl>"
        f'<p style="font-family: sans-serif;"><a href="{html.escape(target_url)}">'
        "Open the item</a> · "
        f'<a href="{html.escape(queue_url)}">Open the queue</a></p>'
    )

    return subject, text, markup
