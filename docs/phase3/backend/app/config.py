from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


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

    # Integrations (configure via environment variables)
    jira_base_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_project_key: Optional[str] = None

    linear_api_key: Optional[str] = None
    linear_team_id: Optional[str] = None

    trello_api_key: Optional[str] = None
    trello_token: Optional[str] = None
    trello_list_id: Optional[str] = None

    slack_webhook_url: Optional[str] = None

    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_to: Optional[str] = None


def load_settings() -> Settings:
    return Settings(
        jira_base_url=os.getenv("JIRA_BASE_URL"),
        jira_email=os.getenv("JIRA_EMAIL"),
        jira_api_token=os.getenv("JIRA_API_TOKEN"),
        jira_project_key=os.getenv("JIRA_PROJECT_KEY"),
        linear_api_key=os.getenv("LINEAR_API_KEY"),
        linear_team_id=os.getenv("LINEAR_TEAM_ID"),
        trello_api_key=os.getenv("TRELLO_API_KEY"),
        trello_token=os.getenv("TRELLO_TOKEN"),
        trello_list_id=os.getenv("TRELLO_LIST_ID"),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        smtp_from=os.getenv("SMTP_FROM"),
        smtp_to=os.getenv("SMTP_TO"),
    )


settings = load_settings()
