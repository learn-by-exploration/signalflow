# Deployment Runbook — SignalFlow AI

> Step-by-step guide for deploying SignalFlow AI to Railway.

---

## Prerequisites

- [Railway CLI](https://docs.railway.app/develop/cli) installed
- Railway account with project created
- All API keys obtained (see [environment-variables.md](../reference/environment-variables.md))
- Domain name configured (optional)

---

## First-Time Deployment

### 1. Create Railway Services

SignalFlow requires 5 services:

| Service | Type | Notes |
|---------|------|-------|
| PostgreSQL | Railway Plugin | Enable TimescaleDB extension |
| Redis | Railway Plugin | Default configuration |
| Backend | Dockerfile | `backend/Dockerfile` |
| Celery Worker | Shared with Backend | Runs via `start.sh` |
| Frontend | Dockerfile | `frontend/Dockerfile` |

### 2. Set Environment Variables

Set ALL required variables from [environment-variables.md](../reference/environment-variables.md) in Railway dashboard:

```bash
# Critical — system won't start without these
DATABASE_URL=<railway-provided>
REDIS_URL=<railway-provided>
ANTHROPIC_API_KEY=sk-ant-...
API_SECRET_KEY=<generated>
JWT_SECRET_KEY=<generated>
NEXTAUTH_SECRET=<generated>
ENVIRONMENT=production

# Required for full functionality
TELEGRAM_BOT_TOKEN=<from-botfather>
ALPHA_VANTAGE_API_KEY=<your-key>

# Recommended
SENTRY_DSN=<your-sentry-dsn>
FRONTEND_URL=https://your-domain.com
ALLOWED_HOSTS=your-domain.com
```

### 3. Deploy Backend

The backend uses a combined start command (see `start.sh`):

```bash
# start.sh runs:
# 1. Alembic migration: alembic upgrade head
# 2. Uvicorn: uvicorn app.main:app --host 0.0.0.0 --port $PORT
# 3. Celery: celery -A app.tasks.celery_app worker --beat --loglevel=info
```

Railway config (`railway.toml`):
```toml
[build]
  builder = "dockerfile"
  dockerfilePath = "backend/Dockerfile"

[deploy]
  startCommand = "bash start.sh"
  restartPolicyType = "always"
  healthcheckPath = "/health"
  healthcheckTimeout = 30
```

### 4. Deploy Frontend

Frontend builds as a standalone Next.js app:

```bash
# Build-time environment variables needed:
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend-url.railway.app
NEXT_PUBLIC_API_KEY=<same-as-API_SECRET_KEY>
```

### 5. Verify Deployment

```bash
# Health check
curl https://your-backend-url/health
# Expected: {"status": "healthy", "uptime": ..., "active_signals_count": ...}

# Frontend loads
curl -s -o /dev/null -w "%{http_code}" https://your-frontend-url
# Expected: 200

# WebSocket
wscat -c wss://your-backend-url/ws/signals
# Expected: connection opens, receives pings every 30s
```

### 6. Post-Deployment Checks

- [ ] Health endpoint returns 200
- [ ] Frontend loads without errors
- [ ] Celery tasks are running (check logs for "beat: Starting..." message)
- [ ] Data ingestion tasks fire (crypto should start within 30 seconds)
- [ ] WebSocket connections are stable
- [ ] Telegram bot responds to `/start`
- [ ] Sentry receiving error events (trigger test error if needed)

---

## Routine Deployment

### Deploying Code Changes

```bash
# 1. Ensure all tests pass locally
cd backend && python -m pytest tests/ -v --override-ini="asyncio_mode=auto"
cd ../frontend && npx vitest run

# 2. Push to main branch
git push origin main

# 3. Railway auto-deploys (if connected to GitHub)
# OR manually: railway up

# 4. Monitor deployment logs
railway logs --follow

# 5. Verify health check
curl https://your-backend-url/health
```

### Rolling Back

```bash
# Railway keeps previous deployments
# Option 1: Revert in Railway dashboard → Deployments → Click previous → Redeploy

# Option 2: Git revert
git revert HEAD
git push origin main

# Option 3: Deploy specific commit
railway up --commit <sha>
```

---

## Database Migrations

### Applying Migrations

Migrations run automatically on deploy (via `start.sh`: `alembic upgrade head`).

To run manually:

```bash
# SSH into backend container
railway run bash

# Check current migration
alembic current

# Apply pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

### Creating New Migrations

```bash
# Generate from model changes (local dev)
cd backend
alembic revision --autogenerate -m "add_new_table"

# Review the generated file in migrations/versions/
# Then commit and deploy
```

---

## Monitoring

### Health Check

UptimeRobot should ping `/health` every 60 seconds.

Health endpoint returns:
```json
{
  "status": "healthy",
  "uptime": "2d 14h 32m",
  "last_data_fetch": "2026-03-26T10:30:00Z",
  "active_signals_count": 12,
  "environment": "production"
}
```

### Celery Monitoring

Check Celery task execution in Railway logs:

```bash
railway logs --filter celery
```

Key indicators:
- `[celery.beat] Scheduler: Sending due task` — Beat is running
- `[celery.worker] Task fetch_crypto succeeded` — Tasks executing
- `[celery.worker] Task generate_signals succeeded` — Signal generation working

### Sentry

Configure alerts for:
- Error rate > 10/hour → Email notification
- New error type → Slack/email notification
- Health check failure → Immediate alert

---

## Troubleshooting

### Backend won't start

1. Check DATABASE_URL is correct and PostgreSQL is running
2. Check REDIS_URL is correct and Redis is running
3. Check logs: `railway logs --filter backend`
4. Try: `railway run python -c "from app.main import app; print('OK')"`

### Celery tasks not firing

1. Check Redis is accessible: `railway run python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping()"`
2. Check Beat schedule: look for "Scheduler: Sending" in logs
3. Verify tasks registered: `railway run celery -A app.tasks.celery_app inspect registered`

### Data not updating

1. Check market hours (NSE: 9:15-15:30 IST, Forex: 24/5, Crypto: 24/7)
2. Check API keys are valid (Alpha Vantage, Binance)
3. Check rate limits haven't been exceeded
4. Look for data fetch errors in logs

### AI features not working

1. Check `ANTHROPIC_API_KEY` is set and valid
2. Check monthly budget: `GET /health` shows remaining budget
3. Check cost tracker: `railway run python -c "from app.services.ai_engine.cost_tracker import CostTracker; ct = CostTracker(); print(ct.get_monthly_spend())"`

### WebSocket disconnecting

1. Check Railway idle timeout settings (increase to 300s)
2. Verify heartbeat interval (30s ping/pong)
3. Check for proxy/CDN WebSocket support
