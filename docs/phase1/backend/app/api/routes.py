from __future__ import annotations

import shutil
from pathlib import Path

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..config import settings
from ..db.init_db import init_db
from ..db.models import Meeting, MeetingStatus
from ..db.session import get_db
from ..services.jobs import enqueue_process_meeting
from ..services.storage import meeting_artifacts_dir, uploads_dir
from .schemas import MeetingCreateResponse, MeetingDetail, MeetingListItem, MeetingResults

router = APIRouter()


@router.on_event("startup")
def _startup() -> None:
    init_db()


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.post("/meetings", response_model=MeetingCreateResponse)
def create_meeting(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    meeting_start: Optional[str] = Form(default=None),
    timezone: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
) -> MeetingCreateResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    # Persist upload to local storage
    up_dir = uploads_dir()
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp3", ".wav", ".m4a", ".mp4", ".mov"}:
        # video optional; accept common containers for MVP
        raise HTTPException(status_code=400, detail="Unsupported file type")

    meeting = Meeting(
        title=title,
        original_filename=file.filename,
        upload_path="",  # set after save
        status=MeetingStatus.UPLOADED,
        meeting_start=meeting_start,
        timezone=timezone,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    dest = up_dir / f"{meeting.id}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    meeting.upload_path = str(dest)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # ensure artifact dir exists
    meeting_artifacts_dir(meeting.id)

    enqueue_process_meeting(meeting.id)
    return MeetingCreateResponse(id=meeting.id, status=meeting.status.value)


@router.get("/meetings", response_model=list[MeetingListItem])
def list_meetings(db: Session = Depends(get_db)) -> list[MeetingListItem]:
    meetings = db.execute(select(Meeting).order_by(desc(Meeting.created_at))).scalars().all()
    return [
        MeetingListItem(
            id=m.id,
            title=m.title,
            created_at=m.created_at,
            status=m.status.value,
            original_filename=m.original_filename,
        )
        for m in meetings
    ]


@router.get("/meetings/{meeting_id}", response_model=MeetingDetail)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)) -> MeetingDetail:
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingDetail(
        id=m.id,
        title=m.title,
        created_at=m.created_at,
        status=m.status.value,
        original_filename=m.original_filename,
        meeting_start=m.meeting_start,
        timezone=m.timezone,
        error_message=m.error_message,
    )


@router.get("/meetings/{meeting_id}/results", response_model=MeetingResults)
def get_results(meeting_id: int, db: Session = Depends(get_db)) -> MeetingResults:
    m = db.get(Meeting, meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return MeetingResults(
        status=m.status.value,
        transcript=m.transcript_json,
        insights=m.insights_json,
    )

