from __future__ import annotations

import base64
import io
import os
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def decode_audio_payload(data_base64: str, fmt: str, sample_rate: int = 16000) -> tuple[Path, float]:
    """
    Decode incoming chunk bytes into a WAV file path for Whisper.
    Returns (wav_path, duration_seconds).
    """
    raw = base64.b64decode(data_base64)

    if fmt == "wav":
        buf = io.BytesIO(raw)
        audio, sr = sf.read(buf, dtype="float32", always_2d=False)
        if isinstance(audio, np.ndarray) and audio.ndim > 1:
            audio = np.mean(audio, axis=1).astype("float32")
        duration = len(audio) / float(sr)
        return _write_wav(audio, sr), duration

    if fmt in {"pcm_s16le", "pcm"}:
        pcm = np.frombuffer(raw, dtype=np.int16).astype("float32") / 32768.0
        duration = len(pcm) / float(sample_rate)
        return _write_wav(pcm, sample_rate), duration

    raise ValueError(f"Unsupported live audio format: {fmt}")


def _write_wav(audio: np.ndarray, sr: int) -> Path:
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, audio, sr, subtype="PCM_16")
    return Path(path)
