.PHONY: up down build logs backend-shell db-shell migrate test lint migration-check

# ── Docker ──
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend celery

# ── Development ──
backend-shell:
	docker compose exec backend bash

db-shell:
	docker compose exec db psql -U postgres signalflow

# ── Database ──
migrate:
	cd backend && alembic upgrade head

migrate-gen:
	cd backend && alembic revision --autogenerate -m "$(msg)"

migration-check:
	@echo "── Checking for model-migration drift ──"
	cd backend && python -m pytest tests/test_migration_integrity.py -v --override-ini="asyncio_mode=auto"

# ── Testing ──
test:
	cd backend && python -m pytest tests/ -v

test-cov:
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html

# ── Linting ──
lint:
	cd backend && ruff check app/
	cd frontend && npm run lint

format:
	cd backend && black app/
	cd backend && ruff check --fix app/

# ── Frontend ──
frontend-dev:
	cd frontend && npm run dev

frontend-install:
	cd frontend && npm install

# ── Quick start ──
init: build up migrate
	@echo "SignalFlow is running!"
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "API docs: http://localhost:8000/docs"
