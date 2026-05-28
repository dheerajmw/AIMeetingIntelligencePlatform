## Phase 5 — Enterprise Readiness

Implements **Phase 5** from `docs/phaseWiseArchitecture.md` and `docs/implementationPlan.md`.

Built on Phase 4 with security, governance, and cost controls:

| Workstream | Implementation |
|------------|----------------|
| **AuthN / AuthZ** | JWT bearer tokens, dev login, OIDC callback stub, RBAC (`OWNER` / `ADMIN` / `MEMBER` / `VIEWER`) |
| **Workspace isolation** | All meetings, live sessions, search, samples, and exports scoped by `workspace_id` |
| **Audit logs** | Immutable audit trail for uploads, deletes, exports, auth, retention, settings |
| **Retention & deletion** | Per-workspace retention days, soft delete, admin purge job, hard delete |
| **Encryption at rest** | Optional Fernet encryption of upload files (`ENCRYPTION_KEY`) |
| **Cost controls** | Monthly meeting + LLM token quotas, transcript analysis cache reuse |
| **Data residency** | `data_region` per workspace (metadata; wire to storage in production) |

---

## Prerequisites

- **ffmpeg** — required for **video** uploads (`.mp4`, `.mov`, etc.) and most audio formats. Whisper uses it to decode media.

  ```bash
  # macOS
  brew install ffmpeg

  # Ubuntu / Debian
  sudo apt update && sudo apt install ffmpeg
  ```

  Without ffmpeg you can only process **16 kHz mono WAV** files directly.

---

## Deploy backend (Render)

See **[backend/DEPLOY_RENDER.md](./backend/DEPLOY_RENDER.md)** for Docker, `render.yaml`, env vars, persistent disk, and frontend `VITE_API_BASE`.

---

## Run (local)

### Backend

```bash
cd docs/phase5/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

### Frontend

```bash
cd docs/phase5/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5175
```

Open http://127.0.0.1:5175/ → **Dev sign in** with `admin@example.com`.

---

## Auth API

| Endpoint | Description |
|----------|-------------|
| `POST /auth/dev-login` | Local dev sign-in (`email`, `workspace_slug`) |
| `GET /auth/me` | Current user + workspace memberships |
| `GET /auth/oidc/start` | OIDC authorization URL (when configured) |
| `POST /auth/oidc/callback` | Exchange OIDC code for JWT |

All protected routes require `Authorization: Bearer <token>` unless `AUTH_DISABLED=true`.

Seeded users (default workspace):

- `admin@example.com` — **OWNER**
- `member@example.com` — **MEMBER**

---

## Admin API (ADMIN / OWNER)

| Endpoint | Description |
|----------|-------------|
| `GET /admin/workspace` | Workspace settings |
| `PATCH /admin/workspace` | Update retention, region, quotas |
| `GET /admin/usage` | Current month usage vs quotas |
| `GET /admin/audit-logs` | Recent audit events |
| `POST /admin/retention/purge` | Purge meetings past retention (`?dry_run=true`) |
| `DELETE /admin/meetings/{id}` | Hard delete meeting + files |

---

## Environment variables

See `backend/.env.example`. Key settings:

- `GROQ_API_KEY` — required for LLM analysis
- `JWT_SECRET` — sign session tokens (auto-generated if unset)
- `ENCRYPTION_KEY` — enable at-rest upload encryption
- `OIDC_*` — production SSO
- `AUTH_DISABLED=true` — bypass auth for local debugging only

---

## Notes

- **Analysis cache**: identical transcript hash within a workspace reuses stored insights (saves Groq tokens).
- **Quotas**: enforced on upload/sample processing and before LLM analysis.
- **Phase 4 features** retained: batch upload, search, integrations, live streaming, sample showcase.
- **Integrations**: By default `INTEGRATIONS_STUB_MODE=true` simulates exports without API keys. Set to `false` and configure Jira/Slack/etc. in `.env` for production.
- Sample WAV files symlink to `docs/phase4/storage/samples/`.
