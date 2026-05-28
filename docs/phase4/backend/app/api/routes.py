from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..db.init_db import init_db
from ..db.models import Meeting, MeetingStatus
from ..db.session import get_db
from ..services.integrations.exporter import list_exports, run_export
from ..services.integrations.providers import IntegrationError
from ..services.jobs import enqueue_process_meeting
from ..services.samples import ensure_sample_file, get_sample, load_manifest, sample_file_path
from ..services.search.index import reindex_all_ready, search_meetings
from ..services.storage import meeting_artifacts_dir, uploads_dir
from .schemas import (
    ExportRecord,
    ExportRequest,
    ExportResponse,
    MeetingCreateResponse,
    MeetingDetail,
    MeetingListItem,
    MeetingResults,
    ReindexResponse,
    SampleItem,
    SampleListResponse,
    SampleProcessResponse,
    SearchHit,
    SearchResponse,
)

router = APIRouter()


def _parse_bool(value: Optional[str], default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@router.on_event("startup")
def _startup() -> None:
    init_db()


@router.get("/health")
def health() -> dict:
    return {"ok": True, "phase": 4}


@router.get("/samples", response_model=SampleListResponse)
def list_samples() -> SampleListResponse:
    items: list[SampleItem] = []
    for raw in load_manifest().get("samples", []):
        path = sample_file_path(raw)
        available = path.exists()
        if raw.get("id") == "icsi-bed-60s" and not available:
            try:
                ensure_sample_file(raw)
                available = path.exists()
            except Exception:
                available = False
        items.append(
            SampleItem(
                id=raw["id"],
                dataset=raw["dataset"],
                title=raw["title"],
                description=raw["description"],
                filename=raw["filename"],
                duration_s=float(raw.get("duration_s", 0)),
                language=raw.get("language", "English"),
                meeting_start=raw.get("meeting_start"),
                timezone=raw.get("timezone"),
                source_url=raw.get("source_url"),
                available=available,
            )
        )
    return SampleListResponse(samples=items)


@router.post("/samples/{sample_id}/process", response_model=SampleProcessResponse)
def process_sample(
    sample_id: str,
    db: Session = Depends(get_db),
) -> SampleProcessResponse:
    sample = get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    try:
        src = ensure_sample_file(sample)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    suffix = src.suffix.lower() or ".wav"
    meeting = Meeting(
        title=sample.get("title"),
        original_filename=src.name,
        upload_path="",
        status=MeetingStatus.UPLOADED,
        meeting_start=sample.get("meeting_start"),
        timezone=sample.get("timezone"),
        enable_diarization=True,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    dest = uploads_dir() / f"{meeting.id}{suffix}"
    shutil.copy2(src, dest)
    meeting.upload_path = str(dest)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    meeting_artifacts_dir(meeting.id)
    enqueue_process_meeting(meeting.id)

    return SampleProcessResponse(
        id=meeting.id,
        status=meeting.status.value,
        sample_id=sample_id,
        message=f"Processing sample '{sample.get('title')}'. Results will appear when status is READY.",
    )


@router.post("/meetings", response_model=MeetingCreateResponse)
def create_meeting(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    meeting_start: Optional[str] = Form(default=None),
    timezone: Optional[str] = Form(default=None),
    enable_diarization: Optional[str] = Form(default="true"),
    db: Session = Depends(get_db),
) -> MeetingCreateResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    up_dir = uploads_dir()
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp3", ".wav", ".m4a", ".mp4", ".mov"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    meeting = Meeting(
        title=title,
        original_filename=file.filename,
        upload_path="",
        status=MeetingStatus.UPLOADED,
        meeting_start=meeting_start,
        timezone=timezone,
        enable_diarization=_parse_bool(enable_diarization, default=True),
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


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    mode: str = Query(default="keyword", pattern="^(keyword|semantic)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SearchResponse:
    hits_raw = search_meetings(db, query=q, mode=mode, limit=limit)
    hits = [SearchHit(**h) for h in hits_raw]
    return SearchResponse(query=q, mode=mode, hits=hits)


@router.post("/search/reindex", response_model=ReindexResponse)
def reindex(db: Session = Depends(get_db)) -> ReindexResponse:
    count = reindex_all_ready(db)
    return ReindexResponse(indexed_count=count)


@router.post("/meetings/{meeting_id}/integrations/export", response_model=ExportResponse)
def export_meeting(
    meeting_id: int,
    body: ExportRequest,
    db: Session = Depends(get_db),
) -> ExportResponse:
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    try:
        record = run_export(
            db,
            meeting,
            provider=body.provider,
            export_kind=body.export_kind,
            force=body.force,
        )
    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    export = ExportRecord(
        id=record.id,
        provider=record.provider,
        export_kind=record.export_kind,
        status=record.status.value,
        external_ref=record.external_ref,
        error_message=record.error_message,
        created_at=record.created_at,
    )
    return ExportResponse(export=export, message="Export completed successfully.")


@router.get("/meetings/{meeting_id}/integrations/exports", response_model=list[ExportRecord])
def get_exports(meeting_id: int, db: Session = Depends(get_db)) -> list[ExportRecord]:
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    rows = list_exports(db, meeting_id)
    return [
        ExportRecord(
            id=r.id,
            provider=r.provider,
            export_kind=r.export_kind,
            status=r.status.value,
            external_ref=r.external_ref,
            error_message=r.error_message,
            created_at=r.created_at,
        )
        for r in rows
    ]
