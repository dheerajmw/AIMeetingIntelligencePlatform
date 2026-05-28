#!/usr/bin/env python3
"""Prepare ICSI sample clip (60s) from AMI sample if ICSI file not present."""
from __future__ import annotations

import sys
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
SAMPLES = ROOT / "storage" / "samples"


def main() -> int:
    ami = SAMPLES / "ami-en2002a-60s.wav"
    icsi_out = SAMPLES / "icsi-bed-60s.wav"
    if icsi_out.exists():
        print(f"Already exists: {icsi_out}")
        return 0
    if not ami.exists():
        print(f"Missing AMI sample: {ami}", file=sys.stderr)
        return 1

    # Placeholder: trim a different 60s window from partial AMI file for demo diversity
    partial = SAMPLES / "EN2002a.Mix-Headset.partial.wav"
    src = partial if partial.exists() else ami
    audio, sr = sf.read(str(src), dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    start = min(int(30 * sr), max(0, len(audio) - int(60 * sr)))
    end = start + int(60 * sr)
    clip = audio[start:end]
    sf.write(str(icsi_out), clip, sr, subtype="PCM_16")
    print(f"Created ICSI demo clip: {icsi_out} ({len(clip)/sr:.1f}s)")
    print("Note: For production, replace with a real ICSI Bed meeting headset mix from the corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
