# Deploy MeetIQ backend on Oracle Cloud (Always Free)

Run the **Phase 5 FastAPI API** (Whisper + Groq + SQLite) on a free Ampere VM. Pair with **Vercel** for the frontend.

| Links |
|-------|
| [Sign up — Oracle Cloud Free](https://www.oracle.com/cloud/free/) |
| [Console](https://cloud.oracle.com/) |
| [Always Free docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm) |

---

## Architecture

```text
Browser → Vercel (React UI)
              ↓  VITE_API_BASE
         Oracle VM :8002 (Docker → meetiq-api)
              ↓
         /var/data (SQLite + uploads)
```

---

## Part 1 — Oracle account & VM

### 1. Create account

1. Open https://www.oracle.com/cloud/free/
2. Sign up (email + card for verification; **Always Free** resources stay $0 if you stay within limits).
3. Pick a **home region** close to you (cannot change later easily).

### 2. Create a compute instance

1. Console → **Compute** → **Instances** → **Create instance**.
2. **Name:** `meetiq-api`
3. **Image:** Ubuntu 22.04 or 24.04 (Always Free eligible).
4. **Shape:** click **Change shape** → **Ampere** → **VM.Standard.A1.Flex**
   - **OCPUs:** `2`
   - **Memory (GB):** `12` (fits Whisper `tiny` / `base`; stays within free pool)
5. **Networking:** use default VCN; assign a **public IPv4**.
6. **SSH keys:** download the private key or paste your Mac `~/.ssh/id_ed25519.pub`.
7. **Boot volume:** 50 GB default is fine.
8. Click **Create**.

Note the **public IP** (e.g. `129.213.x.x`).

### 3. Open firewall ports (required)

Oracle blocks traffic until you allow it in **two** places.

#### A) Security list (cloud firewall)

1. Instance details → **Subnet** link → **Security list** → **Add ingress rules**:

| Source CIDR | Protocol | Dest port | Description |
|-------------|----------|-----------|-------------|
| `0.0.0.0/0` | TCP | 22 | SSH |
| `0.0.0.0/0` | TCP | 8002 | MeetIQ API |

(For production, restrict SSH to your home IP.)

#### B) Ubuntu firewall on the VM (after SSH)

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8002 -j ACCEPT
sudo netfilter-persistent save
```

Or if `ufw` is active:

```bash
sudo ufw allow 22
sudo ufw allow 8002
sudo ufw enable
```

---

## Part 2 — Install Docker on the VM

SSH from your Mac:

```bash
chmod 600 ~/Downloads/ssh-key-*.key   # your downloaded key
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
```

On the VM:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and SSH back in so `docker` works without `sudo`.

---

## Part 3 — Deploy MeetIQ API

### 1. Clone the repo

```bash
git clone https://github.com/dheerajmw/AIMeetingIntelligencePlatform.git
cd AIMeetingIntelligencePlatform/docs/phase5/backend
```

### 2. Create production `.env`

```bash
cp .env.example .env
nano .env
```

Minimum values:

```bash
GROQ_API_KEY=gsk_your_key_here
JWT_SECRET=use-a-long-random-string-here
WHISPER_MODEL=tiny
DEV_AUTH_ENABLED=true
INTEGRATIONS_STUB_MODE=false

# Persistent data (Docker volume mounted at /var/data)
STORAGE_ROOT=/var/data/storage
DATABASE_URL=sqlite:////var/data/app.db

# Your Vercel URL (no trailing slash)
CORS_ORIGINS=https://ai-meeting-intelligence-platform.vercel.app

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=you@gmail.com
```

### 3. Build and run (Docker Compose — recommended)

```bash
docker compose -f docker-compose.oci.yml up -d --build
```

First build takes **15–30 minutes** (PyTorch + Whisper).

### 3b. Or run with plain Docker

```bash
docker build -t meetiq-api .
docker volume create meetiq-data
docker run -d \
  --name meetiq-api \
  --restart unless-stopped \
  -p 8002:8002 \
  --env-file .env \
  -v meetiq-data:/var/data \
  meetiq-api
```

### 4. Verify

On the VM:

```bash
curl http://127.0.0.1:8002/health
```

From your Mac:

```bash
curl http://YOUR_PUBLIC_IP:8002/health
```

Expected: `{"ok":true,"phase":5,...}`

Logs:

```bash
docker logs -f meetiq-api
```

---

## Part 4 — Connect Vercel frontend

1. **Vercel** → Project → **Settings** → **Environment Variables**
2. Set **`VITE_API_BASE`** = `http://YOUR_PUBLIC_IP:8002`  
   (Use `https://...` only after you add TLS in Part 5.)
3. **Redeploy** the frontend (env vars apply at build time).

4. Sign in at your Vercel URL: `admin@example.com`, workspace `default` (if `DEV_AUTH_ENABLED=true`).

---

## Part 5 — HTTPS (optional but recommended)

Browsers may block mixed content if Vercel is **https** and API is **http**. Options:

### Quick test

Temporarily use **http** on Vercel preview only, or test API from curl/Postman.

### Proper TLS with Caddy (on the VM)

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

sudo nano /etc/caddy/Caddyfile
```

If you have a domain `api.yourdomain.com` pointing to the VM IP:

```caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8002
}
```

```bash
sudo systemctl reload caddy
```

Open **port 443** in the Oracle security list. Then set:

- `VITE_API_BASE=https://api.yourdomain.com`
- `CORS_ORIGINS=https://your-app.vercel.app`

---

## Operations

| Task | Command |
|------|---------|
| Restart API | `docker compose -f docker-compose.oci.yml restart` |
| Update code | `git pull && docker compose -f docker-compose.oci.yml up -d --build` |
| Disk usage | `docker system df` / `df -h` |
| Stop | `docker compose -f docker-compose.oci.yml down` |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `curl` to public IP times out | Security list + `ufw` / `iptables`; instance must have public IP |
| Build OOM | Use `WHISPER_MODEL=tiny`; increase VM RAM in shape settings |
| CORS errors in browser | `CORS_ORIGINS` must exactly match Vercel URL (`https://...`) |
| Upload works once, data gone | Ensure volume mount `-v meetiq-data:/var/data` and env paths |
| Vercel still calls localhost | Redeploy Vercel after setting `VITE_API_BASE` |

---

## Cost

Stay within **Always Free** Ampere limits (4 OCPUs / 24 GB RAM total per tenancy). One `2 OCPU / 12 GB` VM for MeetIQ is typically enough.

Do not launch paid shapes or large block volumes unless you intend to pay.

---

## Related docs

- [DEPLOY_VERCEL.md](../frontend/DEPLOY_VERCEL.md) — frontend
- [DEPLOY_RENDER.md](./DEPLOY_RENDER.md) — alternative PaaS
- [DEPLOY_RAILWAY.md](./DEPLOY_RAILWAY.md) — alternative PaaS
