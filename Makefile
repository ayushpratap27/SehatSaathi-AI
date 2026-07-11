# =============================================================================
# SehatSaathi-AI — Makefile
#
# Quick reference:
#   make dev          Start backend + frontend in dev mode
#   make test         Run all backend tests
#   make docker-up    Start full stack with Docker Compose
#   make migrate      Run Alembic migrations
#   make help         Show all available commands
# =============================================================================

.DEFAULT_GOAL := help
PYTHON        := python3
VENV          := .venv
PIP           := $(VENV)/bin/pip
PYTEST        := $(VENV)/bin/python -m pytest

.PHONY: help install dev backend frontend test lint type-check migrate docker-up docker-down docker-build clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────────────────── #

install: ## Create venv and install all backend dependencies
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt "pydantic[email]" PyJWT bcrypt aiosqlite greenlet sqlalchemy alembic
	@echo "✓ Backend dependencies installed. Activate with: source $(VENV)/bin/activate"

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# ── Development ───────────────────────────────────────────────────────────── #

backend: ## Start FastAPI backend (dev)
	source $(VENV)/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start React frontend (dev)
	cd frontend && npm run dev

dev: ## Start backend + frontend in separate terminals (macOS)
	@echo "Starting backend on :8000 and frontend on :3000 …"
	osascript -e 'tell app "Terminal" to do script "cd $(PWD) && source $(VENV)/bin/activate && uvicorn main:app --reload"'
	osascript -e 'tell app "Terminal" to do script "cd $(PWD)/frontend && npm run dev"'

# ── Testing ───────────────────────────────────────────────────────────────── #

test: ## Run all backend tests
	source $(VENV)/bin/activate && $(PYTEST) tests/ -v

test-ci: ## Run tests with coverage (for CI)
	source $(VENV)/bin/activate && $(PYTEST) tests/ -v --tb=short

test-frontend: ## Run frontend tests
	cd frontend && npm test

# ── Code quality ──────────────────────────────────────────────────────────── #

lint: ## Lint backend with ruff
	source $(VENV)/bin/activate && ruff check . --select E,F,W || true

type-check: ## Type-check backend with mypy
	source $(VENV)/bin/activate && mypy app/ --ignore-missing-imports || true

# ── Database ──────────────────────────────────────────────────────────────── #

migrate: ## Run Alembic migrations (head)
	source $(VENV)/bin/activate && alembic upgrade head

migrate-create: ## Create a new Alembic migration (NAME=your_message)
	source $(VENV)/bin/activate && alembic revision --autogenerate -m "$(NAME)"

migrate-down: ## Rollback the last migration
	source $(VENV)/bin/activate && alembic downgrade -1

# ── Docker ────────────────────────────────────────────────────────────────── #

docker-build: ## Build all Docker images
	docker compose build

docker-up: ## Start all services with Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## Tail Docker logs
	docker compose logs -f

docker-clean: ## Remove containers, volumes, and images
	docker compose down -v --rmi local

# ── Utilities ─────────────────────────────────────────────────────────────── #

clean: ## Remove build artefacts and cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f sehat_saathi.db
	rm -rf frontend/dist frontend/node_modules/.cache

env: ## Copy .env.example to .env (first-time setup)
	@if [ -f .env ]; then echo ".env already exists."; else cp .env.example .env && echo "Created .env from .env.example"; fi
