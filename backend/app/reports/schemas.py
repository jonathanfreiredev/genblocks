import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.pagination import ListParams
from app.reports.models import ReportReason, ReportStatus, ReportTarget


class ReportCreate(BaseModel):
    """What a visitor sends when they think an artifact should not be public."""

    target_kind: ReportTarget
    target_id: uuid.UUID
    reason: ReportReason
    details: str | None = Field(default=None, max_length=2_000)


class ReportUpdate(BaseModel):
    """An operator's decision. ``take_down`` is the only action that changes the vault."""

    status: ReportStatus
    resolution: str | None = Field(default=None, max_length=2_000)
    take_down: bool = False


class ReportListQuery(ListParams):
    status: ReportStatus | None = None


class ReportRead(BaseModel):
    id: uuid.UUID
    target_kind: ReportTarget
    target_id: uuid.UUID
    target_slug: str | None
    target_title: str | None
    reason: ReportReason
    details: str | None
    status: ReportStatus
    resolution: str | None
    reporter: str | None
    created_at: datetime
    resolved_at: datetime | None
