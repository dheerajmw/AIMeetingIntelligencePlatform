from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..config import settings


def samples_dir() -> Path:
    p = settings.storage_root / "samples"
    p.mkdir(parents=True, exist_ok=True)
    return p


def manifest_path() -> Path:
    return samples_dir() / "manifest.json"


def load_manifest() -> dict[str, Any]:
    path = manifest_path()
    if not path.exists():
        return {"samples": []}
    return json.loads(path.read_text(encoding="utf-8"))


def get_sample(sample_id: str) -> dict[str, Any] | None:
    for item in load_manifest().get("samples", []):
        if item.get("id") == sample_id:
            return item
    return None


def sample_file_path(sample: dict[str, Any]) -> Path:
    return samples_dir() / sample["filename"]


def ensure_sample_file(sample: dict[str, Any]) -> Path:
    path = sample_file_path(sample)
    if path.exists():
        return path

    if sample.get("id") == "icsi-bed-60s":
        _prepare_icsi_demo_clip(path)

    if path.exists():
        return path
    raise FileNotFoundError(
        f"Sample file missing: {path.name}. Run: python3 scripts/prepare_samples.py"
    )


def _prepare_icsi_demo_clip(dest: Path) -> None:
    """Create a short clip for ICSI demo slot when official corpus file is not bundled."""
    import soundfile as sf

    partial = samples_dir() / "EN2002a.Mix-Headset.partial.wav"
    ami = samples_dir() / "ami-en2002a-60s.wav"
    src = partial if partial.exists() else ami
    if not src.exists():
        return
    audio, sr = sf.read(str(src), dtype="float32", always_2d=False)
    if hasattr(audio, "ndim") and audio.ndim > 1:
        audio = audio.mean(axis=1)
    start = min(int(30 * sr), max(0, len(audio) - int(60 * sr)))
    clip = audio[start : start + int(60 * sr)]
    dest.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dest), clip, sr, subtype="PCM_16")
