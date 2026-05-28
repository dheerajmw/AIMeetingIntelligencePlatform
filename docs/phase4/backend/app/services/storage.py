from __future__ import annotations

from pathlib import Path

from ..config import settings


def uploads_dir() -> Path:
    p = settings.storage_root / "uploads"
    p.mkdir(parents=True, exist_ok=True)
    return p


def artifacts_dir() -> Path:
    p = settings.storage_root / "artifacts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def meeting_artifacts_dir(meeting_id: int) -> Path:
    p = artifacts_dir() / str(meeting_id)
    p.mkdir(parents=True, exist_ok=True)
    return p

