from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo


def _parse_meeting_start(meeting_start_iso: Optional[str], timezone_name: Optional[str]) -> Optional[datetime]:
    if not meeting_start_iso:
        return None
    try:
        dt = datetime.fromisoformat(meeting_start_iso.replace("Z", "+00:00"))
    except ValueError:
        return None

    if dt.tzinfo is None and timezone_name:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception:
            pass
    return dt


def anchor_relative_due_date(
    due_date: str,
    meeting_start_iso: Optional[str],
    timezone_name: Optional[str],
) -> str:
    """
    Best-effort normalization for common relative phrases when meeting start is known.
    Leaves absolute/unknown values unchanged.
    """
    if not due_date or due_date == "Not identified":
        return due_date

    anchor = _parse_meeting_start(meeting_start_iso, timezone_name)
    if anchor is None:
        return due_date

    text = due_date.strip().lower()
    tz = anchor.tzinfo

    if text in {"eod", "end of day", "by eod"}:
        end = anchor.replace(hour=23, minute=59, second=0, microsecond=0)
        return end.isoformat()

    if text == "tomorrow":
        return (anchor + timedelta(days=1)).date().isoformat()

    if text == "today":
        return anchor.date().isoformat()

    if text == "next week":
        return (anchor + timedelta(days=7)).date().isoformat()

    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    for name, idx in weekday_map.items():
        if name in text:
            days_ahead = (idx - anchor.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = anchor + timedelta(days=days_ahead)
            return target.date().isoformat()

    return due_date
