## Phase 3 — Search & Integrations

This implements **Phase 3** from:
- `docs/phaseWiseArchitecture.md`
- `docs/implementationPlan.md`

Built on Phase 2 with:

- **Full-text search** (SQLite FTS5) across title, transcript, summary, decisions, and action items
- **Semantic search** (lightweight cosine similarity over indexed documents)
- **Integrations** with idempotent exports:
  - Jira / Linear / Trello → action items
  - Slack / Email → meeting summary
- **Auto-indexing** when a meeting reaches `READY`

---

## New API endpoints

- `GET /search?q=...&mode=keyword|semantic`
- `POST /search/reindex` — rebuild index for all READY meetings
- `POST /meetings/{id}/integrations/export`
- `GET /meetings/{id}/integrations/exports`

---

## Run (local)

### Backend

```bash
cd docs/phase3/backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

export GROQ_API_KEY="YOUR_KEY"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd docs/phase3/frontend
npm install
npm run dev
```

---

## Integration configuration (environment variables)

### Jira (action items)

```bash
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="..."
export JIRA_PROJECT_KEY="PROJ"
```

### Linear (action items)

```bash
export LINEAR_API_KEY="..."
export LINEAR_TEAM_ID="..."
```

### Trello (action items)

```bash
export TRELLO_API_KEY="..."
export TRELLO_TOKEN="..."
export TRELLO_LIST_ID="..."
```

### Slack (summary)

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### Email (summary)

```bash
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="587"
export SMTP_USER="..."
export SMTP_PASSWORD="..."
export SMTP_FROM="meetings@example.com"
export SMTP_TO="team@example.com"
```

---

## Idempotency

Exports use an idempotency key:

`{meeting_id}:{provider}:{export_kind}`

- Re-running the same export returns the previous successful record (unless `force: true`).
- Failed exports store actionable error messages in export history.

---

## Search notes

- **Keyword mode** uses SQLite FTS5 (`bm25` ranking).
- **Semantic mode** uses token cosine similarity (no external embedding API required).
- Meetings are indexed automatically after processing completes.
