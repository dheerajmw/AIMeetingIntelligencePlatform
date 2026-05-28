from __future__ import annotations

from pathlib import Path

from ...config import settings


def live_session_dir(session_id: int) -> Path:
    p = settings.storage_root / "live" / str(session_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def chunk_path(session_id: int, seq: int, ext: str = "wav") -> Path:
    return live_session_dir(session_id) / f"chunk_{seq:06d}.{ext}"
