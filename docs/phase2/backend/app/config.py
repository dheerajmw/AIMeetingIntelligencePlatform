from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    storage_root: Path = Path(__file__).resolve().parents[2] / "storage"
    database_url: str = "sqlite:///./app.db"

    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "meetings"

    whisper_model: str = "base"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_chunk_max_chars: int = 12000

    enable_diarization: bool = True
    diarization_pause_threshold_s: float = 1.5


settings = Settings()
