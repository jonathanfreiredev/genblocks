import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.dependencies import get_admin_user
from app.authz.dependencies import get_first_party_user
from app.db.session import get_async_db_session
from app.deletion.service import DeletionFailed
from app.notifications import email as notifications
from app.pagination import OffsetPage
from app.reports import service
from app.reports.schemas import ReportCreate, ReportListQuery, ReportRead, ReportUpdate
from app.users.models import User

reports_router = APIRouter(prefix="/reports", tags=["reports"])
admin_reports_router = APIRouter(prefix="/admin/reports", tags=["admin"])


@reports_router.post("", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def report_content(
    payload: ReportCreate,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_first_party_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ReportRead:
    """Report a public block or image for human review."""
    try:
        report, created = await service.create_report(session, payload=payload, created_by=user.id)
    except service.ReportTargetMissing as missing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(missing)) from missing

    read = await service.as_read(session, report)
    # After the report is committed and the response is ready. Resend being down
    # must never turn a saved report into an error. A repeat press returns the
    # open report and does not send the operator a second copy.
    if created:
        background_tasks.add_task(notifications.report_created, read)
    return read


@admin_reports_router.get("", response_model=OffsetPage[ReportRead])
async def read_reports(
    _: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
    params: Annotated[ReportListQuery, Query()],
) -> OffsetPage[ReportRead]:
    """The operator queue, newest first unless ``sort`` says otherwise."""
    reports, total = await service.list_reports(session, params=params, status=params.status)

    return OffsetPage(
        items=[await service.as_read(session, report) for report in reports],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@admin_reports_router.patch("/{report_id}", response_model=ReportRead)
async def resolve_report(
    report_id: uuid.UUID,
    payload: ReportUpdate,
    user: Annotated[User, Depends(get_admin_user)],
    session: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ReportRead:
    """Dismiss a report or take its target down, with the operator's note."""
    report = await service.get_report(session, report_id=report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    try:
        resolved = await service.resolve_report(
            session, report=report, payload=payload, operator=user
        )
    except DeletionFailed as failed:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(failed)) from failed

    return await service.as_read(session, resolved)
