from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..auth.dependencies import AuthContext, require_read, require_write
from ..config import settings
from ..db.init_db import init_db
from ..db.models import Meeting, MeetingStatus
from ..db.session import get_db
from ..enterprise.audit import write_audit
from ..enterprise.encryption import encryption_enabled, file_content_hash
from ..enterprise.quotas import check_meeting_quota, record_meeting_created
from ..enterprise.retention import soft_delete_meeting
from ..services.access import get_workspace_meeting
from ..services.integrations.exporter import list_exports, run_export
from ..services.integrations.providers import IntegrationError
from ..services.integrations.status import integrations_status_payload
from ..services.jobs import enqueue_process_meeting
from ..services.samples import ensure_sample_file, get_sample, load_manifest, sample_file_path
from ..services.search.index import reindex_all_ready, search_meetings
from ..services.storage import meeting_artifacts_dir, uploads_dir
from ..tasks import encrypt_meeting_upload
from .schemas import (
    ExportRecord,
    ExportRequest,
    ExportResponse,
    IntegrationProviderStatus,
    IntegrationsStatusResponse,
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


def _client_ip(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


@router.on_event("startup")
def _startup() -> None:
    init_db()


@router.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "phase": 5,
        "encryption_at_rest": encryption_enabled(),
        "auth_disabled": settings.auth_disabled,
    }


@router.get("/samples", response_model=SampleListResponse)
def list_samples(auth: AuthContext = Depends(require_read)) -> SampleListResponse:
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
    request: Request,
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> SampleProcessResponse:
    try:
        check_meeting_quota(db, auth.workspace)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e

    sample = get_sample(sample_id)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")

    try:
        src = ensure_sample_file(sample)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    suffix = src.suffix.lower() or ".wav"
    meeting = Meeting(
        workspace_id=auth.workspace.id,
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
    meeting.content_hash = file_content_hash(dest)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    meeting_artifacts_dir(meeting.id)
    encrypt_meeting_upload(meeting.id)
    record_meeting_created(db, auth.workspace)
    enqueue_process_meeting(meeting.id)

    write_audit(
        db,
        workspace_id=auth.workspace.id,
        user_id=auth.user.id,
        action="sample.process",
        resource_type="meeting",
        resource_id=str(meeting.id),
        details={"sample_id": sample_id},
        ip_address=_client_ip(request),
    )

    return SampleProcessResponse(
        id=meeting.id,
        status=meeting.status.value,
        sample_id=sample_id,
        message=f"Processing sample '{sample.get('title')}'. Results will appear when status is READY.",
    )


@router.post("/meetings", response_model=MeetingCreateResponse)
def create_meeting(
    request: Request,
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    meeting_start: Optional[str] = Form(default=None),
    timezone: Optional[str] = Form(default=None),
    enable_diarization: Optional[str] = Form(default="true"),
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> MeetingCreateResponse:
    try:
        check_meeting_quota(db, auth.workspace)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e

    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".mp3", ".wav", ".m4a", ".mp4", ".mov"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    meeting = Meeting(
        workspace_id=auth.workspace.id,
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

    dest = uploads_dir() / f"{meeting.id}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    meeting.upload_path = str(dest)
    meeting.content_hash = file_content_hash(dest)
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    meeting_artifacts_dir(meeting.id)
    encrypt_meeting_upload(meeting.id)
    record_meeting_created(db, auth.workspace)
    enqueue_process_meeting(meeting.id)

    write_audit(
        db,
        workspace_id=auth.workspace.id,
        user_id=auth.user.id,
        action="meeting.upload",
        resource_type="meeting",
        resource_id=str(meeting.id),
        ip_address=_client_ip(request),
    )
    return MeetingCreateResponse(id=meeting.id, status=meeting.status.value)


@router.get("/meetings", response_model=list[MeetingListItem])
def list_meetings(
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> list[MeetingListItem]:
    meetings = db.execute(
        select(Meeting)
        .where(Meeting.workspace_id == auth.workspace.id, Meeting.deleted_at.is_(None))
        .order_by(desc(Meeting.created_at))
    ).scalars().all()
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
def get_meeting(
    meeting_id: int,
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> MeetingDetail:
    m = get_workspace_meeting(db, meeting_id, auth.workspace.id)
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
def get_results(
    meeting_id: int,
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> MeetingResults:
    m = get_workspace_meeting(db, meeting_id, auth.workspace.id)
    return MeetingResults(
        status=m.status.value,
        transcript=m.transcript_json,
        insights=m.insights_json,
    )


@router.delete("/meetings/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    request: Request,
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> dict:
    meeting = get_workspace_meeting(db, meeting_id, auth.workspace.id)
    soft_delete_meeting(db, meeting)
    write_audit(
        db,
        workspace_id=auth.workspace.id,
        user_id=auth.user.id,
        action="meeting.soft_delete",
        resource_type="meeting",
        resource_id=str(meeting_id),
        ip_address=_client_ip(request),
    )
    return {"ok": True, "meeting_id": meeting_id}


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    mode: str = Query(default="keyword", pattern="^(keyword|semantic)$"),
    limit: int = Query(default=20, ge=1, le=100),
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> SearchResponse:
    hits_raw = search_meetings(db, query=q, mode=mode, limit=limit, workspace_id=auth.workspace.id)
    hits = [SearchHit(**h) for h in hits_raw]
    return SearchResponse(query=q, mode=mode, hits=hits)


@router.post("/search/reindex", response_model=ReindexResponse)
def reindex(
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> ReindexResponse:
    count = reindex_all_ready(db, workspace_id=auth.workspace.id)
    return ReindexResponse(indexed_count=count)


@router.get("/integrations/status", response_model=IntegrationsStatusResponse)
def integrations_status(auth: AuthContext = Depends(require_read)) -> IntegrationsStatusResponse:
    data = integrations_status_payload()
    return IntegrationsStatusResponse(
        stub_mode=data["stub_mode"],
        providers={
            name: IntegrationProviderStatus(**info) for name, info in data["providers"].items()
        },
    )


@router.post("/meetings/{meeting_id}/integrations/export", response_model=ExportResponse)
def export_meeting(
    meeting_id: int,
    body: ExportRequest,
    request: Request,
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> ExportResponse:
    meeting = get_workspace_meeting(db, meeting_id, auth.workspace.id)

    email_to: str | None = None
    if body.provider == "email" and body.export_kind == "summary":
        requested = (body.email_to or "").strip()
        # Default behavior: send to the currently signed-in user.
        email_to = requested or (auth.user.email or "").strip()
        # Optional: allow overriding recipient only for admins/owners.
        if requested and requested.lower() != (auth.user.email or "").lower() and auth.role.value not in {"OWNER", "ADMIN"}:
            raise HTTPException(status_code=403, detail="Only admins can send email to other recipients.")

    try:
        record = run_export(
            db,
            meeting,
            provider=body.provider,
            export_kind=body.export_kind,
            force=body.force,
            email_to=email_to,
        )
    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    write_audit(
        db,
        workspace_id=auth.workspace.id,
        user_id=auth.user.id,
        action="integration.export",
        resource_type="meeting",
        resource_id=str(meeting_id),
        details={"provider": body.provider, "export_kind": body.export_kind, "email_to": email_to},
        ip_address=_client_ip(request),
    )

    export = ExportRecord(
        id=record.id,
        provider=record.provider,
        export_kind=record.export_kind,
        status=record.status.value,
        external_ref=record.external_ref,
        error_message=record.error_message,
        created_at=record.created_at,
    )
    msg = (
        "Export simulated locally (stub mode — no external API called)."
        if settings.integrations_stub_mode
        else "Export completed successfully."
    )
    return ExportResponse(export=export, message=msg)


@router.get("/meetings/{meeting_id}/integrations/exports", response_model=list[ExportRecord])
def get_exports(
    meeting_id: int,
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> list[ExportRecord]:
    get_workspace_meeting(db, meeting_id, auth.workspace.id)
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
