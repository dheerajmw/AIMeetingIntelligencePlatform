from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from groq import Groq

from .schemas import MeetingInsights
from .utils import extract_first_json_object, now_utc


DEFAULT_MODEL = "llama-3.3-70b-versatile"


@dataclass(frozen=True)
class LlmConfig:
    model: str = DEFAULT_MODEL
    temperature: float = 0.2
    max_output_tokens: int = 1200
    prompt_version: str = "v1"


def _build_system_prompt() -> str:
    return (
        "You are an assistant that extracts structured meeting outcomes.\n"
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
    meeting_title: str | None,
    meeting_start_iso: str | None,
    timezone_name: str | None,
) -> str:
    header = []
    if meeting_title:
        header.append(f"Meeting title: {meeting_title}")
    if meeting_start_iso:
        header.append(f"Meeting start: {meeting_start_iso}")
    if timezone_name:
        header.append(f"Timezone: {timezone_name}")

    header_txt = ("\n".join(header) + "\n\n") if header else ""
    return (
        header_txt
        + "Transcript:\n"
        + transcript_text.strip()
    )


def _call_groq_json(client: Groq, config: LlmConfig, user_prompt: str) -> dict:
    completion = client.chat.completions.create(
        model=config.model,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": user_prompt},
        ],
        temperature=config.temperature,
        max_tokens=config.max_output_tokens,
    )

    content = completion.choices[0].message.content or ""
    json_str = extract_first_json_object(content)
    return json.loads(json_str)


def _segments_to_text(segments: Iterable[dict] | Iterable[object]) -> str:
    # segments are typically pydantic objects; stringify robustly
    lines: list[str] = []
    for s in segments:
        if hasattr(s, "start_s"):
            start_s = float(getattr(s, "start_s"))
            end_s = float(getattr(s, "end_s"))
            text = str(getattr(s, "text")).strip()
        else:
            start_s = float(s.get("start_s", 0))
            end_s = float(s.get("end_s", 0))
            text = str(s.get("text", "")).strip()
        if not text:
            continue
        lines.append(f"[{start_s:0.2f}-{end_s:0.2f}] {text}")
    return "\n".join(lines).strip()


def _chunk_text_by_chars(text: str, max_chars: int) -> list[str]:
    """
    Lightweight token-safe chunking using characters.
    Keeps chunks under roughly a safe token budget without external tokenizers.
    """
    text = text.strip()
    if not text:
        return []

    lines = text.splitlines()
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for line in lines:
        add = len(line) + 1
        if buf and size + add > max_chars:
            chunks.append("\n".join(buf).strip())
            buf = [line]
            size = len(line)
        else:
            buf.append(line)
            size += add

    if buf:
        chunks.append("\n".join(buf).strip())
    return chunks


def generate_meeting_insights(
    transcript_segments: list,
    meeting_title: str | None = None,
    meeting_start_iso: str | None = None,
    timezone_name: str | None = None,
    config: LlmConfig | None = None,
    chunk_max_chars: int = 12000,
) -> MeetingInsights:
    """
    Token-safe approach:
    - chunk transcript into smaller prompts
    - extract per-chunk decisions/actions
    - merge in a final pass
    """
    cfg = config or LlmConfig()
    client = Groq()

    transcript_text = _segments_to_text(transcript_segments)
    chunks = _chunk_text_by_chars(transcript_text, max_chars=chunk_max_chars)
    if not chunks:
        raise ValueError("Transcript is empty; cannot generate insights.")

    # Pass 1: per-chunk extraction
    partials: list[dict] = []
    for idx, ch in enumerate(chunks):
        user_prompt = _build_user_prompt(
            transcript_text=ch,
            meeting_title=meeting_title,
            meeting_start_iso=meeting_start_iso,
            timezone_name=timezone_name,
        )
        out = _call_groq_json(client, cfg, user_prompt)
        out["_chunk_index"] = idx
        partials.append(out)

    # Pass 2: merge (send only partial JSON, not full transcript)
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
        executive_summary=merged.get("executive_summary", "").strip() or "Not identified",
        key_discussion_points=merged.get("key_discussion_points") or [],
        decisions_made=merged.get("decisions_made") or [],
        action_items=merged.get("action_items") or [],
    )

