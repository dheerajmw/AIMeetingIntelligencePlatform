from __future__ import annotations

from typing import Any


def stub_action_item_refs(provider: str, action_items: list[dict[str, Any]]) -> list[str]:
    count = max(len(action_items), 1)
    return [f"STUB-{provider.upper()}-{i + 1}" for i in range(count)]


def stub_summary_ref(provider: str) -> str:
    return f"stub_{provider}_summary_sent"
