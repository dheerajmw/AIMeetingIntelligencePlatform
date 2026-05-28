from __future__ import annotations

import json
import re
from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def extract_first_json_object(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*({[\s\S]*?})\s*```", text, flags=re.IGNORECASE)
    if fenced:
        return fenced.group(1)

    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model output.")

    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError("Unbalanced JSON braces in model output.")


def chunk_text_by_chars(text: str, max_chars: int) -> list[str]:
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

