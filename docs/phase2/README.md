## Phase 2 — Quality Upgrades

This implements **Phase 2** from:
- `docs/phaseWiseArchitecture.md`
- `docs/implementationPlan.md`

Built on top of Phase 1 with:

- **Optional speaker labeling** (pause-based diarization heuristic)
- **Schema v2 outputs** with evidence quotes, timestamp ranges, and confidence
- **Two-pass LLM extraction** (chunk evidence extraction → merge/deduplicate/conflict resolve)
- **Relative date anchoring** for due dates like “Friday”, “tomorrow”, “EOD” (when meeting start + timezone are provided)

---

## What you get

- **Frontend (React)**: upload with diarization toggle, evidence-backed results, speaker-labeled transcript preview
- **Backend (FastAPI)**:
  - Same Phase 1 endpoints
  - `enable_diarization` upload form field
  - Insights schema version `v2`
- **Pipeline upgrades**:
  - Whisper transcript → optional speaker labels
  - Groq LLM two-pass analysis with provenance fields

---

## Run (local)

### 1) Backend API

```bash
cd docs/phase2/backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

export GROQ_API_KEY="YOUR_KEY"
uvicorn app.main:app --reload --port 8000
```

### 2) Worker (optional, Redis + RQ only)

```bash
cd docs/phase2/backend
source .venv/bin/activate
export GROQ_API_KEY="YOUR_KEY"
python3 -m app.worker
```

### 3) Frontend

```bash
cd docs/phase2/frontend
npm install
npm run dev
```

---

## Output schema (v2)

Decisions and action items include:

- `evidence_quote`
- `timestamp_range` (`start_s`, `end_s`)
- `confidence` (0–1)
- action items also include `title`, `description`, `priority`, `due_date`

If owner/due date/evidence is not supported by the transcript, values are `"Not identified"`.

---

## Notes

- Speaker labeling in Phase 2 uses a **pause-based heuristic** (not true voice diarization). It is useful for attribution experiments and can be replaced with a dedicated diarization model later.
- Provide **meeting start ISO + timezone** during upload for best due-date anchoring.
