from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .llm import DEFAULT_MODEL, LlmConfig, generate_meeting_insights
from .report import render_markdown_report
from .transcribe import transcribe_with_whisper
from .utils import ensure_dir, now_utc, safe_slug, write_json


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 0: Whisper → Groq → meeting report")
    p.add_argument("--input", required=True, help="Path to audio/video file")
    p.add_argument("--out-dir", default="outputs", help="Output directory (relative to phase0/)")

    p.add_argument("--whisper-model", default="base", help="Whisper model name (tiny/base/small/medium/large)")
    p.add_argument("--language", default=None, help="Optional language code (e.g., en)")

    p.add_argument("--llm-model", default=DEFAULT_MODEL, help="Groq model name")
    p.add_argument("--skip-llm", action="store_true", help="Only run transcription")
    p.add_argument("--chunk-max-chars", type=int, default=12000, help="Approx prompt size limit per chunk")

    p.add_argument("--meeting-title", default=None, help="Optional meeting title")
    p.add_argument("--meeting-start", default=None, help="Optional meeting start ISO8601")
    p.add_argument("--timezone", default=None, help="Optional timezone name (e.g., Asia/Kolkata)")

    return p.parse_args()


def main() -> int:
    load_dotenv()
    args = _parse_args()

    phase0_root = Path(__file__).resolve().parents[1]
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    run_id = f"{now_utc().strftime('%Y%m%dT%H%M%SZ')}_{safe_slug(args.meeting_title or input_path.stem)}"
    out_root = (phase0_root / args.out_dir / run_id).resolve()
    ensure_dir(out_root)

    metadata: dict[str, Any] = {
        "run_id": run_id,
        "created_at": now_utc().isoformat(),
        "input_path": str(input_path),
        "meeting_title": args.meeting_title,
        "meeting_start": args.meeting_start,
        "timezone": args.timezone,
        "whisper_model": args.whisper_model,
        "language": args.language,
        "llm_model": args.llm_model,
        "chunk_max_chars": args.chunk_max_chars,
    }
    write_json(out_root / "metadata.json", metadata)

    segments, stt_info = transcribe_with_whisper(
        input_path=input_path,
        model_name=args.whisper_model,
        language=args.language,
    )
    write_json(
        out_root / "transcript.json",
        {
            "stt": {"engine": "whisper", **stt_info, "model": args.whisper_model},
            "segments": [s.model_dump() for s in segments],
        },
    )

    if args.skip_llm:
        (out_root / "report.md").write_text(
            "## Meeting Report\n\nLLM step was skipped (`--skip-llm`).\n",
            encoding="utf-8",
        )
        return 0

    insights = generate_meeting_insights(
        transcript_segments=segments,
        meeting_title=args.meeting_title,
        meeting_start_iso=args.meeting_start,
        timezone_name=args.timezone,
        config=LlmConfig(model=args.llm_model),
        chunk_max_chars=args.chunk_max_chars,
    )
    write_json(out_root / "insights.json", insights.model_dump(mode="json"))

    report_md = render_markdown_report(
        insights=insights,
        meeting_title=args.meeting_title,
        meeting_start_iso=args.meeting_start,
        timezone_name=args.timezone,
    )
    (out_root / "report.md").write_text(report_md, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

