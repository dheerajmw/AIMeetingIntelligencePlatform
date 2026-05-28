from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import Meeting, MeetingStatus

_executor = ThreadPoolExecutor(max_workers=2)


def enqueue_process_meeting(meeting_id: int) -> str:
    """
    Enqueue a background job.

    - If Redis/RQ is available, use it.
    - Otherwise, fall back to an in-process thread executor (still async for the API caller).
    """
    try:
        from .queue import get_queue

        q = get_queue()
        # Fail fast if Redis isn't reachable
        q.connection.ping()
        job = q.enqueue("app.tasks.process_meeting", meeting_id, job_timeout="2h")
        return job.id
    except Exception:
        from ..tasks import process_meeting

        _executor.submit(process_meeting, meeting_id)
        return f"local:{meeting_id}"


def set_status(db: Session, meeting: Meeting, status: MeetingStatus, error_message: Optional[str] = None) -> None:
    meeting.status = status
    meeting.error_message = error_message
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

