from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MeetingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    TRANSCRIBING = "TRANSCRIBING"
    ANALYZING = "ANALYZING"
    READY = "READY"
    FAILED_TRANSCRIPTION = "FAILED_TRANSCRIPTION"
    FAILED_ANALYSIS = "FAILED_ANALYSIS"


class ExportStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class LiveSessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FINALIZING = "FINALIZING"
    READY = "READY"
    FAILED = "FAILED"


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    status: Mapped[MeetingStatus] = mapped_column(Enum(MeetingStatus), default=MeetingStatus.UPLOADED)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    original_filename: Mapped[str] = mapped_column(String(300))
    upload_path: Mapped[str] = mapped_column(String(600))

    meeting_start: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    enable_diarization: Mapped[bool] = mapped_column(default=True)

    transcript_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    insights_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    stt_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    schema_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)


class MeetingSearchDocument(Base):
    __tablename__ = "meeting_search_documents"

    meeting_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    document_text: Mapped[str] = mapped_column(Text)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IntegrationExport(Base):
    __tablename__ = "integration_exports"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_integration_export_idempotency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meeting_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(32))
    export_kind: Mapped[str] = mapped_column(String(32))
    idempotency_key: Mapped[str] = mapped_column(String(200))

    status: Mapped[ExportStatus] = mapped_column(Enum(ExportStatus), default=ExportStatus.PENDING)
    external_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class LiveSession(Base):
    __tablename__ = "live_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    status: Mapped[LiveSessionStatus] = mapped_column(Enum(LiveSessionStatus), default=LiveSessionStatus.ACTIVE)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    meeting_start: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    last_processed_seq: Mapped[int] = mapped_column(Integer, default=0)
    audio_duration_s: Mapped[float] = mapped_column(Float, default=0.0)

    draft_transcript_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    draft_insights_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    final_transcript_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    final_insights_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class LiveChunk(Base):
    __tablename__ = "live_chunks"
    __table_args__ = (UniqueConstraint("session_id", "seq", name="uq_live_chunk_session_seq"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, index=True)
    seq: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(600))
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    processed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
