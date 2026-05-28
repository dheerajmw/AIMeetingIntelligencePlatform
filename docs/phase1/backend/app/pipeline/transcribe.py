from __future__ import annotations

from pathlib import Path
import shutil
from typing import Optional

import whisper
import numpy as np
import soundfile as sf

from .schemas import TranscriptSegment


def transcribe_with_whisper(
    input_path: Path,
    model_name: str = "base",
    language: Optional[str] = None,
) -> tuple[list[TranscriptSegment], dict]:
    model = whisper.load_model(model_name)

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None and input_path.suffix.lower() == ".wav":
        audio, sr = sf.read(str(input_path), dtype="float32", always_2d=False)
        if isinstance(audio, np.ndarray) and audio.ndim > 1:
            audio = np.mean(audio, axis=1).astype("float32")
        if int(sr) != 16000:
            raise RuntimeError(
                f"ffmpeg not found and WAV sample rate is {sr}. "
                "Either install ffmpeg or provide a 16 kHz mono WAV."
            )
        result = model.transcribe(audio, language=language, verbose=False)
    else:
        if ffmpeg is None:
            raise RuntimeError("ffmpeg not found. Install ffmpeg or upload a 16 kHz mono WAV.")
        result = model.transcribe(str(input_path), language=language, verbose=False)

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

