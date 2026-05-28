from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import LiveSession, Meeting, MeetingStatus, Workspace
from ..services.storage import meeting_artifacts_dir, uploads_dir
from .audit import write_audit


def soft_delete_meeting(db: Session, meeting: Meeting) -> None:
    meeting.deleted_at = datetime.now(timezone.utc)
    db.add(meeting)
    db.commit()


def purge_expired_meetings(
    db: Session,
    workspace: Workspace,
    *,
    user_id: int | None = None,
    dry_run: bool = False,
) -> list[int]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=workspace.retention_days)
    rows = db.execute(
        select(Meeting).where(
            Meeting.workspace_id == workspace.id,
            Meeting.created_at < cutoff,
            Meeting.deleted_at.is_(None),
        )
    ).scalars().all()

    purged: list[int] = []
    for meeting in rows:
        purged.append(meeting.id)
        if dry_run:
            continue
        _purge_meeting_files(meeting)
        meeting.deleted_at = datetime.now(timezone.utc)
        meeting.status = MeetingStatus.FAILED_ANALYSIS
        meeting.error_message = "Purged by retention policy"
        meeting.transcript_json = None
        meeting.insights_json = None
        db.add(meeting)

    if not dry_run and purged:
        db.commit()
        write_audit(
            db,
            workspace_id=workspace.id,
            user_id=user_id,
            action="retention.purge",
            resource_type="workspace",
            resource_id=str(workspace.id),
            details={"purged_meeting_ids": purged, "retention_days": workspace.retention_days},
        )
    return purged


def _purge_meeting_files(meeting: Meeting) -> None:
    upload = Path(meeting.upload_path)
    if upload.exists():
        upload.unlink(missing_ok=True)
    artifacts = meeting_artifacts_dir(meeting.id)
    if artifacts.exists():
        shutil.rmtree(artifacts, ignore_errors=True)


def hard_delete_meeting(
    db: Session,
    meeting: Meeting,
    *,
    workspace_id: int,
    user_id: int | None,
) -> None:
    mid = meeting.id
    _purge_meeting_files(meeting)
    db.delete(meeting)
    db.commit()
    write_audit(
        db,
        workspace_id=workspace_id,
        user_id=user_id,
        action="meeting.hard_delete",
        resource_type="meeting",
        resource_id=str(mid),
    )


def soft_delete_live_session(db: Session, session: LiveSession) -> None:
    session.deleted_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
