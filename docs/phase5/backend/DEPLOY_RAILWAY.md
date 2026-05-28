# Deploy MeetIQ backend on Railway

Deploy the **Phase 5 FastAPI** API using the existing `Dockerfile` on [Railway](https://railway.com).

| File | Purpose |
|------|---------|
| `/railway.toml` | Repo-root config (Docker path into `docs/phase5/backend`) |
| `railway.toml` (this folder) | Use when Railway **Root Directory** = `docs/phase5/backend` |
| `Dockerfile` | Python 3.11, ffmpeg, CPU PyTorch, Whisper |
| `scripts/start.sh` | Binds `0.0.0.0:$PORT` (Railway sets `PORT` automatically) |

Health check: `GET /health`

---

## Quick start (GitHub)

1. Push the repo to GitHub ([dheerajmw/AIMeetingIntelligencePlatform](https://github.com/dheerajmw/AIMeetingIntelligencePlatform)).
2. [Railway Dashboard](https://railway.com/new) → **Deploy from GitHub repo** → select the repo.
3. Railway creates a service. Open **Settings**:

   **Option A — deploy from repo root (simplest)**  
   - Leave **Root Directory** empty.  
   - Railway picks up `/railway.toml` and builds `docs/phase5/backend/Dockerfile`.

   **Option B — backend-only root**  
   - **Root Directory:** `docs/phase5/backend`  
   - **Config file path:** `docs/phase5/backend/railway.toml`

4. **Settings → Networking → Generate domain** (public URL).
5. **Variables** — add at minimum:

   | Variable | Example | Notes |
   |----------|---------|--------|
   | `GROQ_API_KEY` | `gsk_...` | Required |
   | `JWT_SECRET` | long random string | Required in production |
   | `WHISPER_MODEL` | `tiny` | Less RAM than `base` |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` | Frontend origin(s), comma-separated |
   | `DEV_AUTH_ENABLED` | `true` | Dev login; use `false` with OIDC later |
   | `INTEGRATIONS_STUB_MODE` | `false` | Real email when SMTP is set |

6. **Deploy** and wait for the Docker build (first build often 15–25 minutes).

Verify:

```bash
curl https://YOUR-SERVICE.up.railway.app/health
```

---

## Persistent storage (recommended)

Without a volume, SQLite and uploads are **lost on redeploy**.

1. Open your service → **Volumes** → **Add volume**.
2. Mount path: `/data` (Railway default).
3. Set variables:

   ```bash
   STORAGE_ROOT=/data/storage
   DATABASE_URL=sqlite:////data/app.db
   ```

4. Redeploy.

`scripts/start.sh` creates `/data/storage` when the volume is mounted.

---

## Memory (Whisper)

Local Whisper + PyTorch needs **~2 GB RAM** for reliable transcription.

- Set `WHISPER_MODEL=tiny`.
- In Railway, upgrade the service plan / resources if uploads OOM or the container restarts during processing.
- Prefer **short 16 kHz mono WAV** files for first tests.

---

## Email (optional)

```bash
INTEGRATIONS_STUB_MODE=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=you@gmail.com
```

---

## Connect the frontend

```bash
# docs/phase5/frontend/.env.production
VITE_API_BASE=https://YOUR-SERVICE.up.railway.app
```

Build and deploy `dist/` to Vercel, Cloudflare Pages, Netlify, etc.

---

## CLI deploy (optional)

```bash
npm i -g @railway/cli
railway login
cd docs/phase5/backend
railway link
railway up
```

Set variables with `railway variables set GROQ_API_KEY=...`.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build uses wrong directory | Use Option A or B above; confirm `builder = "DOCKERFILE"` in `railway.toml` |
| Health check fails | Wait for first deploy; path must be `/health`; increase `healthcheckTimeout` in `railway.toml` |
| CORS errors | Set `CORS_ORIGINS` to exact frontend URL (`https://...`) |
| OOM on upload | `WHISPER_MODEL=tiny`, more RAM, shorter audio |
| Data lost after deploy | Add a volume + `STORAGE_ROOT` / `DATABASE_URL` |

---

## Render vs Railway

This repo also includes [DEPLOY_RENDER.md](./DEPLOY_RENDER.md) and root `render.yaml`. Use one host for the API; env vars are the same.
