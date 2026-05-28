from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


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


class SearchHit(BaseModel):
    meeting_id: int
    title: str
    score: float
    snippet: str
    mode: str


class SearchResponse(BaseModel):
    query: str
    mode: str
    hits: list[SearchHit]


class ExportRequest(BaseModel):
    provider: Literal["jira", "linear", "trello", "slack", "email"]
    export_kind: Literal["action_items", "summary"] = "action_items"
    force: bool = False
    # Used for provider=email only. If omitted, backend sends to current user's email.
    email_to: Optional[str] = None


class ExportRecord(BaseModel):
    id: int
    provider: str
    export_kind: str
    status: str
    external_ref: Optional[str]
    error_message: Optional[str]
    created_at: datetime


class ExportResponse(BaseModel):
    export: ExportRecord
    message: str


class IntegrationProviderStatus(BaseModel):
    configured: bool
    ready: bool


class IntegrationsStatusResponse(BaseModel):
    stub_mode: bool
    providers: dict[str, IntegrationProviderStatus]


class ReindexResponse(BaseModel):
    indexed_count: int


class LiveSessionCreate(BaseModel):
    title: Optional[str] = None
    meeting_start: Optional[str] = None
    timezone: Optional[str] = None


class LiveSessionDetail(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    status: str
    meeting_start: Optional[str]
    timezone: Optional[str]
    last_processed_seq: int
    audio_duration_s: float
    error_message: Optional[str]


class LiveSessionResults(BaseModel):
    status: str
    is_draft: bool
    transcript: Optional[dict]
    insights: Optional[dict]


class SampleItem(BaseModel):
    id: str
    dataset: str
    title: str
    description: str
    filename: str
    duration_s: float
    language: str
    meeting_start: Optional[str] = None
    timezone: Optional[str] = None
    source_url: Optional[str] = None
    available: bool = True


class SampleListResponse(BaseModel):
    samples: list[SampleItem]


class SampleProcessResponse(BaseModel):
    id: int
    status: str
    sample_id: str
    message: str
