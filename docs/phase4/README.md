## Phase 4 — Real-time Intelligence

This implements **Phase 4** from:
- `docs/phaseWiseArchitecture.md`
- `docs/implementationPlan.md`

Built on Phase 3 with **live/in-meeting** capabilities:

- **WebSocket streaming gateway** for chunked audio ingestion
- **Incremental transcription** (Whisper per chunk, timestamp offsets)
- **Rolling draft summary** (Groq) during the meeting
- **Chunk sequencing + deduplication** (`seq`, `last_processed_seq`)
- **Finalize** → full two-pass analysis and **final** (non-draft) artifacts

---

## Live API

- `POST /live/sessions` — create live session
- `GET /live/sessions` — list sessions
- `GET /live/sessions/{id}` — session metadata
- `GET /live/sessions/{id}/results` — draft or final results
- `POST /live/sessions/{id}/finalize` — end meeting + final analysis
- `WS /live/sessions/{id}/stream` — stream audio chunks

### WebSocket chunk message

```json
{
  "type": "audio_chunk",
  "seq": 1,
  "format": "wav",
  "data_base64": "..."
}
```

Server replies with `ack` and `draft_update` messages.

On reconnect, client should resume from `last_processed_seq + 1` (server sends `session_state` on connect).

---

## Run (local)

### Backend

```bash
cd docs/phase4/backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

# copy or create .env with GROQ_API_KEY
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd docs/phase4/frontend
npm install
npm run dev
```

Open UI → **Live meeting** tab.

---

## Sample datasets on homepage (new users)

The **Batch upload** homepage includes one-click samples from:

| Corpus | Bundled clips | Purpose |
|--------|---------------|---------|
| **AMI Meeting Corpus** | 60s + ~100s EN2002a headset mix | STT + summary + action items |
| **ICSI Meeting Corpus** | 60s demo clip | Multi-speaker pipeline test |
| **QMSum** | Link only (text) | Summary benchmark (no audio) |

API:

- `GET /samples` — list samples + metadata
- `POST /samples/{sample_id}/process` — start processing a bundled clip

Prepare optional ICSI demo file:

```bash
cd docs/phase4/backend
python3 scripts/prepare_samples.py
```

### CLI simulation (no microphone)

Streams the AMI sample in 10s chunks:

```bash
cd docs/phase4/backend
source .venv/bin/activate
python3 run_live_simulation.py
```

Optional custom file:

```bash
python3 run_live_simulation.py ../storage/samples/ami-en2002a-60s.wav
```

---

## Draft vs final

| Stage | Transcript | Insights |
|------|------------|----------|
| During meeting (`ACTIVE`) | `draft_transcript_json` (`is_draft: true`) | rolling draft (`is_draft: true`) |
| After finalize (`READY`) | `final_transcript_json` | full Phase 2/3 analysis (`is_draft: false`) |

---

## Notes

- Live microphone streaming from browser works best with **WAV/PCM chunks**. The UI uses `MediaRecorder`; for production WebRTC/production codecs, install **ffmpeg** on the server or send PCM from the client.
- Rolling LLM frequency is controlled by `live_rolling_llm_every_n_chunks` in config (default: every 2 chunks).
