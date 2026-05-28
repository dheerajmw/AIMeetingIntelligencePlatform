## MeetIQ — Phase-wise Architecture

This document proposes a phased architecture aligned to the problem statement in `docs/problemStatement.md`. Each phase is a deployable step that expands capabilities without requiring major rewrites.

---

## Common concepts (used across phases)

### Core pipeline stages

- **Ingestion**: upload audio/video, validate format, generate a job
- **Pre-processing**: extract audio from video, normalize, chunk
- **Transcription (STT)**: generate timestamped transcript (Whisper)
- **Meeting intelligence (LLM)**: summary, key points, decisions, action items, owners, deadlines
- **Storage**: artifacts + metadata + searchable text
- **Presentation**: UI/API to view, search, export, and share outputs

### Primary artifacts

- **Recording**: raw uploaded file + extracted audio
- **Transcript**: timestamped segments (optionally speaker-tagged in later phases)
- **Structured outputs**: JSON for summary/decisions/actions + a readable report

---

## Phase 0 — Local prototype (single machine)

### Goal

Prove end-to-end value: recording → transcript → structured meeting outputs.

### Components

- **CLI script / notebook**
  - Accepts a local file path
  - Runs Whisper locally to produce transcript
  - Sends transcript to LLM (Groq) with a fixed prompt to produce structured JSON
  - Generates a markdown report
- **Local storage**
  - Folder-based storage for: uploads, transcripts, outputs

### Data flow

1. User provides file path
2. Pre-process (optional chunking)
3. Whisper → transcript (timestamps)
4. LLM → meeting intelligence JSON + markdown report
5. Save outputs locally

### Exit criteria

- Produces outputs matching the MVP list for at least 5–10 sample recordings (AMI/ICSI/QMSum samples acceptable).

---

## Phase 1 — MVP (asynchronous web app)

### Goal

Ship the MVP as a web app where users can upload a recording and receive structured outputs.

### High-level architecture

- **Frontend**
  - Upload UI, meeting list, meeting details page
  - Shows status: uploaded → transcribing → analyzing → ready
- **Backend API**
  - Auth-lite (optional), upload endpoints, job status, results retrieval
  - Generates signed upload URLs (recommended)
- **Object storage**
  - Stores raw recordings and derived audio (e.g., S3-compatible)
- **Job queue + worker**
  - Background processing for long-running STT/LLM steps
  - Retries + dead-letter handling
- **Database**
  - Meeting metadata, job state, pointers to blobs, structured outputs
- **Observability**
  - Central logs per job, basic metrics, error reporting

### Suggested module boundaries

- **Ingestion Service**
  - Validates file, extracts audio, stores to object storage
  - Creates a `MeetingJob` record and enqueues work
- **Transcription Worker**
  - Downloads audio, runs Whisper (local container or hosted)
  - Produces timestamped transcript segments
- **Analysis Worker**
  - Calls LLM (Groq) to generate:
    - executive summary
    - key points
    - decisions
    - action items
    - owners (if identifiable)
    - deadlines (if mentioned)
  - Validates output schema and stores normalized results
- **Results API**
  - Returns structured JSON + a human-readable report view

### Data flow

1. User uploads recording → stored in object storage
2. Backend creates meeting/job record → enqueues transcription
3. Transcription worker produces transcript → stored in DB (and optionally in object storage)
4. Analysis worker produces structured outputs → stored in DB
5. UI fetches results and renders report

### Exit criteria

- Works reliably for multi-minute recordings
- Job status is visible
- Outputs are consistent and stored in a queryable form

---

## Phase 2 — Quality upgrades (speaker + better extraction)

### Goal

Increase accuracy and usefulness, especially for “owners” and clarity of decisions.

### Additions

- **Speaker diarization (optional)**
  - Add a diarization step before/alongside STT
  - Produce speaker-labeled transcript segments: `speaker_1`, `speaker_2`, …
- **Entity and action normalization**
  - Normalize action items into a consistent schema:
    - `title`, `description`, `owner`, `due_date`, `priority`, `source_quote`, `timestamp_range`
- **Confidence + provenance**
  - Store “evidence” fields (quotes/time ranges) for decisions/actions
  - Add simple confidence scores (heuristic or model-provided)
- **Prompting improvements**
  - Two-pass analysis:
    - Pass 1: extract candidate decisions/actions with evidence
    - Pass 2: deduplicate, merge, and format final output

### Architecture changes

- Insert a **Diarization Worker** between pre-processing and transcription, or use diarization output during analysis.
- Expand DB schema for speaker segments and evidence fields.

### Exit criteria

- Action items show **who/what/when** more consistently
- Report includes **evidence** (timestamps/quotes) for key outputs

---

## Phase 3 — Search, knowledge, and integrations

### Goal

Make meeting knowledge discoverable and actionable across tools.

### Additions

- **Full-text search**
  - Search across transcripts and extracted outputs
- **Semantic search (optional)**
  - Generate embeddings for transcripts/outputs
  - Enable “find meetings about X” and “similar meetings”
- **Integrations**
  - Export action items to Jira/Linear/Trello
  - Send summaries to Slack/Email
  - Calendar association (meeting title, participants, time window)

### Architecture changes

- Add **Search Index** (e.g., Postgres FTS / OpenSearch) and optionally a **Vector DB**
- Add **Integration Workers** with per-integration credentials and rate-limit handling

### Exit criteria

- Users can search across meetings and export action items with minimal friction

---

## Phase 4 — Real-time and “in-meeting” intelligence (optional)

### Goal

Provide near real-time notes and action-item capture during live meetings.

### Additions

- **Streaming ingestion**
  - Chunked audio ingestion during the meeting
- **Incremental transcription**
  - Streaming or periodic STT per chunk
- **Rolling summary**
  - Update key points/decisions/actions as the meeting progresses

### Architecture changes

- Add a **streaming gateway** (WebSocket/WebRTC ingestion)
- Worker model shifts from batch jobs to **incremental pipelines** with partial artifacts

---

## Phase 5 — Enterprise readiness

### Goal

Security, compliance, governance, and scale.

### Additions

- **AuthN/AuthZ**
  - SSO (SAML/OIDC), role-based access control, workspace isolation
- **Data governance**
  - Retention policies, deletion workflows, audit logs
- **Encryption**
  - At-rest and in-transit, key management, secret rotation
- **Scalability**
  - Horizontal worker autoscaling, per-tenant rate limits
- **Cost controls**
  - Caching, transcript reuse, chunk-level retries, token budgeting

---

## Deployment options (choose per phase)

- **Phase 0**: local only
- **Phase 1–2**: single cloud environment (API + workers + managed DB + object storage)
- **Phase 3+**: add search infrastructure and integration services

