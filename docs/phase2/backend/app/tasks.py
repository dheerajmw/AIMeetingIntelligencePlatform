from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from .config import settings
from .db.models import Meeting, MeetingStatus
from .db.session import SessionLocal
from .pipeline.llm import LlmConfig, generate_insights_from_segments
from .pipeline.transcribe import transcribe_with_whisper
from .services.storage import meeting_artifacts_dir


def process_meeting(meeting_id: int) -> None:
    db: Session = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if not meeting:
            return

        meeting.status = MeetingStatus.TRANSCRIBING
        meeting.error_message = None
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

        input_path = Path(meeting.upload_path)
        enable_diarization = meeting.enable_diarization if meeting.enable_diarization is not None else settings.enable_diarization

        segments, stt_info = transcribe_with_whisper(
            input_path=input_path,
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
        meeting.status = MeetingStatus.ANALYZING
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

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
        meeting.status = MeetingStatus.READY
        db.add(meeting)
        db.commit()
        db.refresh(meeting)

    except Exception as e:
        meeting = db.get(Meeting, meeting_id)
        if meeting:
            meeting.status = MeetingStatus.FAILED_ANALYSIS if meeting.transcript_json else MeetingStatus.FAILED_TRANSCRIPTION
            meeting.error_message = str(e)
            db.add(meeting)
            db.commit()
    finally:
        db.close()
