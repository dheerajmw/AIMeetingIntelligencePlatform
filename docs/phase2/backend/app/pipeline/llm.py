from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Optional

from groq import Groq

from .dates import anchor_relative_due_date
from .schemas import ActionItem, Decision, MeetingInsights, TimestampRange
from .utils import chunk_text_by_chars, extract_first_json_object, now_utc


@dataclass(frozen=True)
class LlmConfig:
    model: str
    temperature: float = 0.2
    max_output_tokens: int = 1600
    prompt_version: str = "v2"
    chunk_max_chars: int = 12000


def _pass1_system_prompt() -> str:
    return (
        "You extract candidate meeting outcomes WITH evidence.\n"
        "Return ONLY valid JSON (no markdown, no prose).\n"
        "Rules:\n"
        "- Do not fabricate owners, due dates, or evidence.\n"
        "- If owner/due_date/evidence is missing, use exactly: \"Not identified\".\n"
        "- evidence_quote must be a short verbatim quote from the transcript chunk.\n"
        "- timestamp_range must match the transcript timestamps when possible.\n"
        "- confidence is 0.0-1.0 based on how explicit the item is.\n"
        "- Use speaker labels in transcript (e.g. speaker_1) to infer owners when someone says \"I'll do it\".\n"
        "\n"
        "JSON schema:\n"
        "{\n"
        "  \"executive_summary\": string,\n"
        "  \"key_discussion_points\": string[],\n"
        "  \"decisions_made\": {\n"
        "    \"decision\": string,\n"
        "    \"owner\": string,\n"
        "    \"due_date\": string,\n"
        "    \"evidence_quote\": string,\n"
        "    \"timestamp_range\": {\"start_s\": number, \"end_s\": number} | null,\n"
        "    \"confidence\": number\n"
        "  }[],\n"
        "  \"action_items\": {\n"
        "    \"title\": string,\n"
        "    \"description\": string,\n"
        "    \"owner\": string,\n"
        "    \"due_date\": string,\n"
        "    \"priority\": string,\n"
        "    \"evidence_quote\": string,\n"
        "    \"timestamp_range\": {\"start_s\": number, \"end_s\": number} | null,\n"
        "    \"confidence\": number\n"
        "  }[]\n"
        "}\n"
    )


def _pass2_system_prompt() -> str:
    return (
        "You merge partial meeting extractions into ONE final JSON.\n"
        "Return ONLY valid JSON matching the same schema as pass 1.\n"
        "Rules:\n"
        "- Deduplicate repeated items.\n"
        "- If later chunks contradict earlier decisions, keep the final decision.\n"
        "- Do not fabricate owners/due_dates/evidence; use \"Not identified\".\n"
        "- Preserve the best evidence_quote and timestamp_range for each item.\n"
        "- Anchor relative due dates (Friday/tomorrow/EOD/next week) to meeting start + timezone when provided.\n"
        "- priority must be one of: high, medium, low, or \"Not identified\".\n"
    )


def _build_user_prompt(
    transcript_text: str,
    meeting_title: Optional[str],
    meeting_start_iso: Optional[str],
    timezone_name: Optional[str],
) -> str:
    header = []
    if meeting_title:
        header.append(f"Meeting title: {meeting_title}")
    if meeting_start_iso:
        header.append(f"Meeting start: {meeting_start_iso}")
    if timezone_name:
        header.append(f"Timezone: {timezone_name}")
    header_txt = ("\n".join(header) + "\n\n") if header else ""
    return header_txt + "Transcript:\n" + transcript_text.strip()


def _segments_to_text(segments: Iterable[object]) -> str:
    lines: list[str] = []
    for s in segments:
        start_s = float(getattr(s, "start_s"))
        end_s = float(getattr(s, "end_s"))
        text = str(getattr(s, "text")).strip()
        speaker_id = getattr(s, "speaker_id", None)
        if not text:
            continue
        prefix = f"{speaker_id} " if speaker_id else ""
        lines.append(f"[{start_s:0.2f}-{end_s:0.2f}] {prefix}{text}")
    return "\n".join(lines).strip()


def _call_groq_json(client: Groq, cfg: LlmConfig, system_prompt: str, user_prompt: str) -> dict:
    completion = client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=cfg.temperature,
        max_tokens=cfg.max_output_tokens,
    )
    content = completion.choices[0].message.content or ""
    json_str = extract_first_json_object(content)
    return json.loads(json_str)


def _parse_timestamp_range(raw: object) -> Optional[TimestampRange]:
    if not isinstance(raw, dict):
        return None
    try:
        return TimestampRange(start_s=float(raw["start_s"]), end_s=float(raw["end_s"]))
    except (KeyError, TypeError, ValueError):
        return None


def _normalize_decisions(raw_items: list, meeting_start_iso: Optional[str], timezone_name: Optional[str]) -> list[Decision]:
    out: list[Decision] = []
    for item in raw_items or []:
        if not isinstance(item, dict):
            continue
        due = anchor_relative_due_date(
            str(item.get("due_date") or "Not identified"),
            meeting_start_iso,
            timezone_name,
        )
        out.append(
            Decision(
                decision=str(item.get("decision") or "").strip(),
                owner=str(item.get("owner") or "Not identified"),
                due_date=due,
                evidence_quote=str(item.get("evidence_quote") or "Not identified"),
                timestamp_range=_parse_timestamp_range(item.get("timestamp_range")),
                confidence=float(item["confidence"]) if item.get("confidence") is not None else None,
            )
        )
    return [d for d in out if d.decision]


def _normalize_actions(raw_items: list, meeting_start_iso: Optional[str], timezone_name: Optional[str]) -> list[ActionItem]:
    out: list[ActionItem] = []
    for item in raw_items or []:
        if not isinstance(item, dict):
            continue
        due = anchor_relative_due_date(
            str(item.get("due_date") or "Not identified"),
            meeting_start_iso,
            timezone_name,
        )
        title = str(item.get("title") or item.get("action") or "").strip()
        out.append(
            ActionItem(
                title=title,
                description=str(item.get("description") or "").strip(),
                owner=str(item.get("owner") or "Not identified"),
                due_date=due,
                priority=str(item.get("priority") or "Not identified"),
                evidence_quote=str(item.get("evidence_quote") or "Not identified"),
                timestamp_range=_parse_timestamp_range(item.get("timestamp_range")),
                confidence=float(item["confidence"]) if item.get("confidence") is not None else None,
            )
        )
    return [a for a in out if a.title]


def generate_insights_from_segments(
    segments: list[object],
    meeting_title: Optional[str],
    meeting_start_iso: Optional[str],
    timezone_name: Optional[str],
    cfg: LlmConfig,
) -> MeetingInsights:
    client = Groq()
    transcript_text = _segments_to_text(segments)
    chunks = chunk_text_by_chars(transcript_text, max_chars=cfg.chunk_max_chars)
    if not chunks:
        raise ValueError("Transcript is empty; cannot generate insights.")

    # Pass 1: per-chunk extraction with evidence
    partials: list[dict] = []
    for idx, ch in enumerate(chunks):
        user_prompt = _build_user_prompt(ch, meeting_title, meeting_start_iso, timezone_name)
        out = _call_groq_json(client, cfg, _pass1_system_prompt(), user_prompt)
        out["_chunk_index"] = idx
        partials.append(out)

    # Pass 2: merge + conflict resolution + relative date anchoring
    merge_prompt = (
        "Merge the following partial extractions into ONE final JSON.\n"
        f"Meeting start: {meeting_start_iso or 'Not provided'}\n"
        f"Timezone: {timezone_name or 'Not provided'}\n\n"
        "Partials JSON:\n"
        + json.dumps(partials, ensure_ascii=False)
    )
    merged = _call_groq_json(client, cfg, _pass2_system_prompt(), merge_prompt)

    return MeetingInsights(
        llm_model=cfg.model,
        generated_at=now_utc(),
        executive_summary=(merged.get("executive_summary") or "").strip() or "Not identified",
        key_discussion_points=merged.get("key_discussion_points") or [],
        decisions_made=_normalize_decisions(merged.get("decisions_made"), meeting_start_iso, timezone_name),
        action_items=_normalize_actions(merged.get("action_items"), meeting_start_iso, timezone_name),
    )
