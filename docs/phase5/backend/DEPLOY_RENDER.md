# Deploy MeetIQ backend on Render

This guide deploys the **Phase 5 FastAPI** backend (`docs/phase5/backend`) as a Docker web service on [Render](https://render.com).

## What you get

| File | Purpose |
|------|---------|
| `Dockerfile` | Python 3.11, ffmpeg, CPU PyTorch, Whisper, uvicorn |
| `render.yaml` | Optional Blueprint (web service + 1 GB disk) |
| `scripts/start.sh` | Binds `0.0.0.0:$PORT`, creates storage dirs |
| `deploy/storage/` | Sample manifest (WAV files are not in git; upload your own) |

Health check: `GET /health`

---

## Before you deploy (important)

### 1. Memory (Whisper)

Local **Whisper** loads PyTorch and often needs **2 GB+ RAM**. Render’s **free** tier (512 MB) usually **OOMs** on transcription.

- Use **Starter** ($7/mo) or higher with at least **2 GB RAM**.
- Set `WHISPER_MODEL=tiny` (default in `render.yaml`) to reduce memory.
- Prefer **short WAV uploads** (16 kHz mono) for first tests.

### 2. Persistent data

SQLite and uploaded files must live on a **persistent disk**, not the container filesystem (ephemeral on redeploy).

`render.yaml` mounts a 1 GB disk at `/var/data` and sets:

- `STORAGE_ROOT=/var/data/storage`
- `DATABASE_URL=sqlite:////var/data/app.db`

**Disks require a paid plan** on Render. Without a disk, the API runs but **meetings are lost** on every deploy.

### 3. Redis (optional)

Background jobs fall back to an **in-process thread pool** if Redis is unavailable. You do **not** need Redis for a first deploy.

### 4. Frontend CORS

After you deploy the React app (Vercel, Cloudflare Pages, etc.), set:

```bash
CORS_ORIGINS=https://your-frontend.example.com
```

Comma-separate multiple origins. Local dev origins (`localhost:5173–5175`) are always allowed.

---

## Option A — Deploy with Blueprint (`render.yaml`)

1. Push this repo to GitHub.
2. In Render: **New → Blueprint**.
3. Connect the repo.
4. Set **Root Directory** to: `docs/phase5/backend`
5. Render reads `render.yaml`. Confirm the **meetiq-api** service.
6. Add secrets in the Blueprint flow or dashboard:
   - `GROQ_API_KEY` (required)
   - `CORS_ORIGINS` (your frontend URL)
   - SMTP vars if you use real email (`INTEGRATIONS_STUB_MODE=false`)
7. **Create resources** and wait for the Docker build (15–25 min first time is normal).

API URL: `https://meetiq-api.onrender.com` (name may vary).

---

## Option B — Manual Web Service (dashboard)

1. **New → Web Service** → connect repo.
2. **Root Directory**: `docs/phase5/backend`
3. **Environment**: Docker
4. **Dockerfile path**: `./Dockerfile`
5. **Health check path**: `/health`
6. **Instance type**: Starter (2 GB RAM recommended)
7. **Disk** (paid): mount `/var/data`, 1 GB+
8. **Environment variables**:

| Variable | Example | Notes |
|----------|---------|--------|
| `GROQ_API_KEY` | `gsk_...` | Required for insights |
| `JWT_SECRET` | long random string | Use “Generate” in Render |
| `WHISPER_MODEL` | `tiny` | `base` needs more RAM |
| `STORAGE_ROOT` | `/var/data/storage` | With persistent disk |
| `DATABASE_URL` | `sqlite:////var/data/app.db` | With persistent disk |
| `CORS_ORIGINS` | `https://app.example.com` | Your frontend origin |
| `DEV_AUTH_ENABLED` | `true` | Dev login; set `false` for production SSO |
| `INTEGRATIONS_STUB_MODE` | `false` | Real email when SMTP is set |
| `SMTP_HOST` | `smtp.gmail.com` | Gmail App Password |
| `SMTP_PORT` | `587` | |
| `SMTP_USER` | your@gmail.com | |
| `SMTP_PASSWORD` | app password | |
| `SMTP_FROM` | your@gmail.com | |

Render sets `PORT` automatically; do not hardcode it.

9. **Create Web Service** and wait for deploy.

Verify:

```bash
curl https://YOUR-SERVICE.onrender.com/health
```

---

## Connect the frontend

In `docs/phase5/frontend`, create production env:

```bash
# .env.production
VITE_API_BASE=https://YOUR-SERVICE.onrender.com
```

Build and deploy the static site:

```bash
cd docs/phase5/frontend
npm ci
npm run build
# deploy dist/ to Vercel, Cloudflare Pages, Netlify, etc.
```

Sign in with dev login (`admin@example.com` / workspace `default`) if `DEV_AUTH_ENABLED=true`.

---

## Email on Render

1. `INTEGRATIONS_STUB_MODE=false`
2. Set SMTP variables (see table above).
3. In the UI, use **Integrations → Email** on a processed meeting; optional recipient field (admins can send to another address).

Default recipient is the signed-in user’s email.

---

## Local Docker smoke test

```bash
cd docs/phase5/backend
docker build -t meetiq-api .
docker run --rm -p 8002:8002 \
  -e PORT=8002 \
  -e GROQ_API_KEY=your_key \
  meetiq-api
curl http://127.0.0.1:8002/health
```

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| Build timeout | Large PyTorch/Whisper install; retry or use Render’s longer build timeout |
| Worker OOM / crash on upload | Instance too small; use `WHISPER_MODEL=tiny` or larger plan |
| CORS error in browser | Missing `CORS_ORIGINS` with exact frontend URL (scheme + host) |
| Data gone after redeploy | No persistent disk or wrong `STORAGE_ROOT` / `DATABASE_URL` |
| `ffmpeg not found` | Should not happen in Docker; image installs ffmpeg |
| Cold start slow | Free/starter spin down after idle; first request wakes the service |

---

## Production hardening (later)

- `DEV_AUTH_ENABLED=false` and OIDC (`OIDC_*` env vars)
- Managed **PostgreSQL** instead of SQLite (`DATABASE_URL`)
- Object storage (S3/R2) instead of local `STORAGE_ROOT`
- Separate **Redis** + worker service for long jobs
- Do not commit `.env`; set secrets only in Render
