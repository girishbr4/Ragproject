# Deployment Plan: HDFC Fund FAQ Assistant

> **Frontend:** Vercel (Next.js 14)
> **Backend:** Railway (FastAPI + Python RAG pipeline)
> **Status:** Production Deployment Guide

---

## Architecture Overview

The system uses a two-tier cloud deployment:

- **Vercel** hosts the Next.js 14 frontend (CDN-delivered, serverless API routes)
- **Railway** hosts the FastAPI backend (Python RAG pipeline + ChromaDB + BGE model)

```
Browser
  |
  v  HTTPS
Vercel  (Next.js 14 - frontend/ dir)
  |  /api/chat proxy via serverless function
  v  HTTPS to Railway URL
Railway  (FastAPI - ui/api.py)
  |
  +-- vector_store/chroma_db/   (committed to git)
  +-- BAAI/bge-small-en-v1.5    (cached after first boot)
  +-- Groq API                  (GROQ_API_KEY env var)
```

---

## Pre-Deployment Checklist

- [ ] `ingest_all.py` run successfully -- `vector_store/chroma_db/` populated
- [ ] `python -m pytest tests/` passes locally
- [ ] `uvicorn ui.api:app --port 8000` starts without errors
- [ ] `cd frontend && npm run build` succeeds (no TypeScript errors)
- [ ] `.env` and `.env.local` are NOT committed to git
- [ ] `vector_store/chroma_db/` is NOT in `.gitignore` (needed by Railway)

---

## Part 1 — Backend on Railway

### 1.1 New Files Required at Project Root

#### `Procfile`
```
web: uvicorn ui.api:app --host 0.0.0.0 --port $PORT
```

> Railway injects `$PORT` automatically. Never hardcode `8000`.

#### `railway.json`
```json
{
  "build": { "builder": "NIXPACKS" },
  "deploy": {
    "startCommand": "uvicorn ui.api:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

### 1.2 File Modifications Required

#### `requirements.txt` — add FastAPI + Uvicorn
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
```
Append these two lines to the existing `requirements.txt`.

#### `ui/api.py` — update CORS for production

Replace the hardcoded `allow_origins` with an env-var-aware list so the Vercel
URL is automatically included once `FRONTEND_URL` is set in Railway:

```python
import os

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]
vercel_url = os.getenv("FRONTEND_URL")
if vercel_url:
    ALLOWED_ORIGINS.append(vercel_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

### 1.3 ChromaDB Persistence on Railway

> **IMPORTANT:** Railway's filesystem is ephemeral and resets on every redeploy.
> The pre-built `vector_store/chroma_db/` **must be committed to git**.

For this project (~5-15 MB for 5 schemes), committing to git is the simplest approach:

```bash
# Remove any gitignore rule that excludes chroma_db
git add -f vector_store/chroma_db/
git commit -m "Add pre-built ChromaDB vector store for Railway"
```

*Alternative (Railway Volume):* Create a volume at `/app/vector_store/chroma_db` in the
Railway dashboard and SSH in to run `python ingest_all.py` after first deploy.

### 1.4 BGE Model Caching

`BAAI/bge-small-en-v1.5` (~33 MB) is downloaded from HuggingFace on first import.
Set these Railway env vars to control the cache location:

```
HF_HOME=/app/.cache/huggingface
SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers
```

First cold start takes ~20–40 s for model download. Subsequent starts use the cache.

### 1.5 Railway Environment Variables

Set in Railway dashboard → your service → **Variables**:

| Variable | Value | Notes |
|---|---|---|
| `GROQ_API_KEY` | `gsk_...` | From https://console.groq.com |
| `FRONTEND_URL` | `https://<app>.vercel.app` | Set **after** Vercel deploy |
| `HF_HOME` | `/app/.cache/huggingface` | HuggingFace cache |
| `SENTENCE_TRANSFORMERS_HOME` | `/app/.cache/sentence_transformers` | ST cache |
| `PYTHON_VERSION` | `3.11` | Match your local Python |
| `PORT` | *(auto-set by Railway)* | Do not override |

### 1.6 Deploy to Railway

**Option A — Railway CLI:**
```bash
npm install -g @railway/cli
railway login

# From project root (g:/Ragchatbot)
railway init        # new project
# OR: railway link  # link to existing dashboard project

railway up          # deploy
railway logs        # tail logs
railway domain      # -> https://<svc>.railway.app
```

**Option B — GitHub integration (recommended):**
1. Railway dashboard → **New Project** → Deploy from GitHub repo
2. Select `Ragchatbot` → Railway auto-detects `Procfile`
3. Set environment variables in dashboard
4. Every push to `main` triggers automatic redeploy

### 1.7 Verify Backend

```bash
curl https://<your-service>.railway.app/health
# -> {"status":"ok","service":"HDFC Fund FAQ API"}

curl -X POST https://<your-service>.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the expense ratio of HDFC Mid Cap Fund?"}'
# -> {"response":"The expense ratio of HDFC Mid Cap Fund is..."}
```

---

## Part 2 — Frontend on Vercel

### 2.1 File Modifications Required

#### `frontend/src/app/api/chat/route.ts` — use `BACKEND_URL` env var

Replace the hardcoded `localhost` URL so it points to Railway in production:

```typescript
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const backendUrl =
    process.env.BACKEND_URL || "http://localhost:8000/api/chat";

  const response = await fetch(backendUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return NextResponse.json(
      { response: "Service unavailable. Please try again later." },
      { status: 502 }
    );
  }

  const data = await response.json();
  return NextResponse.json(data);
}
```

#### `frontend/next.config.js` — remove localhost rewrite, simplify

The existing `rewrites()` block that points to `localhost:8000` is replaced by
the `BACKEND_URL` env var inside the API route. The config simplifies to:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
    ],
  },
};

module.exports = nextConfig;
```

### 2.2 Vercel Environment Variables

Set in Vercel dashboard → **Settings → Environment Variables**:

| Variable | Value | Environment |
|---|---|---|
| `BACKEND_URL` | `https://<svc>.railway.app/api/chat` | Production, Preview |

> **Do NOT** set `BACKEND_URL` in `frontend/.env.local` for production.
> `.env.local` is local dev only — it is not read by Vercel's build.

### 2.3 Vercel Project Settings

| Setting | Value |
|---|---|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Node.js Version | 20.x |

> **CRITICAL:** Root Directory must be `frontend`. The repo root contains Python
> backend code — Vercel must be pointed at the Next.js subfolder.

### 2.4 Deploy to Vercel

**Option A — Vercel CLI:**
```bash
npm install -g vercel
cd g:/Ragchatbot/frontend
vercel

# Follow prompts (Next.js auto-detected)
vercel env add BACKEND_URL
# -> https://<your-service>.railway.app/api/chat  [Production, Preview]

vercel --prod
```

**Option B — Vercel Dashboard (recommended for first deploy):**
1. Go to https://vercel.com/new
2. Import your GitHub repo
3. Set **Root Directory**: `frontend`
4. Add env var: `BACKEND_URL` = `https://<svc>.railway.app/api/chat`
5. Click **Deploy**

### 2.5 Verify Frontend

1. Open `https://<your-app>.vercel.app` — Lumina Finance dark UI loads
2. Type: *"What is the expense ratio of HDFC Mid Cap Fund?"*
3. Answer returns from Railway via the Next.js proxy
4. Source citation and disclaimer footer render correctly

---

## Part 3 — Deployment Order

> **Deploy Railway FIRST.** Vercel needs the Railway URL to configure `BACKEND_URL`.

```
Step 1   Create Procfile + railway.json at project root
Step 2   Update requirements.txt, ui/api.py (CORS), route.ts, next.config.js
Step 3   git add && git commit && git push
Step 4   Deploy Railway  ->  note https://<svc>.railway.app
Step 5   Verify: curl https://<svc>.railway.app/health -> 200 OK
Step 6   Deploy Vercel   ->  set BACKEND_URL=https://<svc>.railway.app/api/chat
Step 7   Note Vercel URL ->  set FRONTEND_URL=https://<app>.vercel.app on Railway
Step 8   Redeploy Railway (CORS now includes the Vercel domain)
Step 9   Test end-to-end from browser at Vercel URL
```

---

## Part 4 — Environment Variable Reference

### Railway (Backend)
```
GROQ_API_KEY=gsk_...
FRONTEND_URL=https://<your-app>.vercel.app
HF_HOME=/app/.cache/huggingface
SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers
PYTHON_VERSION=3.11
```

### Vercel (Frontend — dashboard only, not in .env.local)
```
BACKEND_URL=https://<your-service>.railway.app/api/chat
```

### Local Dev (no changes required)
```
# g:/Ragchatbot/.env
GROQ_API_KEY=gsk_...

# g:/Ragchatbot/frontend/.env.local
BACKEND_URL=http://localhost:8000/api/chat
```

---

## Part 5 — Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Railway build fails: `No module named fastapi` | `fastapi`/`uvicorn` not in `requirements.txt` | Add `fastapi>=0.111.0` and `uvicorn[standard]>=0.29.0` |
| Cold start timeout (>30 s) | BGE model downloading on first boot | Set `HF_HOME` env var; cached after first boot |
| Vercel build: `Module not found` | TypeScript / import path error | Run `npm run build` locally and fix errors first |
| CORS error in browser | `FRONTEND_URL` not set on Railway | Set it in Railway dashboard and redeploy |
| 502 from Vercel API route | Railway down or `BACKEND_URL` wrong | Check Railway logs; URL must end in `/api/chat` |
| ChromaDB empty on Railway | `chroma_db/` excluded by `.gitignore` | `git add -f vector_store/chroma_db/` and push |
| `$PORT` binding error | Hardcoded `--port 8000` in Procfile | Use `--port $PORT` in start command |

---

## Part 6 — Cost Estimates

| Service | Tier | Monthly Cost |
|---|---|---|
| Vercel | Hobby (free) | $0 |
| Railway | Trial → Starter | $0 trial credit, ~$5 after |
| Groq API | Free tier | $0 (1K req/day, 200K tokens/day) |
| HuggingFace | Free model download | $0 |
| **Total** | | **~$0–5/month** |

> Railway Starter (512 MB RAM, 1 vCPU) is sufficient:
> BGE small model ~33 MB + ChromaDB + FastAPI runs comfortably within 512 MB.

---

## Part 7 — CI/CD (Optional, Post-MVP)

Once both services are connected to GitHub, deployments are fully automatic:

| Git Event | Action |
|---|---|
| Push to `main` | Vercel auto-builds and deploys frontend |
| Push to `main` | Railway auto-builds and deploys backend |
| PR opened | Vercel creates a preview deployment at a unique URL |

To enable Railway auto-deploy:
Railway dashboard → Service → **Settings → Source** → Connect GitHub repo

---

## Final Checklist

### Backend (Railway)
- [ ] `Procfile` at project root (uses `$PORT`)
- [ ] `railway.json` at project root
- [ ] `fastapi` + `uvicorn[standard]` in `requirements.txt`
- [ ] `ui/api.py` CORS reads `FRONTEND_URL` from env
- [ ] `vector_store/chroma_db/` committed to git (not in `.gitignore`)
- [ ] All env vars set in Railway dashboard
- [ ] `/health` returns `{"status":"ok"}` from Railway URL

### Frontend (Vercel)
- [ ] `route.ts` uses `BACKEND_URL` env var (no hardcoded localhost)
- [ ] `next.config.js` has no localhost rewrites
- [ ] `BACKEND_URL` set in **Vercel dashboard** (not in `.env.local`)
- [ ] **Root Directory** set to `frontend` in Vercel project settings
- [ ] Vercel build succeeds and UI loads

### End-to-End
- [ ] Chat query from Vercel URL returns answer (no CORS errors in console)
- [ ] Source citation and "Last updated" footer render in bot responses
- [ ] "Facts-only. No investment advice." disclaimer visible

---

> **Disclaimer:** Facts-only. No investment advice.
