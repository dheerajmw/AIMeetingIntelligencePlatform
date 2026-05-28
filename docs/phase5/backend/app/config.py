from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


def _default_storage_root() -> Path:
    return Path(__file__).resolve().parents[2] / "storage"


class Settings(BaseModel):
    storage_root: Path = _default_storage_root()
    database_url: str = "sqlite:///./app.db"
    cors_origins: list[str] = []

    redis_url: str = "redis://localhost:6379/0"
    rq_queue_name: str = "meetings"

    whisper_model: str = "base"
    groq_model: str = "llama-3.3-70b-versatile"
    llm_chunk_max_chars: int = 12000

    enable_diarization: bool = True
    diarization_pause_threshold_s: float = 1.5

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

    live_rolling_llm_every_n_chunks: int = 2
    live_max_draft_transcript_chars: int = 8000

    # Phase 5 — enterprise
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60 * 24
    auth_disabled: bool = False
    dev_auth_enabled: bool = True

    encryption_key: Optional[str] = None

    default_workspace_slug: str = "default"
    default_data_region: str = "us-east-1"
    default_retention_days: int = 90
    default_max_meetings_per_month: int = 100
    default_max_llm_tokens_per_month: int = 500_000

    oidc_issuer: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_redirect_uri: str = "http://127.0.0.1:5175/auth/callback"

    # When true, exports succeed locally without Jira/Slack/etc. credentials (demo mode).
    integrations_stub_mode: bool = True


def _parse_cors_origins(raw: Optional[str]) -> list[str]:
    if not raw or not raw.strip():
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def load_settings() -> Settings:
    jwt_secret = os.getenv("JWT_SECRET") or secrets.token_urlsafe(32)
    storage_root = os.getenv("STORAGE_ROOT")
    return Settings(
        storage_root=Path(storage_root) if storage_root else _default_storage_root(),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./app.db"),
        cors_origins=_parse_cors_origins(os.getenv("CORS_ORIGINS")),
        whisper_model=os.getenv("WHISPER_MODEL", "base"),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        jwt_secret=jwt_secret,
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24))),
        auth_disabled=os.getenv("AUTH_DISABLED", "false").lower() in {"1", "true", "yes"},
        dev_auth_enabled=os.getenv("DEV_AUTH_ENABLED", "true").lower() in {"1", "true", "yes"},
        encryption_key=os.getenv("ENCRYPTION_KEY"),
        default_data_region=os.getenv("DEFAULT_DATA_REGION", "us-east-1"),
        default_retention_days=int(os.getenv("DEFAULT_RETENTION_DAYS", "90")),
        default_max_meetings_per_month=int(os.getenv("DEFAULT_MAX_MEETINGS_PER_MONTH", "100")),
        default_max_llm_tokens_per_month=int(os.getenv("DEFAULT_MAX_LLM_TOKENS_PER_MONTH", "500000")),
        oidc_issuer=os.getenv("OIDC_ISSUER"),
        oidc_client_id=os.getenv("OIDC_CLIENT_ID"),
        oidc_client_secret=os.getenv("OIDC_CLIENT_SECRET"),
        oidc_redirect_uri=os.getenv("OIDC_REDIRECT_URI", "http://127.0.0.1:5175/auth/callback"),
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
        integrations_stub_mode=os.getenv("INTEGRATIONS_STUB_MODE", "true").lower()
        in {"1", "true", "yes"},
    )


settings = load_settings()
