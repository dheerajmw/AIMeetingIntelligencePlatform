from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..db.models import LiveSession, Meeting


def get_workspace_meeting(db: Session, meeting_id: int, workspace_id: int) -> Meeting:
    meeting = db.get(Meeting, meeting_id)
    if not meeting or meeting.workspace_id != workspace_id or meeting.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def get_workspace_live_session(db: Session, session_id: int, workspace_id: int) -> LiveSession:
    session = db.get(LiveSession, session_id)
    if not session or session.workspace_id != workspace_id or session.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Live session not found")
    return session
