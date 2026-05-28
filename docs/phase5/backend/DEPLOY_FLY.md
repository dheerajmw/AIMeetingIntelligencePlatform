# Deploy MeetIQ backend on Fly.io

Deploy the **Phase 5 FastAPI** API with Docker on [Fly.io](https://fly.io).

| File | Purpose |
|------|---------|
| `fly.toml` | App config, health check, 2 GB VM, volume mount |
| `Dockerfile` | Python 3.11, ffmpeg, Whisper (CPU) |

Frontend stays on **Vercel**; set `VITE_API_BASE` to your Fly URL.

---

## Before you start

| Requirement | Notes |
|-------------|--------|
| **Fly account** | https://fly.io/app/sign-up — card may be required |
| **flyctl** | CLI (install below) |
| **Groq API key** | For LLM (and optional future STT) |
| **RAM** | Whisper needs **~2 GB** — `fly.toml` requests `2gb` (may incur small monthly cost on Fly) |

Fly’s old “free 3 VMs” allowance changed; check https://fly.io/docs/about/pricing/ for current credits.

---

## 1. Install CLI and log in

**macOS:**

```bash
brew install flyctl
fly auth login
```

---

## 2. Pick a unique app name

App names are **global** on Fly. If `meetiq-api` is taken, edit `fly.toml`:

```toml
app = 'meetiq-api-yourname'
```

---

## 3. Create the app and volume

```bash
cd docs/phase5/backend
```

Create the app (without deploying yet):

```bash
fly apps create meetiq-api
```

Create a **persistent volume** in the same region as `primary_region` in `fly.toml` (`bom` = Mumbai):

```bash
fly volumes create meetiq_data --region bom --size 3
```

List volumes:

```bash
fly volumes list
```

---

## 4. Set secrets (required)

Do **not** commit `.env` to git.

```bash
fly secrets set \
  GROQ_API_KEY="gsk_your_key" \
  JWT_SECRET="your-long-random-secret" \
  CORS_ORIGINS="https://ai-meeting-intelligence-platform.vercel.app"
```

Optional email:

```bash
fly secrets set \
  SMTP_HOST="smtp.gmail.com" \
  SMTP_PORT="587" \
  SMTP_USER="you@gmail.com" \
  SMTP_PASSWORD="your-app-password" \
  SMTP_FROM="you@gmail.com"
```

View secrets (names only):

```bash
fly secrets list
```

---

## 5. Deploy

```bash
fly deploy
```

First build often takes **15–30 minutes** (PyTorch + Whisper).

Watch logs:

```bash
fly logs
```

---

## 6. Verify

```bash
fly status
curl https://meetiq-api.fly.dev/health
```

Replace `meetiq-api` with your app name from `fly.toml`.

Expected: `{"ok":true,"phase":5,...}`

Public URL format: `https://<app-name>.fly.dev`

---

## 7. Connect Vercel frontend

1. Vercel → **Environment Variables**
2. `VITE_API_BASE` = `https://meetiq-api.fly.dev` (your app URL, no trailing slash)
3. **Redeploy** frontend

Ensure `CORS_ORIGINS` on Fly includes your exact Vercel URL.

---

## Useful commands

| Task | Command |
|------|---------|
| SSH into machine | `fly ssh console` |
| Restart | `fly apps restart meetiq-api` |
| Scale memory | `fly scale memory 2048` |
| Open dashboard | `fly dashboard` |
| Destroy app | `fly apps destroy meetiq-api` |

---

## Change region

Edit `fly.toml` → `primary_region = 'sin'` (or `iad`, `lhr`, etc.), create a **new volume** in that region, redeploy.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Deploy fails: volume not found | `fly volumes create meetiq_data --region <primary_region> --size 3` |
| OOM / crash on upload | `fly scale memory 2048`; keep `WHISPER_MODEL=tiny` |
| Health check failing | Wait for first boot; `fly logs`; path is `/health` |
| CORS errors | `fly secrets set CORS_ORIGINS=https://your-app.vercel.app` |
| 502 on first request | `auto_start_machines` — cold start ~5–30s, retry |
| App name taken | Change `app` in `fly.toml` and recreate |

---

## Cost tips

- `min_machines_running = 0` + `auto_stop_machines` stops billing when idle (with cold starts).
- **2 GB** RAM is required for Whisper; smaller sizes will likely fail.
- Use short test files (`WHISPER_MODEL=tiny`) to limit CPU time.

---

## Related

- [DEPLOY_VERCEL.md](../frontend/DEPLOY_VERCEL.md) — frontend
- [DEPLOY_RENDER.md](./DEPLOY_RENDER.md) — alternative host
- [DEPLOY_ORACLE.md](./DEPLOY_ORACLE.md) — VM hosting
