from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def cosine_similarity(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    q = Counter(query_tokens)
    d = Counter(doc_tokens)
    dot = sum(q[t] * d.get(t, 0) for t in q)
    q_norm = math.sqrt(sum(v * v for v in q.values()))
    d_norm = math.sqrt(sum(v * v for v in d.values()))
    if q_norm == 0 or d_norm == 0:
        return 0.0
    return dot / (q_norm * d_norm)


@dataclass(frozen=True)
class SemanticHit:
    meeting_id: int
    score: float
    snippet: str


def rank_semantic(query: str, documents: list[tuple[int, str]], limit: int = 20) -> list[SemanticHit]:
    q_tokens = tokenize(query)
    hits: list[SemanticHit] = []
    for meeting_id, text in documents:
        tokens = tokenize(text)
        score = cosine_similarity(q_tokens, tokens)
        if score <= 0:
            continue
        snippet = text[:240].strip()
        if len(text) > 240:
            snippet += "…"
        hits.append(SemanticHit(meeting_id=meeting_id, score=score, snippet=snippet))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]
