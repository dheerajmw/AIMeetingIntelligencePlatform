from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable
from typing import Optional

from groq import Groq

from .schemas import MeetingInsights
from .utils import chunk_text_by_chars, extract_first_json_object, now_utc


@dataclass(frozen=True)
class LlmConfig:
    model: str
    temperature: float = 0.2
    max_output_tokens: int = 1200
    prompt_version: str = "v1"
    chunk_max_chars: int = 12000


def _build_system_prompt() -> str:
    return (
        "You extract structured meeting outcomes.\n"
        "Return ONLY valid JSON (no markdown, no prose).\n"
        "Rules:\n"
        "- Do not fabricate owners or deadlines.\n"
        "- If owner or deadline is not explicitly present, use exactly: \"Not identified\".\n"
        "- Keep items concise and action-oriented.\n"
        "\n"
        "JSON schema (keys must match exactly):\n"
        "{\n"
        "  \"executive_summary\": string,\n"
        "  \"key_discussion_points\": string[],\n"
        "  \"decisions_made\": {\"decision\": string, \"owner\": string, \"deadline\": string}[],\n"
        "  \"action_items\": {\"action\": string, \"owner\": string, \"deadline\": string}[]\n"
        "}\n"
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
        if not text:
            continue
        lines.append(f"[{start_s:0.2f}-{end_s:0.2f}] {text}")
    return "\n".join(lines).strip()


def _call_groq_json(client: Groq, cfg: LlmConfig, user_prompt: str) -> dict:
    completion = client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ],
        temperature=cfg.temperature,
        max_tokens=cfg.max_output_tokens,
    )
    content = completion.choices[0].message.content or ""
    json_str = extract_first_json_object(content)
    return json.loads(json_str)


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

    partials: list[dict] = []
    for idx, ch in enumerate(chunks):
        user_prompt = _build_user_prompt(ch, meeting_title, meeting_start_iso, timezone_name)
        out = _call_groq_json(client, cfg, user_prompt)
        out["_chunk_index"] = idx
        partials.append(out)

    merge_prompt = (
        "Merge the following partial extractions into ONE final JSON.\n"
        "Return ONLY valid JSON matching the schema.\n"
        "Rules:\n"
        "- Deduplicate repeated items.\n"
        "- If a later chunk contradicts an earlier decision, keep the final decision.\n"
        "- Do not fabricate owners or deadlines; use \"Not identified\".\n\n"
        "Partials JSON:\n"
        + json.dumps(partials, ensure_ascii=False)
    )
    merged = _call_groq_json(client, cfg, merge_prompt)

    return MeetingInsights(
        llm_model=cfg.model,
        generated_at=now_utc(),
        executive_summary=(merged.get("executive_summary") or "").strip() or "Not identified",
        key_discussion_points=merged.get("key_discussion_points") or [],
        decisions_made=merged.get("decisions_made") or [],
        action_items=merged.get("action_items") or [],
    )

