from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text
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


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    status: Mapped[MeetingStatus] = mapped_column(Enum(MeetingStatus), default=MeetingStatus.UPLOADED)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # input
    original_filename: Mapped[str] = mapped_column(String(300))
    upload_path: Mapped[str] = mapped_column(String(600))

    meeting_start: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ISO8601 string (MVP)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # outputs
    transcript_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    insights_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    stt_model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    schema_version: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

