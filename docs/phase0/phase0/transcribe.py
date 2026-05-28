from __future__ import annotations

from pathlib import Path

import whisper

from .schemas import TranscriptSegment


def transcribe_with_whisper(
    input_path: Path,
    model_name: str = "base",
    language: str | None = None,
) -> tuple[list[TranscriptSegment], dict]:
    """
    Returns (segments, raw_info).
    `segments` are timestamped transcript segments.
    """
    model = whisper.load_model(model_name)

    result = model.transcribe(
        str(input_path),
        language=language,
        verbose=False,
    )

    segments: list[TranscriptSegment] = []
    for seg in result.get("segments", []) or []:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                start_s=float(seg.get("start", 0.0)),
                end_s=float(seg.get("end", 0.0)),
                text=text,
            )
        )

    return segments, {"language": result.get("language"), "text": result.get("text", "")}

