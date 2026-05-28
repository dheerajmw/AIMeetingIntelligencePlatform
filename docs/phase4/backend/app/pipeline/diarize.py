from __future__ import annotations

from .schemas import TranscriptSegment


def label_speakers_by_pauses(
    segments: list[TranscriptSegment],
    pause_threshold_s: float = 1.5,
    max_speakers: int = 6,
) -> list[TranscriptSegment]:
    """
    Lightweight optional diarization: assign speaker labels when pauses suggest
    a turn change. This is a heuristic baseline (Phase 2) — not true voice diarization.
    """
    if not segments:
        return segments

    ordered = sorted(segments, key=lambda s: s.start_s)
    speaker_idx = 1
    labeled: list[TranscriptSegment] = []

    for i, seg in enumerate(ordered):
        if i > 0:
            gap = seg.start_s - ordered[i - 1].end_s
            if gap >= pause_threshold_s:
                speaker_idx = (speaker_idx % max_speakers) + 1

        labeled.append(
            TranscriptSegment(
                start_s=seg.start_s,
                end_s=seg.end_s,
                text=seg.text,
                speaker_id=f"speaker_{speaker_idx}",
            )
        )

    return labeled
