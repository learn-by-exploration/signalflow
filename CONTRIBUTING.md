# Contributing to SignalFlow AI

Thank you for your interest in contributing to SignalFlow AI.

---

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 16 + TimescaleDB (via Docker)
- Redis 7 (via Docker)

### Quick Start

```bash
# Clone and configure
git clone <repo-url> && cd signalflow
cp .env.example .env  # Fill in API keys

# First-time setup
make init              # Build + start + migrate

# Daily development
make up                # Start services
make test              # Run all backend tests
make lint              # Lint backend + frontend
make logs              # Follow logs
```

---

## Development Workflow

### Branch Naming
- `feature/signal-generation` — New features
- `fix/websocket-reconnect` — Bug fixes
- `test/indicator-coverage` — Test additions
- `docs/api-reference` — Documentation changes
- `security/jwt-refresh` — Security fixes

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add position sizing calculator
fix: portfolio currency mixing for multi-market trades
test: add Sharpe ratio calculation tests
docs: update API reference with new endpoints
refactor: extract target calculation to separate module
security: add rate limiting per user
```

---

## Pre-Commit Testing Rule (MANDATORY)

**Before every commit, ALL tests must pass.** No exceptions.

```bash
# Backend (from backend/ directory)
python -m pytest tests/ -v --override-ini="asyncio_mode=auto"

# Frontend (from frontend/ directory)
npx vitest run

# Docker build check
docker compose build
```

All three must succeed before `git add` and `git commit`. Never commit with failing tests.

---

## Code Standards

### Python (Backend)
- **Formatter**: Black (line length 100)
- **Linter**: Ruff
- **Type hints**: Required on ALL function signatures
- **Async**: ALL FastAPI endpoints and DB operations must be async
- **Decimal**: Use `decimal.Decimal` for all financial calculations, never `float`
- **Docstrings**: Google style on all public functions

### TypeScript (Frontend)
- **Strict mode**: `"strict": true` — no `any` types
- **Components**: Functional only, no class components
- **State**: Zustand for global, React hooks for local
- **Styling**: Tailwind utility classes only, no inline styles
- **Exports**: Named exports preferred

---

## Adding Features

### New API Endpoint
1. Create route handler in `backend/app/api/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Register router in `backend/app/api/router.py`
4. Write tests in `backend/tests/`
5. Update `docs/reference/api.md`

### New Frontend Component
1. Create component in `frontend/src/components/`
2. Define prop interfaces explicitly
3. Write tests in `frontend/src/__tests__/`
4. Use existing design tokens from `globals.css`

### New Database Table
1. Add SQLAlchemy model in `backend/app/models/`
2. Register in `backend/app/models/__init__.py`
3. Generate migration: `make migrate-gen msg="add_new_table"`
4. Apply migration: `make migrate`
5. Update `docs/reference/database-schema.md`

---

## Testing

### Backend Tests
- **Coverage target**: ≥80%
- **Mock external APIs**: Never call real APIs in tests
- **Fixtures**: Use `conftest.py` fixtures for test DB, test client, mocks
- **Naming**: `test_<module>_<scenario>.py`

### Frontend Tests
- **Framework**: Vitest + Testing Library
- **Pattern**: Arrange → Act → Assert
- **Mocking**: Mock API calls, not components

---

## Project Structure Reference

See [CLAUDE.md](CLAUDE.md) for the complete project structure and architecture details.
