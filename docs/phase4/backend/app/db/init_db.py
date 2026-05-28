from __future__ import annotations

from sqlalchemy import text

from .base import Base
from .session import engine
from . import models  # noqa: F401


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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    init_search_fts()
