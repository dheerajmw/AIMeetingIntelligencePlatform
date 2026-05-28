from __future__ import annotations

import json
from typing import Optional

from groq import Groq

from ...config import settings
from ...pipeline.utils import extract_first_json_object, now_utc


def rolling_draft_insights(
    transcript_text: str,
    meeting_title: Optional[str],
    previous_draft: Optional[dict],
) -> dict:
    """
    Lightweight rolling summary for live meetings. Output is explicitly marked draft.
    """
    client = Groq()
    prev_summary = (previous_draft or {}).get("executive_summary", "")

    system = (
        "You update a LIVE meeting draft summary.\n"
        "Return ONLY valid JSON with keys:\n"
        "executive_summary, key_discussion_points, decisions_made, action_items\n"
        "Rules:\n"
        "- Mark uncertainty; do not fabricate owners/deadlines.\n"
        "- Use Not identified when missing.\n"
        "- decisions_made items: decision, owner, due_date, evidence_quote\n"
        "- action_items: title, description, owner, due_date, priority, evidence_quote\n"
    )
    user = (
        f"Meeting title: {meeting_title or 'Live meeting'}\n"
        f"Previous draft summary: {prev_summary or 'None'}\n\n"
        f"Transcript so far:\n{transcript_text[-settings.live_max_draft_transcript_chars:]}\n"
    )

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=900,
    )
    content = completion.choices[0].message.content or ""
    parsed = json.loads(extract_first_json_object(content))
    parsed["is_draft"] = True
    parsed["generated_at"] = now_utc().isoformat()
    parsed["llm_model"] = settings.groq_model
    return parsed
