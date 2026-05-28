from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import AnalysisCache, Workspace
from .quotas import record_cache_hit


def transcript_content_hash(transcript_json: dict) -> str:
    payload = json.dumps(transcript_json, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def lookup_analysis_cache(
    db: Session,
    *,
    workspace_id: int,
    content_hash: str,
) -> Optional[AnalysisCache]:
    return db.execute(
        select(AnalysisCache).where(
            AnalysisCache.workspace_id == workspace_id,
            AnalysisCache.content_hash == content_hash,
        )
    ).scalar_one_or_none()


def store_analysis_cache(
    db: Session,
    *,
    workspace_id: int,
    content_hash: str,
    insights_json: dict,
    llm_model: str,
    schema_version: str,
) -> AnalysisCache:
    existing = lookup_analysis_cache(db, workspace_id=workspace_id, content_hash=content_hash)
    now = datetime.now(timezone.utc)
    if existing:
        existing.insights_json = insights_json
        existing.llm_model = llm_model
        existing.schema_version = schema_version
        existing.last_used_at = now
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    row = AnalysisCache(
        workspace_id=workspace_id,
        content_hash=content_hash,
        insights_json=insights_json,
        llm_model=llm_model,
        schema_version=schema_version,
        last_used_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def touch_cache_hit(db: Session, workspace: Workspace, cache_row: AnalysisCache) -> None:
    cache_row.last_used_at = datetime.now(timezone.utc)
    db.add(cache_row)
    db.commit()
    record_cache_hit(db, workspace)
