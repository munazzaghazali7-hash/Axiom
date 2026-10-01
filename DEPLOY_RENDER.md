# Deploying Axiom on Render

This guide outlines how to deploy the entire Axiom platform (Next.js frontend, FastAPI backend, Celery worker, PostgreSQL, and Redis) to [Render](https://render.com).

---

## Architecture on Render

```
┌────────────────┐        ┌────────────────┐        ┌────────────────┐
│   axiom-web    │ ─────► │   axiom-api    │ ─────► │  axiom-worker  │
│ Next.js (Node) │        │ FastAPI (Py)   │        │  Celery (Py)   │
└────────────────┘        └──────┬──┬──────┘        └───────┬──┬─────┘
                                 │  │                       │  │
                                 │  └─────────┐   ┌─────────┘  │
                                 ▼            ▼   ▼            ▼
                          ┌──────────────┐ ┌──────────────┐
                          │ axiom-postgres│ │ axiom-redis  │
                          │ (PostgreSQL) │ │ (Key-Value)  │
                          └──────────────┘ └──────────────┘
```

---

## Method 1: Automatic Blueprint (Recommended)

Axiom includes a pre-configured `render.yaml` Blueprint file at the repository root.

### Steps:
1. **Fork or Push** this repository to your GitHub account:
   ```bash
   https://github.com/munazzaghazali7-hash/Axiom.git
   ```
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** in the top navigation bar and select **Blueprint**.
4. Connect your GitHub repository (`Axiom`).
5. Render will automatically detect `render.yaml` and display the resources it will provision:
   - `axiom-postgres` (Database)
   - `axiom-redis` (Key-Value Cache)
   - `axiom-api` (FastAPI Web Service)
   - `axiom-worker` (Celery Background Worker)
   - `axiom-web` (Next.js Web Service)
6. Under **Environment Variables**, provide your API keys:
   - `GEMINI_API_KEY`: Your Google Gemini API Key
   - `TAVILY_API_KEY`: Your Tavily Search API Key
7. Click **Apply**.
8. Render will build and deploy all services in the correct sequence. Once finished, visit your `axiom-web` URL (`https://axiom-web.onrender.com`).

---

## Method 2: Manual Service-by-Service Deployment

If you prefer deploying services individually or using external free providers (like [Upstash Redis](https://upstash.com) for a 100% free non-expiring Redis):

### 1. PostgreSQL Database
1. Go to **New +** → **PostgreSQL**.
2. **Name**: `axiom-postgres`
3. **Database**: `dataintel`
4. **User**: `dataintel`
5. **Plan**: Free
6. Click **Create Database**. Copy the **Internal Database URL**.

### 2. Redis (Key-Value or Upstash)
- **Option A (Render Key-Value)**: Go to **New +** → **Redis** / **Key-Value**, select Free tier, and copy the internal connection URL.
- **Option B (Upstash Redis - 100% Free forever)**: Create a free Redis database at [upstash.com](https://upstash.com) and copy the `rediss://...` connection URL.

### 3. FastAPI Web Service (`apps/api`)
1. Go to **New +** → **Web Service**.
2. Connect your repo and set:
   - **Root Directory**: `apps/api`
   - **Runtime**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install --no-root`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables:
   - `DATABASE_URL`: *(Internal PostgreSQL URL from Step 1)*
   - `REDIS_URL`: *(Redis connection URL from Step 2)*
   - `GEMINI_API_KEY`: `your_gemini_key`
   - `TAVILY_API_KEY`: `your_tavily_key`
   - `PYTHONPATH`: `.:../../packages:../..`
4. Click **Create Web Service**. Note the deployed URL (e.g. `https://axiom-api.onrender.com`).

### 4. Celery Background Worker (`apps/worker`)
1. Go to **New +** → **Background Worker**.
2. Connect your repo and set:
   - **Root Directory**: `apps/worker`
   - **Runtime**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false && poetry install --no-root`
   - **Start Command**: `celery -A worker.celery_app worker --loglevel=info --pool=threads --concurrency=4 -Q celery,planning,execution,processing`
3. Add the same Environment Variables as Step 3:
   - `DATABASE_URL`
   - `REDIS_URL`
   - `GEMINI_API_KEY`
   - `TAVILY_API_KEY`
   - `PYTHONPATH`: `.:../../packages:../..`
4. Click **Create Background Worker**.

### 5. Next.js Web Frontend (`apps/web`)
1. Go to **New +** → **Web Service**.
2. Connect your repo and set:
   - **Root Directory**: `apps/web`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run start`
3. Add Environment Variables:
   - `NODE_ENV`: `production`
   - `NEXT_PUBLIC_API_URL`: *(Your API URL from Step 3, e.g. `https://axiom-api.onrender.com`)*
4. Click **Create Web Service**.

---

## Verification & Health Check

Once deployed:
1. Visit `https://<your-api-url>/health` → should return `{"status":"ok"}`.
2. Visit `https://<your-api-url>/docs` → opens Swagger UI documentation.
3. Open `https://<your-web-url>` in your browser.
4. Submit a sample query (e.g. *"Find 5 AI events in 2025"*) to verify end-to-end execution.
