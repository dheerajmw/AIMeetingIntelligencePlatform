## MeetIQ — Implementation Plan

This plan is aligned to:
- `docs/problemStatement.md` (MVP inputs/outputs, target users, objective)
- `docs/phaseWiseArchitecture.md` (Phase 0 → Phase 5 architecture)

The goal is to deliver a usable MVP quickly (Phase 1), while keeping the system extensible for quality/search/real-time/enterprise phases.

---

## Guiding principles

- **Asynchronous by default**: transcription and analysis are long-running; always run in background jobs.
- **Schema-first outputs**: store LLM results as validated structured JSON (and render a report from it).
- **No fabrication**: when owners/deadlines/decisions aren’t supported, output “Not identified” rather than guessing.
- **Idempotent jobs**: retries should not duplicate meetings or downstream artifacts.
- **Version everything**: STT model version, LLM model, prompt version, schema version.

---

## Phase 0 — Local prototype (1–3 days)

### Deliverables

- A local script/notebook that:
  - Accepts a meeting recording file path
  - Produces a **timestamped transcript** (Whisper local)
  - Produces **structured meeting outputs** (Groq LLM):
    - executive summary, key points, decisions, action items, owners (if identified), deadlines (if mentioned)
  - Saves artifacts locally: transcript + JSON + markdown report

### Implementation steps

- **STT**
  - Run Whisper locally and output transcript segments with timestamps.
- **LLM extraction**
  - Create a single prompt that returns **strict JSON** matching a defined schema.
  - Add a JSON validation step (fail fast if invalid).
- **Report generation**
  - Convert JSON → markdown report for easy reading.

### Acceptance criteria

- Runs end-to-end on 5–10 sample recordings with consistent outputs.
- Produces “Not identified” for owners/deadlines when missing.

---

## Phase 1 — MVP (asynchronous web app) (1–2 weeks)

### MVP user flow

1. User uploads an audio recording (`.mp3/.wav/.m4a`) (video optional)
2. User sees job status: uploaded → transcribing → analyzing → ready
3. User views results:
   - executive summary
   - key discussion points
   - decisions made
   - action items (+ owners/deadlines if identified)

### Milestone 1: Project skeleton + basic API

- **Backend**
  - Endpoints:
    - `POST /meetings` (create meeting + upload instructions)
    - `GET /meetings/:id` (metadata + status)
    - `GET /meetings/:id/results` (structured outputs)
  - Meeting state machine:
    - `UPLOADED` → `TRANSCRIBING` → `ANALYZING` → `READY`
    - terminal failure states: `FAILED_TRANSCRIPTION`, `FAILED_ANALYSIS`
- **Database**
  - Tables (minimum):
    - `meetings` (id, title, created_at, status, input_blob_key, duration, error_message)
    - `transcripts` (meeting_id, segments_json, stt_model_version)
    - `analysis_results` (meeting_id, results_json, llm_model, prompt_version, schema_version)
- **Storage**
  - Store recordings (and extracted audio if video is supported).

### Milestone 2: Job queue + workers

- **Queue**
  - Enqueue a transcription job when upload completes.
  - Enqueue analysis job after transcription succeeds.
- **Transcription worker**
  - Downloads audio, runs Whisper, stores transcript segments.
  - Writes progress and updates meeting status.
- **Analysis worker**
  - Loads transcript, calls Groq, validates JSON, stores normalized results.
  - Updates meeting status to `READY`.
- **Retry policy**
  - Retries on transient errors (network/API timeouts).
  - No duplicate rows on retry (idempotency keys / unique constraints).

### Milestone 3: Frontend MVP

- **Pages**
  - Upload page
  - Meeting list page (recent meetings)
  - Meeting details page (status + results)
- **Rendering rules**
  - Missing owners/deadlines should render as “Not identified”.
  - If no decisions found, render “No decisions detected” (not empty).

### Milestone 4: Observability + guardrails

- **Logging**
  - Correlate logs by `meeting_id` and `job_id`.
- **Metrics**
  - Job durations (STT, LLM), failure rate, queue depth.
- **Guardrails**
  - Output validation (schema + max lengths).
  - Token budgeting / transcript chunking strategy for long meetings.

### Acceptance criteria (Phase 1)

- Upload + async processing completes for multi-minute recordings.
- Results persist in DB and can be reloaded later.
- Failures produce clear status + message and do not wedge the UI.

---

## Phase 2 — Quality upgrades (1–2 weeks, iterative)

### Goals (from architecture)

- Better owners and attributions (diarization optional)
- Evidence fields (quote + timestamp range) for key outputs
- More reliable extraction via 2-pass analysis

### Implementation steps

- **Transcript enhancements**
  - Add optional diarization step (or speaker labeling integration).
  - Store speaker-tagged segments when available.
- **Schema upgrades**
  - Add evidence fields:
    - decisions: `decision`, `evidence_quote`, `timestamp_range`
    - action items: `title`, `owner`, `due_date`, `evidence_quote`, `timestamp_range`
- **Two-pass LLM**
  - Pass 1: extract candidates with evidence
  - Pass 2: deduplicate, resolve conflicts, format final JSON
- **Relative date anchoring**
  - Store meeting start time + timezone, interpret “Friday/EOD/tomorrow”.

### Acceptance criteria (Phase 2)

- Action items more consistently include who/what/when.
- Evidence timestamps/quotes are present for most extracted items.

---

## Phase 3 — Search and integrations (1–3 weeks)

### Search

- **Full-text search**
  - Index transcripts + results for keyword search.
- **(Optional) semantic search**
  - Embeddings for “find similar meetings about X”.

### Integrations

- Export action items to external tools (e.g., Jira/Linear/Trello).
- Send summary to Slack/Email.
- Handle OAuth, rate limits, retries, and idempotency (avoid duplicate tickets).

### Acceptance criteria (Phase 3)

- Newly processed meetings become searchable quickly and reliably.
- Exports succeed or fail with actionable errors; retries do not duplicate tasks.

---

## Phase 4 — Real-time intelligence (optional, 2–4+ weeks)

### Goals

- Stream audio chunks during meeting
- Incremental transcript + rolling summary/actions

### Implementation steps

- Streaming ingestion (WebSocket/WebRTC gateway)
- Chunk sequencing and deduplication (handle reconnects)
- Draft vs final artifacts (rolling updates marked “Draft”)

### Acceptance criteria (Phase 4)

- Live meeting shows progressively improving transcript and draft summaries without scrambling or duplication.

---

## Phase 5 — Enterprise readiness (ongoing)

### Key workstreams

- SSO + RBAC + workspace isolation
- Retention policies + deletion workflows + audit logs
- Encryption (KMS), secret rotation, key rotation
- Multi-region / residency controls (if required)
- Cost controls (caching, reuse, per-tenant quotas)

---

## Recommended build order (practical)

- **Start with Phase 0** to validate prompts + schema.
- **Implement Phase 1** end-to-end (upload → queue → workers → results UI).
- **Add Phase 2 quality** (evidence + better action schema) before investing heavily in integrations.
- **Add Phase 3 search** once you have enough meetings to make search valuable.

