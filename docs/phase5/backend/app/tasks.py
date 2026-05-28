from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .db.models import Meeting, MeetingStatus, Workspace
from .db.session import SessionLocal
from .enterprise.cache import (
    lookup_analysis_cache,
    store_analysis_cache,
    touch_cache_hit,
    transcript_content_hash,
)
from .enterprise.encryption import cleanup_temp_decrypt, decrypt_upload_for_processing, encryption_enabled, encrypt_file_at_path
from .enterprise.quotas import check_llm_quota, record_llm_usage
from .pipeline.llm import LlmConfig, generate_insights_from_segments
from .pipeline.transcribe import transcribe_with_whisper
from .services.search.index import index_meeting
from .services.storage import meeting_artifacts_dir


def _estimate_tokens(transcript_json: dict) -> int:
    text = " ".join((s.get("text") or "") for s in (transcript_json.get("segments") or []))
    return max(500, len(text) // 4)


def process_meeting(meeting_id: int) -> None:
    db: Session = SessionLocal()
    decrypt_path: Path | None = None
    upload_path: Path | None = None
    try:
        meeting = db.get(Meeting, meeting_id)
        if not meeting or meeting.deleted_at is not None:
            return

        workspace = db.get(Workspace, meeting.workspace_id)
        if not workspace:
            return

        meeting.status = MeetingStatus.TRANSCRIBING
        meeting.error_message = None
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        upload_path = Path(meeting.upload_path)
        decrypt_path = decrypt_upload_for_processing(
            upload_path,
            meeting.id,
            meeting.upload_encrypted,
        )
        enable_diarization = meeting.enable_diarization if meeting.enable_diarization is not None else settings.enable_diarization

        segments, stt_info = transcribe_with_whisper(
            input_path=decrypt_path,
            model_name=settings.whisper_model,
            language=None,
            enable_diarization=enable_diarization,
            diarization_pause_threshold_s=settings.diarization_pause_threshold_s,
        )

        transcript_json = {
            "stt": {"engine": "whisper", **stt_info, "model": settings.whisper_model},
            "segments": [s.model_dump() for s in segments],
        }

        artifacts = meeting_artifacts_dir(meeting_id)
        (artifacts / "transcript.json").write_text(
            json.dumps(transcript_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        meeting.transcript_json = transcript_json
        meeting.stt_model_version = settings.whisper_model
        meeting.content_hash = transcript_content_hash(transcript_json)
        meeting.status = MeetingStatus.ANALYZING
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        cache_row = lookup_analysis_cache(
            db,
            workspace_id=meeting.workspace_id,
            content_hash=meeting.content_hash,
        )
        if cache_row:
            insights_json = cache_row.insights_json
            meeting.insights_json = insights_json
            meeting.llm_model = cache_row.llm_model
            meeting.schema_version = cache_row.schema_version
            meeting.prompt_version = insights_json.get("prompt_version")
            meeting.analysis_from_cache = True
            meeting.status = MeetingStatus.READY
            db.add(meeting)
            db.commit()
            touch_cache_hit(db, workspace, cache_row)
            (artifacts / "insights.json").write_text(
                json.dumps(insights_json, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            index_meeting(db, meeting)
            return

        est_tokens = _estimate_tokens(transcript_json)
        check_llm_quota(db, workspace, est_tokens)

        cfg = LlmConfig(
            model=settings.groq_model,
            chunk_max_chars=settings.llm_chunk_max_chars,
        )
        insights = generate_insights_from_segments(
            segments=segments,
            meeting_title=meeting.title,
            meeting_start_iso=meeting.meeting_start,
            timezone_name=meeting.timezone,
            cfg=cfg,
        )
        insights_json = insights.model_dump(mode="json")
        (artifacts / "insights.json").write_text(
            json.dumps(insights_json, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        meeting.insights_json = insights_json
        meeting.llm_model = settings.groq_model
        meeting.prompt_version = insights.prompt_version
        meeting.schema_version = insights.schema_version
        meeting.analysis_from_cache = False
        meeting.status = MeetingStatus.READY
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        record_llm_usage(db, workspace, est_tokens)
        store_analysis_cache(
            db,
            workspace_id=meeting.workspace_id,
            content_hash=meeting.content_hash,
            insights_json=insights_json,
            llm_model=settings.groq_model,
            schema_version=insights.schema_version,
        )
        index_meeting(db, meeting)

    except Exception as e:
        meeting = db.get(Meeting, meeting_id)
        if meeting:
            meeting.status = MeetingStatus.FAILED_ANALYSIS if meeting.transcript_json else MeetingStatus.FAILED_TRANSCRIPTION
            meeting.error_message = str(e)
            db.add(meeting)
            db.commit()
    finally:
        if decrypt_path and upload_path:
            cleanup_temp_decrypt(decrypt_path, upload_path)
        db.close()


def encrypt_meeting_upload(meeting_id: int) -> None:
    if not encryption_enabled():
        return
    db: Session = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if not meeting:
            return
        path = Path(meeting.upload_path)
        if path.exists() and not meeting.upload_encrypted:
            encrypt_file_at_path(path)
            meeting.upload_encrypted = True
            db.add(meeting)
            db.commit()
    finally:
        db.close()
