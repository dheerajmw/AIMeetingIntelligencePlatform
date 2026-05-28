from __future__ import annotations

from sqlalchemy import inspect, text

from .base import Base
from .session import engine
from . import models  # noqa: F401
from ..enterprise.seed import bootstrap


def init_search_fts() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS meeting_fts USING fts5(
                    meeting_id UNINDEXED,
                    title,
                    transcript,
                    summary,
                    decisions,
                    action_items,
                    tokenize='porter'
                )
                """
            )
        )


def _ensure_column(table: str, column: str, ddl: str) -> None:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns(table)}
    if column not in cols:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def migrate_legacy_schema() -> None:
    _ensure_column("meetings", "workspace_id", "workspace_id INTEGER NOT NULL DEFAULT 1")
    _ensure_column("meetings", "deleted_at", "deleted_at DATETIME")
    _ensure_column("meetings", "upload_encrypted", "upload_encrypted BOOLEAN NOT NULL DEFAULT 0")
    _ensure_column("meetings", "content_hash", "content_hash VARCHAR(64)")
    _ensure_column("meetings", "analysis_from_cache", "analysis_from_cache BOOLEAN NOT NULL DEFAULT 0")
    _ensure_column("live_sessions", "workspace_id", "workspace_id INTEGER NOT NULL DEFAULT 1")
    _ensure_column("live_sessions", "deleted_at", "deleted_at DATETIME")
    _ensure_column("meeting_search_documents", "workspace_id", "workspace_id INTEGER NOT NULL DEFAULT 1")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_legacy_schema()
    init_search_fts()
    from .session import SessionLocal

    db = SessionLocal()
    try:
        bootstrap(db)
    finally:
        db.close()
