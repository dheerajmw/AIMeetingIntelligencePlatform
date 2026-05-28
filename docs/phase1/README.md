## Phase 1 — MVP (Async Web App)

This implements **Phase 1** from:
- `docs/phaseWiseArchitecture.md`
- `docs/implementationPlan.md`

### What you get

- **Frontend (React)**: upload, meeting list, meeting details + status
- **Backend (FastAPI)**:
  - `POST /meetings` upload recording (multipart)
  - `GET /meetings` list meetings
  - `GET /meetings/{id}` meeting metadata + status
  - `GET /meetings/{id}/results` structured outputs (when ready)
- **Async processing**:
  - Uses **RQ + Redis** if available
  - Otherwise falls back to an **in-process background worker** (no extra services needed)
  - Transcription (Whisper local)
  - Analysis (Groq LLM: `llama-3.3-70b-versatile`)

---

## Prerequisites

- Python 3.9+
- Node 18+
- (Optional) Redis if you want a dedicated queue/worker
- (Optional) `ffmpeg` if you want to upload non-WAV formats (e.g. `.m4a`, `.mp3`)

---

## Run (local)

### 1) Backend API

```bash
cd docs/phase1/backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

export GROQ_API_KEY="YOUR_KEY"
uvicorn app.main:app --reload --port 8000
```

### 2) Worker (optional)

Only needed if you're using **Redis + RQ**.

```bash
cd docs/phase1/backend
source .venv/bin/activate
export GROQ_API_KEY="YOUR_KEY"
python3 -m app.worker
```

### 3) Frontend

```bash
cd docs/phase1/frontend
npm install
npm run dev
```

Open the frontend printed URL and upload an audio file (`.mp3/.wav/.m4a`).

### Notes about `ffmpeg`

- If `ffmpeg` is installed, you can upload `.mp3/.m4a/.mp4/.mov` as well.
- If `ffmpeg` is **not** installed, the backend still supports **`.wav`** uploads, but expects a **16 kHz mono WAV** for best results.

