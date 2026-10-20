"""Reporting a public artifact, and the operator's decision about it.

A report is a request for a human to look, not an automatic takedown. The queue
is therefore append-only until an operator resolves it: opening, reviewing,
resolving and dismissing are states of the same row, and the target is only
soft-deleted when the operator says so.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.components.models import Component
from app.db.models import utcnow
from app.images.models import Image
from app.pagination import ListParams
from app.reports.models import Report, ReportStatus, ReportTarget
from app.reports.schemas import ReportCreate, ReportRead, ReportUpdate
from app.users.models import User
from app.users.service import display_names


class ReportTargetMissing(Exception):
    """The artifact a report points at is not public."""


async def create_report(
    session: AsyncSession, *, payload: ReportCreate, created_by: uuid.UUID
) -> Report:
    """Record one report after checking the target exists and is still public."""
    if not await _target_exists(session, kind=payload.target_kind, target_id=payload.target_id):
        raise ReportTargetMissing("That artifact is not in the public vault.")

    report = Report(
        component_id=payload.target_id if payload.target_kind is ReportTarget.COMPONENT else None,
        image_id=payload.target_id if payload.target_kind is ReportTarget.IMAGE else None,
        reason=payload.reason,
        details=payload.details,
        status=ReportStatus.OPEN,
        created_by=created_by,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


async def list_reports(
    session: AsyncSession,
    *,
    params: ListParams,
    status: ReportStatus | None = None,
) -> tuple[Sequence[Report], int]:
    """A page of reports, newest first unless the caller sorts otherwise."""
    order_by = params.order_by(
        {"created_at": Report.created_at, "status": Report.status},
        default="-created_at",
        tiebreaker=Report.id,
    )
    base = select(Report)
    if status is not None:
        base = base.where(Report.status == status)

    reports = await session.scalars(
        base.order_by(*order_by).limit(params.limit).offset(params.offset)
    )
    total = await session.scalar(select(func.count()).select_from(base.subquery()))

    return reports.all(), total or 0


async def get_report(session: AsyncSession, *, report_id: uuid.UUID) -> Report | None:
    return await session.scalar(select(Report).where(Report.id == report_id))


async def resolve_report(
    session: AsyncSession,
    *,
    report: Report,
    payload: ReportUpdate,
    operator: User,
) -> Report:
    """Apply an operator's decision, and take the target down when asked.

    A takedown is a soft delete: the report and the audit trail survive, the
    public read endpoints stop returning the row, and a later review can restore
    it by clearing ``deleted_at`` if the decision was wrong.
    """
    if payload.take_down:
        target = await _target(
            session, kind=_kind_of(report), target_id=_target_id(report), public_only=False
        )
        if target is not None:
            target.deleted_at = utcnow()

    report.status = payload.status
    report.resolution = payload.resolution
    if payload.status in (ReportStatus.RESOLVED, ReportStatus.DISMISSED):
        report.resolved_by = operator.id
        report.resolved_at = utcnow()

    await session.commit()
    await session.refresh(report)
    return report


async def as_read(session: AsyncSession, report: Report) -> ReportRead:
    """The public shape of a report, with the target and reporter resolved."""
    target = await _target(
        session, kind=_kind_of(report), target_id=_target_id(report), public_only=False
    )
    reporter = (
        await display_names(session, ids=[report.created_by])
        if report.created_by is not None
        else {}
    )

    if isinstance(target, Component):
        slug, title = target.slug, target.title
    elif isinstance(target, Image):
        slug, title = target.slug, target.prompt
    else:
        slug, title = None, None

    return ReportRead(
        id=report.id,
        target_kind=_kind_of(report),
        target_id=_target_id(report),
        target_slug=slug,
        target_title=title,
        reason=report.reason,
        details=report.details,
        status=report.status,
        resolution=report.resolution,
        reporter=reporter.get(report.created_by) if report.created_by else None,
        created_at=report.created_at,
        resolved_at=report.resolved_at,
    )


async def _target_exists(
    session: AsyncSession, *, kind: ReportTarget, target_id: uuid.UUID
) -> bool:
    return await _target(session, kind=kind, target_id=target_id, public_only=True) is not None


async def _target(
    session: AsyncSession,
    *,
    kind: ReportTarget,
    target_id: uuid.UUID,
    public_only: bool = True,
) -> Component | Image | None:
    """The target row, optionally including a row that was taken down.

    Creation asks for the public row: a report cannot point at something that is
    already gone. Reading and resolving ask for the row regardless, because the
    audit trail should keep the title of what it acted on.
    """
    if kind is ReportTarget.COMPONENT:
        statement = select(Component).where(Component.id == target_id)
        if public_only:
            statement = statement.where(Component.deleted_at.is_(None))
        return await session.scalar(statement)

    statement = select(Image).where(Image.id == target_id)
    if public_only:
        statement = statement.where(Image.deleted_at.is_(None))
    return await session.scalar(statement)


def _kind_of(report: Report) -> ReportTarget:
    return ReportTarget.COMPONENT if report.component_id is not None else ReportTarget.IMAGE


def _target_id(report: Report) -> uuid.UUID:
    found = report.component_id or report.image_id
    if found is None:  # pragma: no cover - the database check prevents it
        raise ReportTargetMissing("The report has no target.")
    return found
