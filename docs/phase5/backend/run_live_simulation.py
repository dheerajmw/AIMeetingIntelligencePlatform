#!/usr/bin/env python3
"""Simulate a live meeting by streaming a local WAV in timed chunks."""
from __future__ import annotations

import base64
import sys
import time
from pathlib import Path

import soundfile as sf

from app.db.init_db import init_db
from app.db.models import LiveSession, LiveSessionStatus
from app.db.session import SessionLocal
from app.services.live.processor import finalize_session, process_audio_chunk


def main() -> int:
    sample = Path(__file__).resolve().parents[1] / "storage/samples/ami-en2002a-60s.wav"
    if len(sys.argv) > 1:
        sample = Path(sys.argv[1])
    if not sample.exists():
        print(f"Sample not found: {sample}", file=sys.stderr)
        return 1

    chunk_seconds = 10
    init_db()
    db = SessionLocal()

    session = LiveSession(
        title=f"Simulated live — {sample.name}",
        meeting_start="2005-02-08T10:00:00+00:00",
        timezone="Europe/London",
        status=LiveSessionStatus.ACTIVE,
        draft_transcript_json={"is_draft": True, "segments": []},
        draft_insights_json={"is_draft": True, "executive_summary": "Live meeting started."},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    print(f"Live session #{session.id} created")

    audio, sr = sf.read(str(sample), dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    step = int(chunk_seconds * sr)
    seq = 1
    for start in range(0, len(audio), step):
        chunk = audio[start : start + step]
        import io

        buf = io.BytesIO()
        sf.write(buf, chunk, sr, format="WAV", subtype="PCM_16")
        payload = base64.b64encode(buf.getvalue()).decode("ascii")

        print(f"Sending chunk seq={seq} …")
        result = process_audio_chunk(
            db,
            session,
            seq=seq,
            data_base64=payload,
            fmt="wav",
            sample_rate=sr,
        )
        db.refresh(session)
        segs = (result.get("draft_transcript_json") or {}).get("segments") or []
        print(f"  processed={not result.get('duplicate')} segments_total={len(segs)}")
        seq += 1
        time.sleep(0.2)

    print("Finalizing …")
    session = finalize_session(db, session.id)
    print(f"Final status: {session.status.value}")
    insights = session.final_insights_json or {}
    print("Summary:", (insights.get("executive_summary") or "")[:240])
    db.close()
    return 0 if session.status == LiveSessionStatus.READY else 2


if __name__ == "__main__":
    raise SystemExit(main())
