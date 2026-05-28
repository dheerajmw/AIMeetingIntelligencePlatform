## Phase 0 — Local prototype

This folder implements **Phase 0** from:
- `docs/phaseWiseArchitecture.md`
- `docs/implementationPlan.md`

It runs locally on a single machine:

1. **Whisper (local)** → timestamped transcript
2. **Groq LLM** → structured meeting outputs (validated JSON)
3. **Markdown report** + saved artifacts

---

## Setup

Create a virtual environment (recommended) and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Set your Groq API key:

```bash
export GROQ_API_KEY="YOUR_KEY"
```

---

## Run

### End-to-end (STT + LLM)

```bash
python3 -m phase0.run \
  --input "/path/to/meeting.m4a" \
  --meeting-title "Sprint planning" \
  --meeting-start "2026-05-27T10:00:00+05:30" \
  --timezone "Asia/Kolkata"
```

### Transcription only (no LLM call)

```bash
python3 -m phase0.run --input "/path/to/meeting.m4a" --skip-llm
```

---

## Outputs

Each run writes a folder under `docs/phase0/outputs/<run_id>/`:

- `metadata.json` (input + configuration)
- `transcript.json` (Whisper segments with timestamps)
- `insights.json` (validated structured output)
- `report.md` (human-readable report)

