from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MeetingCreateResponse(BaseModel):
    id: int
    status: str


class MeetingListItem(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    status: str
    original_filename: str


class MeetingDetail(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    status: str
    original_filename: str
    meeting_start: Optional[str]
    timezone: Optional[str]
    error_message: Optional[str]


class MeetingResults(BaseModel):
    status: str
    transcript: Optional[dict]
    insights: Optional[dict]

