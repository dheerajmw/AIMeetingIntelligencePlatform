from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    start_s: float = Field(..., ge=0)
    end_s: float = Field(..., ge=0)
    text: str = Field(..., min_length=1)


class Decision(BaseModel):
    decision: str = Field(..., min_length=1)
    owner: str = Field(default="Not identified")
    deadline: str = Field(default="Not identified")


class ActionItem(BaseModel):
    action: str = Field(..., min_length=1)
    owner: str = Field(default="Not identified")
    deadline: str = Field(default="Not identified")


class MeetingInsights(BaseModel):
    schema_version: Literal["v1"] = "v1"
    llm_model: str
    prompt_version: Literal["v1"] = "v1"
    generated_at: datetime

    executive_summary: str = Field(..., min_length=1)
    key_discussion_points: list[str] = Field(default_factory=list)
    decisions_made: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)

