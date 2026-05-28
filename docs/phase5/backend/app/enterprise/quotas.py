from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Workspace, WorkspaceUsage


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_or_create_usage(db: Session, workspace: Workspace) -> WorkspaceUsage:
    period = _current_period()
    row = db.execute(
        select(WorkspaceUsage).where(
            WorkspaceUsage.workspace_id == workspace.id,
            WorkspaceUsage.period == period,
        )
    ).scalar_one_or_none()
    if row:
        return row
    row = WorkspaceUsage(workspace_id=workspace.id, period=period)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def check_meeting_quota(db: Session, workspace: Workspace) -> None:
    usage = get_or_create_usage(db, workspace)
    if usage.meetings_created >= workspace.max_meetings_per_month:
        raise ValueError(
            f"Monthly meeting quota exceeded ({workspace.max_meetings_per_month}). "
            "Contact your workspace admin or wait until next month."
        )


def record_meeting_created(db: Session, workspace: Workspace) -> None:
    usage = get_or_create_usage(db, workspace)
    usage.meetings_created += 1
    db.add(usage)
    db.commit()


def check_llm_quota(db: Session, workspace: Workspace, estimated_tokens: int) -> None:
    usage = get_or_create_usage(db, workspace)
    projected = usage.llm_tokens_estimated + estimated_tokens
    if projected > workspace.max_llm_tokens_per_month:
        raise ValueError(
            f"Monthly LLM token quota would be exceeded ({workspace.max_llm_tokens_per_month}). "
            "Try a shorter recording or contact your admin."
        )


def record_llm_usage(db: Session, workspace: Workspace, estimated_tokens: int) -> None:
    usage = get_or_create_usage(db, workspace)
    usage.llm_tokens_estimated += max(0, estimated_tokens)
    db.add(usage)
    db.commit()


def record_cache_hit(db: Session, workspace: Workspace) -> None:
    usage = get_or_create_usage(db, workspace)
    usage.cache_hits += 1
    db.add(usage)
    db.commit()
