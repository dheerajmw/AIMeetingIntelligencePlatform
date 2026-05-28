from __future__ import annotations

from datetime import datetime

from .schemas import MeetingInsights


def render_markdown_report(
    insights: MeetingInsights,
    meeting_title: str | None,
    meeting_start_iso: str | None,
    timezone_name: str | None,
) -> str:
    header_bits: list[str] = []
    if meeting_title:
        header_bits.append(f"**Meeting**: {meeting_title}")
    if meeting_start_iso:
        header_bits.append(f"**Start**: {meeting_start_iso}")
    if timezone_name:
        header_bits.append(f"**Timezone**: {timezone_name}")
    header_bits.append(f"**Generated at**: {insights.generated_at.isoformat()}")
    header_bits.append(f"**Model**: {insights.llm_model}")

    lines: list[str] = []
    lines.append("## Meeting Report")
    lines.append("")
    lines.extend(header_bits)
    lines.append("")

    lines.append("### Executive summary")
    lines.append("")
    lines.append(insights.executive_summary.strip())
    lines.append("")

    lines.append("### Key discussion points")
    lines.append("")
    if insights.key_discussion_points:
        for p in insights.key_discussion_points:
            lines.append(f"- {p}")
    else:
        lines.append("- Not identified")
    lines.append("")

    lines.append("### Decisions made")
    lines.append("")
    if insights.decisions_made:
        for d in insights.decisions_made:
            lines.append(f"- **Decision**: {d.decision}")
            lines.append(f"  - **Owner**: {d.owner}")
            lines.append(f"  - **Deadline**: {d.deadline}")
    else:
        lines.append("- No decisions detected")
    lines.append("")

    lines.append("### Action items")
    lines.append("")
    if insights.action_items:
        for a in insights.action_items:
            lines.append(f"- **Action**: {a.action}")
            lines.append(f"  - **Owner**: {a.owner}")
            lines.append(f"  - **Deadline**: {a.deadline}")
    else:
        lines.append("- No action items detected")
    lines.append("")

    return "\n".join(lines).strip() + "\n"

