from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..auth.dependencies import AuthContext, require_read, require_write
from ..db.models import LiveSession, LiveSessionStatus
from ..db.session import SessionLocal, get_db
from ..enterprise.audit import write_audit
from ..enterprise.retention import soft_delete_live_session
from ..services.access import get_workspace_live_session
from ..services.live.processor import finalize_session, process_audio_chunk
from .schemas import LiveSessionCreate, LiveSessionDetail, LiveSessionResults

router = APIRouter(prefix="/live", tags=["live"])

_executor = ThreadPoolExecutor(max_workers=2)


def _session_detail(session: LiveSession) -> LiveSessionDetail:
    return LiveSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        status=session.status.value,
        meeting_start=session.meeting_start,
        timezone=session.timezone,
        last_processed_seq=session.last_processed_seq,
        audio_duration_s=session.audio_duration_s,
        error_message=session.error_message,
    )


@router.post("/sessions", response_model=LiveSessionDetail)
def create_live_session(
    body: LiveSessionCreate,
    request: Request,
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> LiveSessionDetail:
    session = LiveSession(
        workspace_id=auth.workspace.id,
        title=body.title,
        meeting_start=body.meeting_start,
        timezone=body.timezone,
        status=LiveSessionStatus.ACTIVE,
        draft_transcript_json={"is_draft": True, "segments": []},
        draft_insights_json={"is_draft": True, "executive_summary": "Live meeting started."},
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    write_audit(
        db,
        workspace_id=auth.workspace.id,
        user_id=auth.user.id,
        action="live.session.create",
        resource_type="live_session",
        resource_id=str(session.id),
        ip_address=request.client.host if request.client else None,
    )
    return _session_detail(session)


@router.get("/sessions", response_model=list[LiveSessionDetail])
def list_live_sessions(
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> list[LiveSessionDetail]:
    sessions = db.execute(
        select(LiveSession)
        .where(LiveSession.workspace_id == auth.workspace.id, LiveSession.deleted_at.is_(None))
        .order_by(desc(LiveSession.created_at))
    ).scalars().all()
    return [_session_detail(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=LiveSessionDetail)
def get_live_session(
    session_id: int,
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> LiveSessionDetail:
    session = get_workspace_live_session(db, session_id, auth.workspace.id)
    return _session_detail(session)


@router.get("/sessions/{session_id}/results", response_model=LiveSessionResults)
def get_live_results(
    session_id: int,
    auth: AuthContext = Depends(require_read),
    db: Session = Depends(get_db),
) -> LiveSessionResults:
    session = get_workspace_live_session(db, session_id, auth.workspace.id)

    if session.status == LiveSessionStatus.READY:
        return LiveSessionResults(
            status=session.status.value,
            is_draft=False,
            transcript=session.final_transcript_json,
            insights=session.final_insights_json,
        )

    return LiveSessionResults(
        status=session.status.value,
        is_draft=True,
        transcript=session.draft_transcript_json,
        insights=session.draft_insights_json,
    )


@router.post("/sessions/{session_id}/finalize", response_model=LiveSessionResults)
def finalize_live_session(
    session_id: int,
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> LiveSessionResults:
    get_workspace_live_session(db, session_id, auth.workspace.id)

    try:
        session = finalize_session(db, session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return LiveSessionResults(
        status=session.status.value,
        is_draft=False,
        transcript=session.final_transcript_json,
        insights=session.final_insights_json,
    )


@router.delete("/sessions/{session_id}")
def delete_live_session(
    session_id: int,
    request: Request,
    auth: AuthContext = Depends(require_write),
    db: Session = Depends(get_db),
) -> dict:
    session = get_workspace_live_session(db, session_id, auth.workspace.id)
    soft_delete_live_session(db, session)
    write_audit(
        db,
        workspace_id=auth.workspace.id,
        user_id=auth.user.id,
        action="live.session.soft_delete",
        resource_type="live_session",
        resource_id=str(session_id),
        ip_address=request.client.host if request.client else None,
    )
    return {"ok": True, "session_id": session_id}


def _process_chunk_sync(session_id: int, seq: int, data_base64: str, fmt: str, sample_rate: int) -> dict:
    db = SessionLocal()
    try:
        session = db.get(LiveSession, session_id)
        if not session or session.deleted_at is not None:
            raise ValueError("Live session not found")
        return process_audio_chunk(
            db,
            session,
            seq=seq,
            data_base64=data_base64,
            fmt=fmt,
            sample_rate=sample_rate,
        )
    finally:
        db.close()


@router.websocket("/sessions/{session_id}/stream")
async def live_stream(websocket: WebSocket, session_id: int) -> None:
    await websocket.accept()

    db = SessionLocal()
    session = db.get(LiveSession, session_id)
    db.close()
    if not session or session.deleted_at is not None:
        await websocket.send_json({"type": "error", "message": "Live session not found"})
        await websocket.close()
        return

    await websocket.send_json(
        {
            "type": "session_state",
            "session_id": session_id,
            "status": session.status.value,
            "last_processed_seq": session.last_processed_seq,
        }
    )

    loop = asyncio.get_event_loop()
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            mtype = msg.get("type")

            if mtype == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if mtype == "audio_chunk":
                seq = int(msg["seq"])
                data_base64 = msg["data_base64"]
                fmt = msg.get("format", "wav")
                sample_rate = int(msg.get("sample_rate", 16000))

                result = await loop.run_in_executor(
                    _executor,
                    _process_chunk_sync,
                    session_id,
                    seq,
                    data_base64,
                    fmt,
                    sample_rate,
                )

                await websocket.send_json(
                    {
                        "type": "ack",
                        "seq": seq,
                        "duplicate": result.get("duplicate", False),
                        "last_processed_seq": result.get("last_processed_seq"),
                    }
                )

                if not result.get("duplicate"):
                    await websocket.send_json(
                        {
                            "type": "draft_update",
                            "is_draft": True,
                            "last_processed_seq": result.get("last_processed_seq"),
                            "transcript": result.get("draft_transcript_json"),
                            "insights": result.get("draft_insights_json"),
                        }
                    )
                continue

            await websocket.send_json({"type": "error", "message": f"Unknown message type: {mtype}"})

    except WebSocketDisconnect:
        return
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
