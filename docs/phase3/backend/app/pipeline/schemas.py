from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TimestampRange(BaseModel):
    start_s: float = Field(..., ge=0)
    end_s: float = Field(..., ge=0)


class TranscriptSegment(BaseModel):
    start_s: float = Field(..., ge=0)
    end_s: float = Field(..., ge=0)
    text: str = Field(..., min_length=1)
    speaker_id: Optional[str] = None


class Decision(BaseModel):
    decision: str = Field(..., min_length=1)
    owner: str = Field(default="Not identified")
    due_date: str = Field(default="Not identified")
    evidence_quote: str = Field(default="Not identified")
    timestamp_range: Optional[TimestampRange] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class ActionItem(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(default="")
    owner: str = Field(default="Not identified")
    due_date: str = Field(default="Not identified")
    priority: str = Field(default="Not identified")
    evidence_quote: str = Field(default="Not identified")
    timestamp_range: Optional[TimestampRange] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class MeetingInsights(BaseModel):
    schema_version: Literal["v2"] = "v2"
    llm_model: str
    prompt_version: Literal["v2"] = "v2"
    generated_at: datetime

    executive_summary: str = Field(..., min_length=1)
    key_discussion_points: list[str] = Field(default_factory=list)
    decisions_made: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
