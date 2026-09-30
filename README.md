# Axiom — Provable Autonomous Data Intelligence Platform

> **Code Cubicle 6.0 · Problem Statement 01 · Geek Room**

## What it is

**Axiom** is an autonomous web intelligence platform where you describe what data you need in plain English and receive a clean, structured, source-backed dataset — with every record traceable to its origin URL and accompanied by a cryptographic attestation proving it was never hallucinated.

**Example prompt:** *"Find 20 Python developer job openings in Bangalore"*
**Output:** A paginated, searchable, exportable table of job records — each linked to the source page with a content hash and stub attestation.

---

## Why this beats "just write a custom scraper"

| Problem with custom scrapers | How this platform solves it |
|---|---|
| Must be rebuilt for every new data shape | AI designs the schema and workflow from the prompt |
| Silent breakage when site changes | Every fetch stores a raw snapshot — failures are logged, not hidden |
| No way to verify the data wasn't hallucinated | Attestation ties each record to a source content hash |
| One-off scripts, no history | All runs stored, re-inspectable, re-exportable |

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Vanilla CSS (design-token driven) |
| API | FastAPI, SQLAlchemy async, asyncpg |
| Workers | Celery 5, Redis |
| AI (planner + extractor) | Gemini 3.8 Flash / 1.5 Pro (`google-genai`) |
| Search | Tavily |
| Database | PostgreSQL 15 |
| Attestation | Stub TEE signer (Nitro Enclave–ready architecture) |

---

## Quick start (local)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker Desktop
- `GEMINI_API_KEY` from [Google AI Studio](https://aistudio.google.com)
- `TAVILY_API_KEY` from [Tavily](https://tavily.com)

### 1. Configure environment
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY and TAVILY_API_KEY in .env
```

### 2. Fast Launch with `make` (Recommended)

Run each command in a separate terminal:
```bash
make infra && make migrate   # Tab 1: Start Postgres + Redis and run migrations
make api                     # Tab 2: Start FastAPI (port 8000)
make worker                  # Tab 3: Start Celery worker (all queues)
make web                     # Tab 4: Start Next.js frontend (port 3000)
make seed                    # Tab 5: Populate demo workflow history
```
Open **http://localhost:3000** in your browser.

---

### Alternative: Manual Step-by-Step

#### Start infrastructure
```bash
docker-compose up -d
```

#### Install & migrate API
```bash
cd apps/api
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000
```

#### Start Celery worker
```bash
cd apps/worker
poetry install
poetry run celery -A worker.celery_app worker --loglevel=info -Q celery,planning,execution,processing
```

#### Start frontend
```bash
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

#### Seed demo data
```bash
cd apps/worker
poetry run python seed_demo.py
# Inserts 3 pre-completed workflow runs so History is populated immediately
```

---

## Environment variables

```env
# ── AI ─────────────────────────────────────────
GEMINI_API_KEY=AIzaSy...

# ── Search ─────────────────────────────────────
TAVILY_API_KEY=tvly-...

# ── Database ───────────────────────────────────
DATABASE_URL=postgresql+asyncpg://dataintel:dataintel@localhost:5432/dataintel

# ── Redis ──────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Storage ────────────────────────────────────
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./data/snapshots
```

---

## Architecture

```
User prompt (plain English)
  → Gemini (Workflow planner)    → WorkflowPlan JSON (validated via Pydantic)
  → Celery executor              → search() + fetch() + extract()
  → Processing pipeline          → schema validation + dedup (exact + fuzzy)
  → Postgres                     → results + sources + stub attestations
  → Next.js dashboard            → live monitor + results table + source inspector
```

### Pipeline steps

1. **Plan** — Gemini converts the prompt to a structured `WorkflowPlan` (JSON Schema–validated). The planner *only emits a plan* — it never fetches directly.
2. **Execute** — `search()` (Tavily), `fetch()` (httpx + robots.txt check), `extract()` (Gemini structured JSON output)
3. **Process** — Pydantic schema validation → exact-match dedup on `unique_key` → fuzzy dedup via `rapidfuzz`
4. **Store** — Results land in Postgres, raw page snapshots saved to disk, stub attestation generated per source

### Data model

```
workflow_runs  →  run_steps  →  results  →  sources  →  attestations
```

Every `result` has a `source_id`. Every `source` has an `attestation`. The UI exposes this chain in the **Source Inspector** panel.

---

## Demo walkthrough

See [`docs/DEMO.md`](docs/DEMO.md) for the step-by-step judge demo script.

---

## Project structure

```
apps/
  web/       # Next.js 16 frontend
  api/       # FastAPI backend
  worker/    # Celery workers (planner, executor, processor)
packages/
  schemas/   # Shared Pydantic models (WorkflowPlan, ResultRecord, Attestation)
docs/
  architecture.md  # System design
  DESIGN.md        # Visual design system & tokens
  phases.md        # Project roadmap & current status
  DEMO.md          # Judge demo script
```

---

## Decision log

| Date | Decision |
|---|---|
| Sept 24 | **Tavily** (search) + **Gemini 1.5 Pro** (AI) — locked |
| Oct 4 | Real Nitro Enclave vs stub attestation — final call |
| Oct 8 | Feature freeze |
