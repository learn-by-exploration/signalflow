# Operations Runbook — SignalFlow AI

> Incident response procedures for production issues.

---

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|-----------|---------------|---------|
| **SEV-1** | System down, all users affected | Immediately | Backend crash, DB down |
| **SEV-2** | Major feature broken, partial impact | < 1 hour | Signal generation stopped, WebSocket down |
| **SEV-3** | Minor feature broken, workaround exists | < 4 hours | One market data source down, Telegram bot unresponsive |
| **SEV-4** | Cosmetic or low-impact issue | Next business day | Chart rendering bug, stale cache |

---

## Incident Procedures

### Backend API Down (SEV-1)

**Symptoms**: `/health` returns 5xx or times out, frontend shows errors

**Steps**:
1. Check Railway dashboard → Backend service → Deployment status
2. Check logs: `railway logs --filter backend --last 100`
3. If OOM: Increase memory allocation in Railway settings
4. If crash loop: Check recent deployment → Rollback to last working deploy
5. If DB connection error: Check PostgreSQL service status in Railway
6. Verify: `curl https://your-backend-url/health`

### Database Issues (SEV-1)

**Symptoms**: 500 errors on all DB-dependent endpoints

**Steps**:
1. Check PostgreSQL service in Railway dashboard
2. Check connection pool: look for "pool exhausted" or "too many connections" in logs
3. If pool exhausted: Restart backend service (clears connection pool)
4. If disk full: Check TimescaleDB retention policies, consider purging old market_data
5. If corrupted: Restore from Railway automatic backup

**Data Retention**:
```sql
-- Remove market_data older than 90 days (safe — only affects historical analysis depth)
DELETE FROM market_data WHERE timestamp < NOW() - INTERVAL '90 days';

-- Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;
```

### Redis Down (SEV-2)

**Symptoms**: Celery tasks stop executing, no real-time updates, AI cache misses

**Steps**:
1. Check Redis service in Railway dashboard
2. If OOM: Flush non-critical caches: `redis-cli FLUSHDB`
3. Restart Redis service
4. Restart Celery worker (it should auto-reconnect, but may need restart)
5. Verify: Tasks should resume within 60 seconds

**Impact**: System continues to function without Redis but:
- Celery tasks won't schedule (no Beat)
- AI sentiment calls won't cache (higher API costs)
- WebSocket pub/sub may not work

### Signal Generation Stopped (SEV-2)

**Symptoms**: No new signals appearing, dashboard shows stale data

**Steps**:
1. Check Celery logs for `generate_signals` task
2. Check if data ingestion is working (look for `fetch_crypto` / `fetch_indian_stocks` tasks)
3. Check if technical analysis is running (look for `run_analysis` task)
4. Check AI budget: If exhausted, signals still generate but capped at 60% confidence
5. Manual trigger: `railway run python -c "from app.tasks.signal_tasks import generate_signals; generate_signals.delay()"`

### One Market Data Source Down (SEV-3)

**Symptoms**: One market (stocks/crypto/forex) showing stale prices

**Steps**:
1. Identify which source: Check task logs for `fetch_indian_stocks`, `fetch_crypto`, `fetch_forex`
2. **yfinance down**: Usually temporary, auto-recovers. Check yahoo finance status
3. **Binance down**: CoinGecko fallback should activate automatically
4. **Alpha Vantage down**: Twelve Data fallback should activate. Check API key validity
5. Other two markets continue unaffected (independent services)

### Telegram Bot Unresponsive (SEV-3)

**Symptoms**: Bot doesn't respond to `/start` or other commands

**Steps**:
1. Check `TELEGRAM_BOT_TOKEN` is valid
2. Check logs for Telegram-related errors
3. Verify bot is registered: `curl https://api.telegram.org/bot<TOKEN>/getMe`
4. Check webhook status: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
5. Restart backend service (bot handler starts on app startup)

### AI Budget Exhausted (SEV-4)

**Symptoms**: AI reasoning becomes template-based, sentiment scores default to 50

**Steps**:
1. Check spend: Look at `ai_cost_log.json` or health endpoint
2. System auto-downgrades: Technical-only signals still generate (capped at 60%)
3. Wait for month reset, or increase `MONTHLY_AI_BUDGET_USD` env var
4. Review: Consider if prompts can be more token-efficient

---

## Celery Task Health Reference

| Task | Interval | Failure Impact |
|------|----------|----------------|
| `fetch_crypto` | 30s | Crypto prices stale |
| `fetch_indian_stocks` | 60s | Stock prices stale (market hours only) |
| `fetch_forex` | 60s | Forex prices stale |
| `run_analysis` | 5min | No new indicator calculations |
| `run_sentiment` | 60min | AI sentiment unavailable |
| `generate_signals` | 5min | No new signals |
| `resolve_signals` | 15min | Signal outcomes not tracked |
| `check_price_alerts` | 60s | Price alerts don't fire |
| `morning_brief` | Daily 8AM IST | No morning summary |
| `evening_wrap` | Daily 4PM IST | No evening recap |
| `seed_calendar_events` | Daily 6AM IST | Calendar not updated |
| `health_check` | 5min | No self-monitoring |

---

## Backup & Recovery

### Automatic Backups (Railway)
- Railway provides automatic daily PostgreSQL backups
- Retention: 7 days on Starter plan
- Access: Railway Dashboard → Database → Backups

### Manual Backup

```bash
# Create backup
railway run pg_dump $DATABASE_URL > signalflow_backup_$(date +%Y%m%d).sql

# Restore from backup
railway run psql $DATABASE_URL < signalflow_backup_20260326.sql
```

### What to Backup

| Data | Priority | Method |
|------|----------|--------|
| PostgreSQL (all tables) | Critical | Railway auto-backup + manual dumps |
| Redis | Low | Ephemeral cache, regenerates on restart |
| `ai_cost_log.json` | Medium | Git-tracked (committed with code) |
| `.env` / env vars | Critical | Store in secure password manager |
| Alembic migrations | Critical | Git-tracked |

### Recovery Priority Order

1. **Database** — Restore PostgreSQL from backup
2. **Environment variables** — Re-set in Railway dashboard
3. **Redis** — Restart service (cache regenerates)
4. **Backend** — Redeploy from last working commit
5. **Frontend** — Redeploy (stateless, no recovery needed)

---

## Scaling

### When to Scale

| Signal | Action |
|--------|--------|
| API response time > 2s | Increase backend memory/CPU |
| WebSocket disconnects frequently | Add WebSocket-dedicated service |
| DB queries > 500ms | Add database indexes, check query plans |
| Celery task queue depth growing | Add worker instances |
| market_data table > 10M rows | Enable TimescaleDB compression |

### How to Scale on Railway

```yaml
# Backend: increase resources
railway service update --memory 1024 --cpu 1

# Add Celery worker (separate service)
# Create new service pointing to same Dockerfile
# Start command: celery -A app.tasks.celery_app worker --loglevel=info
# (Remove --beat from the new worker — only one Beat scheduler)
```
