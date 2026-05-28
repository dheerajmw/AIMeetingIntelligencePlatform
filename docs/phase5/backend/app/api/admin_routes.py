from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..auth.dependencies import AuthContext, require_admin
from ..db.models import AuditLog, Workspace, WorkspaceUsage
from ..db.session import get_db
from ..enterprise.audit import write_audit
from ..enterprise.retention import hard_delete_meeting, purge_expired_meetings
from ..enterprise.quotas import get_or_create_usage
from ..services.access import get_workspace_meeting

router = APIRouter(prefix="/admin", tags=["admin"])


class WorkspaceSettingsUpdate(BaseModel):
    retention_days: Optional[int] = Field(default=None, ge=1, le=3650)
    data_region: Optional[str] = None
    max_meetings_per_month: Optional[int] = Field(default=None, ge=1, le=100_000)
    max_llm_tokens_per_month: Optional[int] = Field(default=None, ge=1_000, le=50_000_000)


class WorkspaceSettingsResponse(BaseModel):
    id: int
    slug: str
    name: str
    data_region: str
    retention_days: int
    max_meetings_per_month: int
    max_llm_tokens_per_month: int


class UsageResponse(BaseModel):
    period: str
    meetings_created: int
    llm_tokens_estimated: int
    cache_hits: int
    max_meetings_per_month: int
    max_llm_tokens_per_month: int


class AuditLogItem(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: Optional[str]
    user_id: Optional[int]
    details_json: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime


class RetentionPurgeResponse(BaseModel):
    purged_meeting_ids: list[int]
    dry_run: bool


@router.get("/workspace", response_model=WorkspaceSettingsResponse)
def get_workspace_settings(auth: AuthContext = Depends(require_admin)) -> WorkspaceSettingsResponse:
    w = auth.workspace
    return WorkspaceSettingsResponse(
        id=w.id,
        slug=w.slug,
        name=w.name,
        data_region=w.data_region,
        retention_days=w.retention_days,
        max_meetings_per_month=w.max_meetings_per_month,
        max_llm_tokens_per_month=w.max_llm_tokens_per_month,
    )


@router.patch("/workspace", response_model=WorkspaceSettingsResponse)
def update_workspace_settings(
    body: WorkspaceSettingsUpdate,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WorkspaceSettingsResponse:
    w = db.get(Workspace, auth.workspace.id)
    if not w:
        raise HTTPException(status_code=404, detail="Workspace not found")

    changes: dict = {}
    if body.retention_days is not None:
        w.retention_days = body.retention_days
        changes["retention_days"] = body.retention_days
    if body.data_region is not None:
        w.data_region = body.data_region.strip()
        changes["data_region"] = w.data_region
    if body.max_meetings_per_month is not None:
        w.max_meetings_per_month = body.max_meetings_per_month
        changes["max_meetings_per_month"] = body.max_meetings_per_month
    if body.max_llm_tokens_per_month is not None:
        w.max_llm_tokens_per_month = body.max_llm_tokens_per_month
        changes["max_llm_tokens_per_month"] = body.max_llm_tokens_per_month

    db.add(w)
    db.commit()
    db.refresh(w)

    write_audit(
        db,
        workspace_id=w.id,
        user_id=auth.user.id,
        action="workspace.settings_update",
        resource_type="workspace",
        resource_id=str(w.id),
        details=changes,
    )
    return WorkspaceSettingsResponse(
        id=w.id,
        slug=w.slug,
        name=w.name,
        data_region=w.data_region,
        retention_days=w.retention_days,
        max_meetings_per_month=w.max_meetings_per_month,
        max_llm_tokens_per_month=w.max_llm_tokens_per_month,
    )


@router.get("/usage", response_model=UsageResponse)
def get_usage(
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsageResponse:
    usage = get_or_create_usage(db, auth.workspace)
    return UsageResponse(
        period=usage.period,
        meetings_created=usage.meetings_created,
        llm_tokens_estimated=usage.llm_tokens_estimated,
        cache_hits=usage.cache_hits,
        max_meetings_per_month=auth.workspace.max_meetings_per_month,
        max_llm_tokens_per_month=auth.workspace.max_llm_tokens_per_month,
    )


@router.get("/audit-logs", response_model=list[AuditLogItem])
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AuditLogItem]:
    rows = db.execute(
        select(AuditLog)
        .where(AuditLog.workspace_id == auth.workspace.id)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
    ).scalars().all()
    return [
        AuditLogItem(
            id=r.id,
            action=r.action,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            user_id=r.user_id,
            details_json=r.details_json,
            ip_address=r.ip_address,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.post("/retention/purge", response_model=RetentionPurgeResponse)
def run_retention_purge(
    dry_run: bool = Query(default=False),
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RetentionPurgeResponse:
    purged = purge_expired_meetings(
        db,
        auth.workspace,
        user_id=auth.user.id,
        dry_run=dry_run,
    )
    return RetentionPurgeResponse(purged_meeting_ids=purged, dry_run=dry_run)


@router.delete("/meetings/{meeting_id}")
def hard_delete(
    meeting_id: int,
    request: Request,
    auth: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    meeting = get_workspace_meeting(db, meeting_id, auth.workspace.id)
    hard_delete_meeting(db, meeting, workspace_id=auth.workspace.id, user_id=auth.user.id)
    return {"ok": True, "meeting_id": meeting_id}
