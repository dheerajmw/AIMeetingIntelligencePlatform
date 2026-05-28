from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ...db.models import LiveSession, LiveSessionStatus, Meeting, MeetingSearchDocument, MeetingStatus
from .semantic import SemanticHit, rank_semantic


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _join_segments(transcript_json: Optional[dict]) -> str:
    if not transcript_json:
        return ""
    parts: list[str] = []
    for seg in transcript_json.get("segments") or []:
        t = (seg.get("text") or "").strip()
        if t:
            parts.append(t)
    return " ".join(parts)


def _join_insights_fields(insights_json: Optional[dict]) -> tuple[str, str, str]:
    if not insights_json:
        return "", "", ""

    summary = (insights_json.get("executive_summary") or "").strip()
    decisions = " ".join(
        (d.get("decision") or "").strip() for d in (insights_json.get("decisions_made") or [])
    )
    actions = " ".join(
        (a.get("title") or a.get("action") or "").strip() for a in (insights_json.get("action_items") or [])
    )
    return summary, decisions, actions


def build_search_fields(meeting: Meeting) -> dict[str, str]:
    title = (meeting.title or meeting.original_filename or "").strip()
    transcript = _join_segments(meeting.transcript_json)
    summary, decisions, actions = _join_insights_fields(meeting.insights_json)
    document_text = "\n".join(
        part for part in [title, summary, decisions, actions, transcript] if part
    ).strip()
    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "decisions": decisions,
        "action_items": actions,
        "document_text": document_text,
    }


def index_meeting(db: Session, meeting: Meeting) -> None:
    if meeting.status != MeetingStatus.READY:
        return

    fields = build_search_fields(meeting)
    if not fields["document_text"]:
        return

    existing = db.get(MeetingSearchDocument, meeting.id)
    if existing:
        existing.title = fields["title"]
        existing.document_text = fields["document_text"]
        existing.indexed_at = _utcnow()
    else:
        db.add(
            MeetingSearchDocument(
                meeting_id=meeting.id,
                title=fields["title"],
                document_text=fields["document_text"],
                indexed_at=_utcnow(),
            )
        )

    db.execute(text("DELETE FROM meeting_fts WHERE meeting_id = :mid"), {"mid": meeting.id})
    db.execute(
        text(
            """
            INSERT INTO meeting_fts (meeting_id, title, transcript, summary, decisions, action_items)
            VALUES (:meeting_id, :title, :transcript, :summary, :decisions, :action_items)
            """
        ),
        {
            "meeting_id": meeting.id,
            "title": fields["title"],
            "transcript": fields["transcript"],
            "summary": fields["summary"],
            "decisions": fields["decisions"],
            "action_items": fields["action_items"],
        },
    )
    db.commit()


def keyword_search(db: Session, query: str, limit: int = 20) -> list[dict]:
    q = query.strip()
    if not q:
        return []

    rows = db.execute(
        text(
            """
            SELECT meeting_id, snippet(meeting_fts, 2, '<b>', '</b>', '…', 20) AS snippet,
                   bm25(meeting_fts) AS score
            FROM meeting_fts
            WHERE meeting_fts MATCH :query
            ORDER BY score
            LIMIT :limit
            """
        ),
        {"query": q, "limit": limit},
    ).mappings().all()

    hits: list[dict] = []
    for row in rows:
        doc = db.get(MeetingSearchDocument, int(row["meeting_id"]))
        hits.append(
            {
                "meeting_id": int(row["meeting_id"]),
                "title": doc.title if doc else f"Meeting #{row['meeting_id']}",
                "score": float(row["score"]),
                "snippet": row["snippet"] or "",
                "mode": "keyword",
            }
        )
    return hits


def semantic_search(db: Session, query: str, limit: int = 20) -> list[dict]:
    docs = db.execute(select(MeetingSearchDocument)).scalars().all()
    ranked: list[SemanticHit] = rank_semantic(
        query,
        [(d.meeting_id, d.document_text) for d in docs],
        limit=limit,
    )
    title_by_id = {d.meeting_id: d.title for d in docs}
    return [
        {
            "meeting_id": h.meeting_id,
            "title": title_by_id.get(h.meeting_id, f"Meeting #{h.meeting_id}"),
            "score": h.score,
            "snippet": h.snippet,
            "mode": "semantic",
        }
        for h in ranked
    ]


def search_meetings(db: Session, query: str, mode: str = "keyword", limit: int = 20) -> list[dict]:
    if mode == "semantic":
        return semantic_search(db, query, limit=limit)
    return keyword_search(db, query, limit=limit)


def reindex_all_ready(db: Session) -> int:
    meetings = db.execute(select(Meeting).where(Meeting.status == MeetingStatus.READY)).scalars().all()
    count = 0
    for meeting in meetings:
        index_meeting(db, meeting)
        count += 1
    return count


LIVE_SEARCH_ID_OFFSET = 1_000_000


def live_search_meeting_id(session_id: int) -> int:
    return LIVE_SEARCH_ID_OFFSET + session_id


def index_meeting_from_live(db: Session, session: LiveSession) -> None:
    if session.status != LiveSessionStatus.READY:
        return

    meeting_id = live_search_meeting_id(session.id)
    title = (session.title or f"Live session #{session.id}").strip()
    transcript = _join_segments(session.final_transcript_json or session.draft_transcript_json)
    summary, decisions, actions = _join_insights_fields(session.final_insights_json or session.draft_insights_json)
    document_text = "\n".join(
        part for part in [title, summary, decisions, actions, transcript] if part
    ).strip()
    if not document_text:
        return

    fields = {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "decisions": decisions,
        "action_items": actions,
        "document_text": document_text,
    }

    existing = db.get(MeetingSearchDocument, meeting_id)
    if existing:
        existing.title = fields["title"]
        existing.document_text = fields["document_text"]
        existing.indexed_at = _utcnow()
    else:
        db.add(
            MeetingSearchDocument(
                meeting_id=meeting_id,
                title=fields["title"],
                document_text=fields["document_text"],
                indexed_at=_utcnow(),
            )
        )

    db.execute(text("DELETE FROM meeting_fts WHERE meeting_id = :mid"), {"mid": meeting_id})
    db.execute(
        text(
            """
            INSERT INTO meeting_fts (meeting_id, title, transcript, summary, decisions, action_items)
            VALUES (:meeting_id, :title, :transcript, :summary, :decisions, :action_items)
            """
        ),
        {
            "meeting_id": meeting_id,
            "title": fields["title"],
            "transcript": fields["transcript"],
            "summary": fields["summary"],
            "decisions": fields["decisions"],
            "action_items": fields["action_items"],
        },
    )
    db.commit()
