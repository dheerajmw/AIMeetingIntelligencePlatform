## MeetIQ — Edge Cases & Failure Scenarios

This document lists detailed edge cases derived from:
- `docs/problemStatement.md` (MVP outputs and user needs)
- `docs/phaseWiseArchitecture.md` (phase-wise system design)

Use this as a build checklist, QA matrix, and backlog for robustness work.

---

## 1) Ingestion (upload) edge cases

### File type and container issues

- **Unsupported extension**: user uploads `.aac`, `.flac`, `.ogg`, `.mov` when only `.mp3/.wav/.m4a` are advertised.
- **Extension mismatch**: file named `.mp3` but is actually AAC/MP4 container; decoder fails.
- **Corrupt file**: truncated upload, broken headers, invalid duration metadata.
- **Encrypted/protected media**: DRM-protected recordings cannot be decoded.
- **Multi-track video**: video contains multiple audio tracks; wrong track selected (e.g., commentary track).
- **Variable sample rate**: causes drift between timestamps and audio playback.

### Size, duration, and bandwidth

- **Very large file**: exceeds max upload size, request timeout, or storage limits.
- **Very long meeting**: hours-long audio causes queue/worker timeouts and huge transcripts.
- **Slow network**: upload stalls; resumable uploads needed.
- **Duplicate uploads**: same file uploaded multiple times; create duplicate meetings unintentionally.
- **Partial upload**: client disconnects mid-upload but backend still creates a job record.

### Security and abuse

- **Malicious filenames/metadata**: path traversal attempts, weird unicode normalization, extremely long names.
- **Abusive content**: user uploads non-meeting audio (music, podcasts) causing misleading outputs.
- **Rate limiting**: repeated large uploads by same user/tenant causes resource exhaustion.

### User experience expectations

- **Wrong meeting selected**: user uploads the wrong recording and expects deletion/retry.
- **User closes tab**: upload completes but user never sees results; needs “recent meetings” list.

---

## 2) Pre-processing edge cases (audio extraction, normalization, chunking)

### Audio extraction failures

- **No audio track**: video with no audio stream.
- **Stereo/mono assumptions**: downmix causes loss (e.g., one speaker only on left channel).
- **Clipping and distortion**: normalization increases noise, reduces STT quality.

### Content characteristics

- **Very low volume**: quiet participants or distant microphone.
- **High background noise**: fan noise, street noise, keyboard noise.
- **Cross-talk / overlaps**: multiple speakers talking simultaneously.
- **Non-speech segments**: long silence, hold music, screen-share audio.
- **Multiple languages**: code-switching mid-meeting.
- **Strong accents**: STT accuracy drops.

### Chunking and timestamp integrity

- **Chunk boundary cuts words**: degrades STT around boundaries; causes duplicated/missing words.
- **Clock drift**: timestamps shift after re-encoding.
- **Reordered segments**: parallel processing merges chunks out of order.
- **Overlapping chunk windows**: duplicates transcript lines if not deduped.

---

## 3) Transcription (Whisper/STT) edge cases

### Model and decoding behavior

- **Hallucinated words**: STT invents content in noisy or silent sections.
- **Punctuation issues**: missing punctuation changes meaning of “decisions” or action items.
- **Speaker ambiguity** (Phase 1): transcript has no speaker labels, making “owners” hard.
- **Numerals & dates**: “two” vs “2”, “May 5” vs “my five” confusion.
- **Domain vocabulary**: project names, acronyms, code terms misrecognized.
- **Named entities**: people names and company names corrupted.

### Time alignment

- **Inaccurate segment timestamps**: makes “evidence” timestamps unreliable later.
- **Long latency**: STT step dominates; job appears stuck without progress updates.

### Output formatting variance

- **Empty transcript**: STT outputs near-empty due to decoding failure or silence.
- **Huge transcript**: token limits for downstream LLM analysis.
- **Encoding problems**: unicode issues in transcript (smart quotes, special chars) break JSON parsing later.

---

## 4) Meeting intelligence (LLM analysis) edge cases

### Extraction correctness

- **No clear decisions**: meeting is exploratory; output should not fabricate decisions.
- **Conflicting decisions**: later reversal (“We decided X… actually let’s do Y”); platform must reflect final state.
- **Ambiguous action items**: “we should look into it” without owner/date; must be captured as “unassigned/unscheduled”.
- **Implicit owners**: “I’ll do it” without name; needs speaker context (Phase 2+).
- **Multiple owners**: action item assigned to a team; represent as list or “team”.
- **Conditional actions**: “If vendor approves, then…”; capture conditions.
- **Dependencies**: action depends on another meeting/task; capture dependency notes.

### Deadlines and time references

- **Relative dates**: “by Friday”, “next week”, “EOD”, “tomorrow” depend on meeting date/timezone.
- **Timezones**: participants in different zones; “EOD” ambiguous.
- **Ranges**: “sometime between 10–12”; not a single due date.
- **Soft dates**: “ideally by…” should not be treated as firm.
- **Multiple dates**: discussion mentions several dates; correct mapping to the right task is hard.

### Evidence and provenance (especially Phase 2)

- **Wrong quote attribution**: evidence quote doesn’t actually support extracted decision.
- **Quote spans across chunks**: missing context in evidence.
- **Timestamp mismatch**: evidence timestamp points to wrong moment due to STT drift.

### Prompt / schema / parsing failures

- **JSON invalid**: trailing commas, unescaped quotes, or markdown fences around JSON.
- **Schema drift**: LLM changes field names (“ownerName” vs “owner”).
- **Overly verbose outputs**: huge summaries that swamp UI and storage.
- **Hallucinated owners/deadlines**: model guesses missing details; must require evidence or mark unknown.

### Safety, privacy, and compliance

- **PII leakage**: summaries may reveal personal info; need redaction rules or warnings.
- **Sensitive content**: passwords, API keys spoken aloud; should be detected/redacted.

---

## 5) Storage and data model edge cases

### Consistency and idempotency

- **Job retried**: same meeting processed twice; avoid duplicate transcript/output rows.
- **Partial writes**: transcript stored but analysis failed; meeting stuck in inconsistent state.
- **Out-of-order completion**: analysis finishes before transcript write finalizes (race conditions).

### Versioning and reproducibility

- **Model/prompt updates**: reprocessing yields different outputs; keep version fields:
  - STT model/version, LLM model, prompt version, extraction schema version
- **Regeneration**: user requests “regenerate summary”; should not overwrite without history.

### Data integrity

- **Dangling blobs**: DB references object storage keys that were deleted/expired.
- **Corrupt JSON**: structured output stored as text but not validated; later UI breaks.

---

## 6) UI and API edge cases (MVP)

### Status and progress

- **Stuck status**: worker crashed; UI shows “processing” forever.
- **No incremental updates**: long STT jobs need progress indicators (duration processed / queued position).

### Rendering

- **Very long outputs**: summaries or transcript pages become slow; need pagination/collapsing.
- **Missing fields**: owners/deadlines absent; UI must gracefully show “Not identified”.
- **Empty meeting intelligence**: display “No decisions detected” instead of blank.

### Sharing and access

- **Unauthorized access**: user guesses meeting ID and accesses other user’s outputs.
- **Link sharing**: shared link should respect permissions and expiry.

---

## 7) Phase-wise edge cases (beyond MVP)

### Phase 2 — Speaker diarization & better extraction

- **Diarization errors**: speaker segments swapped; “owner” assignments become incorrect.
- **Same speaker, different mic**: diarization splits one person into multiple speakers.
- **Two people with similar voices**: diarization merges them into one speaker.
- **Overlapping speech**: diarization assigns overlap incorrectly, causing attribution errors.
- **Speaker-to-name mapping**: calendar participant list doesn’t match diarization speakers (missing attendees, guest phones).

### Phase 3 — Search, knowledge, and integrations

#### Search

- **Index lag**: meeting outputs ready but not searchable yet.
- **Stale index**: regenerated summary not reflected in search results.
- **PII in search**: sensitive text indexed; requires filtering/redaction strategy.

#### Integrations

- **Duplicate ticket creation**: retries create duplicate Jira/Linear issues.
- **Rate limits**: integration API throttling delays exports.
- **Auth expiry**: OAuth token expired; export fails mid-run.
- **Field mapping mismatch**: “due date” format not accepted by target tool.
- **Permission mismatch**: user lacks rights in the external tool; export fails.

### Phase 4 — Real-time / in-meeting intelligence

- **Out-of-order audio chunks**: network jitter reorders chunks; transcript becomes scrambled.
- **Partial context**: rolling summary changes meaning as new info arrives; must show “draft” state.
- **Corrections**: later chunks correct earlier transcript; downstream summaries need updating.
- **Latency vs cost trade-off**: too frequent updates increases cost and noise.
- **Disconnect/reconnect**: meeting stream resumes; avoid duplicated chunks.

### Phase 5 — Enterprise readiness

- **Tenant isolation bugs**: cross-tenant data access via search or storage key collisions.
- **Retention policy conflicts**: legal hold vs user delete request.
- **Audit log gaps**: missing logs for sensitive operations (download, share, delete).
- **Encryption key rotation**: old artifacts become unreadable if not handled correctly.
- **Regional data residency**: recordings must remain in a specific region.

---

## 8) Concrete “expected behavior” rules (recommended)

These rules help prevent the most damaging failures (fabrication and ambiguity).

- **No fabrication**: if a decision/owner/deadline is not supported, output should be “Not identified” and (optionally) a short note.
- **Evidence-first (Phase 2+)**: decisions/action items should include a supporting quote + timestamp range when possible.
- **Relative dates must be anchored**: interpret “Friday/tomorrow/EOD” relative to meeting start time and stored timezone.
- **Idempotent processing**: safe retries should not create duplicate meetings or duplicate external tasks.

