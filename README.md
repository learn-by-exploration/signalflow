# SignalFlow AI

> AI-powered trading signal platform for Indian Stocks, Cryptocurrency, and Forex.

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Add your API keys to .env

# 3. Start everything
make init

# This runs: docker compose build → up → migrate
```

**Services:**
- Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Development

```bash
make up          # Start all services
make down        # Stop all services
make logs        # Follow all logs
make test        # Run backend tests
make lint        # Lint backend + frontend
make migrate     # Run database migrations
make migrate-gen msg="add new table"  # Generate migration
```

## Architecture

See [CLAUDE.md](CLAUDE.md) for full architecture documentation, database schema, API contracts, and coding standards.

---

*SignalFlow AI generates AI-assisted signals. This is not financial advice.*
