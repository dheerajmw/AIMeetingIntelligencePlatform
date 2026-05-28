from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ...config import settings
from ...db.models import LiveChunk, LiveSession, LiveSessionStatus
from ...pipeline.diarize import label_speakers_by_pauses
from ...pipeline.llm import LlmConfig, generate_insights_from_segments
from ...pipeline.schemas import TranscriptSegment
from ...pipeline.transcribe import transcribe_with_whisper
from ...services.search.index import index_meeting_from_live
from .audio_decode import decode_audio_payload
from .chunk_store import chunk_path, live_session_dir
from .rolling_llm import rolling_draft_insights


def _segments_to_text(segments: list[dict]) -> str:
    lines = []
    for s in segments:
        text = (s.get("text") or "").strip()
        if not text:
            continue
        speaker = s.get("speaker_id")
        prefix = f"{speaker} " if speaker else ""
        lines.append(f"[{s.get('start_s', 0):.1f}-{s.get('end_s', 0):.1f}] {prefix}{text}")
    return "\n".join(lines)


def _get_draft_segments(session: LiveSession) -> list[dict]:
    draft = session.draft_transcript_json or {}
    return list(draft.get("segments") or [])


def process_audio_chunk(
    db: Session,
    session: LiveSession,
    seq: int,
    data_base64: str,
    fmt: str = "wav",
    sample_rate: int = 16000,
) -> dict:
    if session.status != LiveSessionStatus.ACTIVE:
        raise ValueError(f"Session is not active (status={session.status.value})")

    if seq <= session.last_processed_seq:
        return {"duplicate": True, "seq": seq, "last_processed_seq": session.last_processed_seq}

    existing = (
        db.query(LiveChunk)
        .filter(LiveChunk.session_id == session.id, LiveChunk.seq == seq)
        .one_or_none()
    )
    if existing and existing.processed:
        session.last_processed_seq = max(session.last_processed_seq, seq)
        db.add(session)
        db.commit()
        return {"duplicate": True, "seq": seq, "last_processed_seq": session.last_processed_seq}

    dest = chunk_path(session.id, seq, ext="wav" if fmt in {"wav", "pcm", "pcm_s16le"} else fmt)
    tmp_wav, duration = decode_audio_payload(data_base64, fmt=fmt, sample_rate=sample_rate)
    shutil.move(str(tmp_wav), dest)

    if existing:
        chunk = existing
        chunk.storage_path = str(dest)
        chunk.duration_s = duration
        chunk.processed = False
    else:
        chunk = LiveChunk(
            session_id=session.id,
            seq=seq,
            storage_path=str(dest),
            duration_s=duration,
            processed=False,
        )
        db.add(chunk)
    db.commit()

    offset = session.audio_duration_s
    segments, stt_info = transcribe_with_whisper(
        input_path=dest,
        model_name=settings.whisper_model,
        enable_diarization=settings.enable_diarization,
        diarization_pause_threshold_s=settings.diarization_pause_threshold_s,
    )

    chunk_segments: list[dict] = []
    for seg in segments:
        chunk_segments.append(
            TranscriptSegment(
                start_s=seg.start_s + offset,
                end_s=seg.end_s + offset,
                text=seg.text,
                speaker_id=seg.speaker_id,
            ).model_dump()
        )

    all_segments = _get_draft_segments(session) + chunk_segments
    if settings.enable_diarization:
        labeled = label_speakers_by_pauses(
            [TranscriptSegment(**s) for s in all_segments],
            pause_threshold_s=settings.diarization_pause_threshold_s,
        )
        all_segments = [s.model_dump() for s in labeled]

    session.draft_transcript_json = {
        "is_draft": True,
        "stt": {"engine": "whisper", **stt_info, "model": settings.whisper_model},
        "segments": all_segments,
    }
    session.audio_duration_s = offset + duration
    session.last_processed_seq = seq
    chunk.processed = True

    should_roll = (seq % max(1, settings.live_rolling_llm_every_n_chunks)) == 0
    if should_roll and all_segments:
        draft_insights = rolling_draft_insights(
            transcript_text=_segments_to_text(all_segments),
            meeting_title=session.title,
            previous_draft=session.draft_insights_json,
        )
        session.draft_insights_json = draft_insights

    db.add(session)
    db.add(chunk)
    db.commit()
    db.refresh(session)

    return {
        "duplicate": False,
        "seq": seq,
        "last_processed_seq": session.last_processed_seq,
        "draft_transcript_json": session.draft_transcript_json,
        "draft_insights_json": session.draft_insights_json,
    }


def finalize_session(db: Session, session_id: int) -> LiveSession:
    session = db.get(LiveSession, session_id)
    if not session:
        raise ValueError("Live session not found")
    if session.status not in {LiveSessionStatus.ACTIVE, LiveSessionStatus.FAILED}:
        return session

    session.status = LiveSessionStatus.FINALIZING
    session.error_message = None
    db.add(session)
    db.commit()
    db.refresh(session)

    try:
        segments_raw = _get_draft_segments(session)
        segments = [TranscriptSegment(**s) for s in segments_raw]

        cfg = LlmConfig(model=settings.groq_model, chunk_max_chars=settings.llm_chunk_max_chars)
        final_insights = generate_insights_from_segments(
            segments=segments,
            meeting_title=session.title,
            meeting_start_iso=session.meeting_start,
            timezone_name=session.timezone,
            cfg=cfg,
        )
        final_insights_dict = final_insights.model_dump(mode="json")
        final_insights_dict["is_draft"] = False

        session.final_transcript_json = session.draft_transcript_json
        if session.final_transcript_json:
            session.final_transcript_json["is_draft"] = False
        session.final_insights_json = final_insights_dict
        session.status = LiveSessionStatus.READY
        db.add(session)
        db.commit()
        db.refresh(session)

        index_meeting_from_live(db, session)
        return session
    except Exception as e:
        session.status = LiveSessionStatus.FAILED
        session.error_message = str(e)
        db.add(session)
        db.commit()
        db.refresh(session)
        raise
