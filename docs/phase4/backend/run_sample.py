#!/usr/bin/env python3
"""Run Phase 3 pipeline on a local sample recording."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from app.db.init_db import init_db
from app.db.models import Meeting, MeetingStatus
from app.db.session import SessionLocal
from app.services.search.index import index_meeting, keyword_search, semantic_search
from app.services.storage import meeting_artifacts_dir, uploads_dir
from app.tasks import process_meeting


def main() -> int:
    sample = Path(__file__).resolve().parents[1] / "storage/samples/ami-en2002a-60s.wav"
    if not sample.exists():
        print(f"Sample not found: {sample}", file=sys.stderr)
        return 1

    init_db()
    db = SessionLocal()

    dest = uploads_dir() / sample.name
    shutil.copy2(sample, dest)

    meeting = Meeting(
        title="AMI EN2002a sample (60s)",
        original_filename=sample.name,
        upload_path=str(dest),
        status=MeetingStatus.UPLOADED,
        meeting_start="2005-02-08T10:00:00+00:00",
        timezone="Europe/London",
        enable_diarization=True,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    meeting_artifacts_dir(meeting.id)

    print(f"Processing meeting #{meeting.id} from {sample.name} …")
    db.close()

    process_meeting(meeting.id)

    db = SessionLocal()
    meeting = db.get(Meeting, meeting.id)
    if not meeting:
        print("Meeting missing after processing", file=sys.stderr)
        return 1

    print(f"Status: {meeting.status.value}")
    if meeting.error_message:
        print(f"Error: {meeting.error_message}")

    if meeting.status == MeetingStatus.READY:
        index_meeting(db, meeting)
        kw = keyword_search(db, "project", limit=3)
        sem = semantic_search(db, "decision action item", limit=3)
        print("\nKeyword search hits:", json.dumps(kw, indent=2))
        print("\nSemantic search hits:", json.dumps(sem, indent=2))
        print("\nInsights preview:")
        insights = meeting.insights_json or {}
        print(json.dumps(
            {
                "executive_summary": insights.get("executive_summary"),
                "decisions_count": len(insights.get("decisions_made") or []),
                "action_items_count": len(insights.get("action_items") or []),
                "action_items": (insights.get("action_items") or [])[:3],
            },
            indent=2,
            ensure_ascii=False,
        ))

    artifacts = meeting_artifacts_dir(meeting.id)
    print(f"\nArtifacts: {artifacts}")
    db.close()
    return 0 if meeting.status == MeetingStatus.READY else 2


if __name__ == "__main__":
    raise SystemExit(main())
