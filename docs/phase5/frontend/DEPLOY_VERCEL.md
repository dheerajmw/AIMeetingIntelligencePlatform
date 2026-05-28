# Deploy MeetIQ frontend on Vercel

Vercel hosts the **Phase 5 React (Vite) UI** only. The **FastAPI backend** (Whisper, SQLite, uploads) must run elsewhere — Oracle free VM, Render, Railway, or your laptop + tunnel.

| Deploy on Vercel | Do **not** deploy on Vercel |
|------------------|-------------------------------|
| `docs/phase5/frontend` | `docs/phase5/backend` (needs long-running Python + GPU/RAM) |

---

## 1. Push to GitHub

Repo: [dheerajmw/AIMeetingIntelligencePlatform](https://github.com/dheerajmw/AIMeetingIntelligencePlatform)

---

## 2. Import project

1. [vercel.com/new](https://vercel.com/new) → **Import** your GitHub repo.
2. Configure the project:

   | Setting | Value |
   |---------|--------|
   | **Root Directory** | `docs/phase5/frontend` (recommended) |
   | **Framework Preset** | Vite (auto-detected) |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |
   | **Install Command** | `npm ci` |

   **Alternative:** leave Root Directory empty and use the repo-root `vercel.json` (builds from `docs/phase5/frontend` automatically).

3. **Environment variables** (Production + Preview):

   | Name | Value |
   |------|--------|
   | `VITE_API_BASE` | Your backend URL, e.g. `https://meetiq-api.onrender.com` or Railway URL **with no trailing slash** |

4. Click **Deploy**.

Your app will be at `https://your-project.vercel.app`.

---

## 3. Allow the Vercel origin on the backend

On the API host (Render / Railway / VM), set:

```bash
CORS_ORIGINS=https://your-project.vercel.app,https://your-project-*.vercel.app
```

Or list each preview URL you use. The backend already allows `localhost` for local dev.

Redeploy the backend after changing `CORS_ORIGINS`.

---

## 4. Verify

1. Open `https://your-project.vercel.app`
2. Sign in (dev login if `DEV_AUTH_ENABLED=true` on backend): `admin@example.com`, workspace `default`
3. Upload a short meeting and confirm processing works

If the UI loads but API calls fail, check the browser **Network** tab (CORS or wrong `VITE_API_BASE`).

---

## Local vs Vercel env

| File | Used by |
|------|---------|
| `.env.local` | `npm run dev` locally |
| Vercel dashboard `VITE_API_BASE` | Production & preview builds |

Vite only exposes variables prefixed with `VITE_`.

---

## Custom domain (optional)

Vercel → **Settings → Domains** → add your domain → update `CORS_ORIGINS` on the backend to include it.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| UI shows login but API 404 / failed fetch | `VITE_API_BASE` wrong or backend down |
| CORS error | Add exact Vercel URL to backend `CORS_ORIGINS` |
| Old API URL after change | Redeploy Vercel (env vars are baked in at **build** time) |
| Build fails on `tsc` | Run `npm run build` locally; fix TypeScript errors |

---

## Backend hosting (free-friendly)

See [../backend/DEPLOY_RAILWAY.md](../backend/DEPLOY_RAILWAY.md), [../backend/DEPLOY_RENDER.md](../backend/DEPLOY_RENDER.md), or run the API locally and use [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) for demos.
