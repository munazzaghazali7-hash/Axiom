# ── Data Intelligence Platform — Makefile ─────────────────────────────────────
# Run `make help` for a full list of targets.

.PHONY: help dev infra migrate api worker web seed stop clean demo check

POETRY   ?= $(shell which poetry 2>/dev/null || echo "$(CURDIR)/.poetry-venv/bin/poetry")
PYTHON   := $(POETRY) run python
UVICORN  := $(POETRY) run uvicorn
CELERY   := $(POETRY) run celery

# ── Help ──────────────────────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── Infrastructure ─────────────────────────────────────────────────────────────

infra: ## Start Postgres + Redis (Docker)
	docker-compose up -d
	@echo "✅ Postgres → localhost:5432 | Redis → localhost:6379"

stop: ## Stop Docker infrastructure
	docker-compose down

clean: ## Tear down infra AND delete data volumes
	docker-compose down -v

# ── Backend ────────────────────────────────────────────────────────────────────

migrate: ## Run Alembic migrations (run after `make infra`)
	cd apps/api && $(PYTHON) -m alembic upgrade head

api: ## Start the FastAPI server (port 8000)
	cd apps/api && $(UVICORN) app.main:app --reload --port 8000 --host 0.0.0.0

worker: ## Start the Celery worker
	cd apps/worker && $(CELERY) -A worker.celery_app worker --loglevel=info --concurrency=4 -Q celery,planning,execution,processing

# ── Frontend ───────────────────────────────────────────────────────────────────

web: ## Start the Next.js dev server (port 3000)
	cd apps/web && npm run dev

# ── Demo helpers ───────────────────────────────────────────────────────────────

seed: ## Seed 3 demo workflows into the database
	cd apps/worker && $(PYTHON) seed_demo.py

# ── Check ──────────────────────────────────────────────────────────────────────

check: ## Run the smoke test (requires GEMINI_API_KEY + TAVILY_API_KEY + running DB)
	cd apps/worker && $(PYTHON) smoke_test.py

# ── Full demo setup (Phase 6) ──────────────────────────────────────────────────
# Opens 4 terminal panes isn't possible in Make, but this is the sequence:

demo: ## Print the Phase 6 demo startup sequence
	@echo ""
	@echo "\033[1m  Data Intelligence Platform — Demo Startup\033[0m"
	@echo ""
	@echo "  Run each command in a SEPARATE terminal tab:\033[0m"
	@echo ""
	@echo "  \033[36mTab 1 — Infrastructure:\033[0m"
	@echo "    make infra && make migrate"
	@echo ""
	@echo "  \033[36mTab 2 — API:\033[0m"
	@echo "    make api"
	@echo ""
	@echo "  \033[36mTab 3 — Worker:\033[0m"
	@echo "    make worker"
	@echo ""
	@echo "  \033[36mTab 4 — Frontend:\033[0m"
	@echo "    make web"
	@echo ""
	@echo "  \033[36mTab 5 — Seed demo data (once everything is running):\033[0m"
	@echo "    make seed"
	@echo ""
	@echo "  \033[32mOpen http://localhost:3000 in your browser.\033[0m"
	@echo "  \033[32mSee docs/DEMO.md for the judge demo script.\033[0m"
	@echo ""
