# Database Schema Reference

> **17 tables** | PostgreSQL 16 + TimescaleDB | All prices as `Decimal(20,8)`  
> Last updated: 26 March 2026

---

## Entity Relationship Overview

```
users ──┐
        ├── refresh_tokens (1:N)
        ├── alert_configs (1:1 via telegram_chat_id)
        ├── trades (1:N via telegram_chat_id)
        ├── price_alerts (1:N via telegram_chat_id)
        └── signal_feedback (1:N via telegram_chat_id)

signals ──┐
          ├── signal_history (1:1)
          ├── signal_shares (1:N)
          ├── signal_feedback (1:N)
          ├── signal_news_links (M:N → news_events)
          └── trades (optional FK)

news_events ──┐
              └── signal_news_links (M:N → signals)

event_entities ──┐
                 ├── causal_links.source_event_id (1:N)
                 └── causal_links.target_event_id (1:N)

market_data (TimescaleDB hypertable — standalone)
event_calendar (standalone — scheduling)
backtest_runs (standalone — on-demand analysis)
```

---

## Core Trading Tables

### market_data (TimescaleDB Hypertable)

OHLCV price data ingested every 30-60 seconds per market.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | BIGSERIAL | PK | Auto-increment ID |
| symbol | VARCHAR(20) | NOT NULL | Market symbol (e.g., HDFCBANK.NS, BTCUSDT) |
| market_type | VARCHAR(10) | NOT NULL, CHECK(stock/crypto/forex) | Market classification |
| open | Numeric(20,8) | NOT NULL, CHECK > 0 | Open price |
| high | Numeric(20,8) | NOT NULL, CHECK > 0, >= low | High price |
| low | Numeric(20,8) | NOT NULL, CHECK > 0 | Low price |
| close | Numeric(20,8) | NOT NULL, CHECK > 0 | Close price |
| volume | Numeric(20,4) | nullable | Trading volume |
| timestamp | TIMESTAMPTZ | NOT NULL | Candle timestamp (time dimension) |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |

**Primary Key:** (id, timestamp)  
**Index:** (symbol, timestamp DESC)  
**TimescaleDB:** `create_hypertable('market_data', 'timestamp')`

### signals

Generated trading signals with AI reasoning.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() | Signal identifier |
| symbol | VARCHAR(20) | NOT NULL | Market symbol |
| market_type | VARCHAR(10) | NOT NULL, CHECK(stock/crypto/forex) | Market type |
| signal_type | VARCHAR(15) | NOT NULL, CHECK(STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL) | Signal action |
| confidence | INTEGER | NOT NULL, CHECK(0-100) | Confidence score |
| current_price | Numeric(20,8) | NOT NULL | Entry price |
| target_price | Numeric(20,8) | NOT NULL | Profit target |
| stop_loss | Numeric(20,8) | NOT NULL | Stop-loss level |
| timeframe | VARCHAR(50) | nullable | Expected holding period |
| ai_reasoning | TEXT | NOT NULL | Claude-generated explanation |
| technical_data | JSONB | NOT NULL | All indicator values |
| sentiment_data | JSONB | nullable | AI sentiment analysis result |
| is_active | BOOLEAN | DEFAULT TRUE | Whether signal is still live |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Signal generation time |
| expires_at | TIMESTAMPTZ | nullable | Signal expiry time |

**Indexes:** (is_active, created_at DESC), (symbol, created_at DESC)

### signal_history

Tracks outcomes of resolved signals.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | History entry ID |
| signal_id | UUID | FK → signals.id | Linked signal |
| outcome | VARCHAR(20) | CHECK(hit_target/hit_stop/expired/pending) | Resolution outcome |
| exit_price | Numeric(20,8) | nullable | Price at resolution |
| return_pct | Numeric(8,4) | nullable | Percentage return |
| resolved_at | TIMESTAMPTZ | nullable | When outcome was determined |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation time |

**Index:** (outcome, created_at DESC)

---

## User & Authentication Tables

### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | User ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| telegram_chat_id | BIGINT | UNIQUE, nullable | Telegram integration |
| tier | VARCHAR(10) | DEFAULT 'free' | free/pro/admin |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Registration time |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update |

### refresh_tokens

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Token ID |
| user_id | UUID | indexed | Token owner |
| token_hash | VARCHAR(255) | UNIQUE | SHA256 of refresh token |
| is_revoked | BOOLEAN | DEFAULT FALSE | Revocation flag |
| expires_at | TIMESTAMPTZ | NOT NULL | Token expiry |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

### alert_configs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Config ID |
| telegram_chat_id | BIGINT | UNIQUE, NOT NULL | Telegram user |
| username | VARCHAR(100) | nullable | Display name |
| markets | JSONB | DEFAULT '["stock","crypto","forex"]' | Subscribed markets |
| min_confidence | INTEGER | DEFAULT 60 | Minimum confidence filter |
| signal_types | JSONB | DEFAULT '["STRONG_BUY","BUY","SELL","STRONG_SELL"]' | Signal type filter |
| quiet_hours | JSONB | nullable | {start:"23:00", end:"07:00"} |
| watchlist | JSONB | DEFAULT [] | Watched symbols |
| is_active | BOOLEAN | DEFAULT TRUE | Alert status |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | Last update |

---

## Portfolio & Feedback Tables

### trades

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Trade ID |
| telegram_chat_id | BIGINT | NOT NULL | Trade owner |
| symbol | VARCHAR(20) | NOT NULL | Traded symbol |
| market_type | VARCHAR(10) | NOT NULL | Market type |
| side | VARCHAR(4) | NOT NULL | buy/sell |
| quantity | Numeric(20,8) | NOT NULL | Trade quantity |
| price | Numeric(20,8) | NOT NULL | Trade price |
| notes | TEXT | nullable | User notes |
| signal_id | UUID | nullable, FK → signals.id | Linked signal |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Trade time |

### price_alerts

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Alert ID |
| telegram_chat_id | BIGINT | NOT NULL | Alert owner |
| symbol | VARCHAR(20) | NOT NULL | Target symbol |
| market_type | VARCHAR(10) | NOT NULL | Market type |
| condition | VARCHAR(10) | NOT NULL | above/below |
| threshold | Numeric(20,8) | NOT NULL | Trigger price |
| is_triggered | BOOLEAN | DEFAULT FALSE | Trigger status |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| triggered_at | TIMESTAMPTZ | nullable | When triggered |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

### signal_feedback

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Feedback ID |
| signal_id | UUID | NOT NULL, indexed | Signal reference |
| telegram_chat_id | BIGINT | NOT NULL, indexed | User reference |
| action | VARCHAR(20) | NOT NULL | took/skipped/watching |
| entry_price | Numeric(20,8) | nullable | User's actual entry |
| notes | VARCHAR(500) | nullable | User notes |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Feedback time |

### signal_shares

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Share token (used in URL) |
| signal_id | UUID | NOT NULL | Shared signal |
| created_by | VARCHAR(36) | nullable | Creator user ID |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Share creation |
| expires_at | TIMESTAMPTZ | DEFAULT NOW() + 30 days | Share expiry |

---

## News & Events Tables

### news_events

Raw news articles ingested from sources.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Event ID |
| headline | TEXT | NOT NULL | Article headline |
| source | VARCHAR(100) | nullable | Source name |
| source_url | TEXT | nullable | Original URL |
| symbol | VARCHAR(20) | NOT NULL | Related symbol |
| market_type | VARCHAR(10) | NOT NULL | Market type |
| sentiment_direction | VARCHAR(10) | nullable | bullish/bearish/neutral |
| impact_magnitude | INTEGER | nullable | 1-5 scale |
| event_category | VARCHAR(30) | nullable | Category classification |
| published_at | TIMESTAMPTZ | nullable | Publication time |
| fetched_at | TIMESTAMPTZ | NOT NULL | Ingestion time |
| is_active | BOOLEAN | DEFAULT TRUE | Active flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Record creation |

**Indexes:** (symbol, created_at DESC), (market_type, created_at DESC)

### event_entities

Deduplicated events extracted from multiple news articles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Entity ID |
| title | VARCHAR(200) | NOT NULL | Event title |
| description | TEXT | nullable | Full description |
| event_category | VARCHAR(30) | NOT NULL | macro_policy/earnings/regulatory/etc |
| source_category | VARCHAR(30) | nullable | central_bank/corporate/government |
| affected_symbols | JSONB | nullable | List of affected symbols |
| affected_sectors | JSONB | nullable | List of sectors |
| affected_markets | JSONB | nullable | List of markets |
| geographic_scope | VARCHAR(20) | nullable | india/us/global |
| impact_magnitude | INTEGER | NOT NULL | 1-5 impact level |
| sentiment_direction | VARCHAR(10) | NOT NULL | bullish/bearish/neutral/mixed |
| confidence | INTEGER | NOT NULL | 0-100 AI confidence |
| article_count | INTEGER | NOT NULL | Contributing articles |
| news_event_ids | JSONB | nullable | Source news UUIDs |
| occurred_at | TIMESTAMPTZ | nullable | Event occurrence time |
| expires_at | TIMESTAMPTZ | nullable | Relevance expiry |
| is_active | BOOLEAN | DEFAULT TRUE | Active flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

**Indexes:** (event_category, created_at DESC), (is_active, created_at DESC)

### causal_links

Causal relationships between events.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Link ID |
| source_event_id | UUID | FK → event_entities.id | Cause event |
| target_event_id | UUID | FK → event_entities.id | Effect event |
| relationship_type | VARCHAR(20) | NOT NULL | causes/amplifies/dampens/contradicts |
| propagation_delay | VARCHAR(20) | nullable | minutes/hours/days/weeks |
| impact_decay | FLOAT | nullable | 0.0-1.0 decay factor |
| confidence | INTEGER | NOT NULL | 0-100 confidence |
| reasoning | TEXT | nullable | Why this relationship |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

**Indexes:** (source_event_id), (target_event_id)

### signal_news_links

Many-to-many: which news articles contributed to which signals.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Link ID |
| signal_id | UUID | FK → signals.id | Signal reference |
| news_event_id | UUID | FK → news_events.id | News reference |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Link creation |

**Indexes:** (signal_id), (news_event_id)

### event_calendar

Scheduled future events (earnings, central bank meetings).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Calendar entry ID |
| title | VARCHAR(200) | NOT NULL | Event title |
| event_type | VARCHAR(30) | NOT NULL | rbi_mpc/fomc/earnings/gdp_release/etc |
| description | TEXT | nullable | Event details |
| scheduled_at | TIMESTAMPTZ | NOT NULL | Scheduled date/time |
| affected_symbols | JSONB | nullable | Impacted symbols |
| affected_markets | JSONB | nullable | Impacted markets |
| impact_magnitude | INTEGER | NOT NULL | 1-5 expected impact |
| is_recurring | BOOLEAN | DEFAULT FALSE | Recurring event flag |
| recurrence_rule | VARCHAR(100) | nullable | bimonthly/quarterly/etc |
| outcome | TEXT | nullable | Post-event result |
| is_completed | BOOLEAN | DEFAULT FALSE | Completion flag |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |

**Indexes:** (scheduled_at), (event_type)

---

## Analysis Tables

### backtest_runs

On-demand historical backtesting results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Backtest ID |
| symbol | VARCHAR(20) | NOT NULL | Tested symbol |
| market_type | VARCHAR(10) | NOT NULL | Market type |
| start_date | TIMESTAMPTZ | NOT NULL | Backtest start |
| end_date | TIMESTAMPTZ | NOT NULL | Backtest end |
| total_signals | INTEGER | NOT NULL | Signals generated |
| wins | INTEGER | NOT NULL | Winning trades |
| losses | INTEGER | NOT NULL | Losing trades |
| win_rate | FLOAT | NOT NULL | Win percentage |
| avg_return_pct | FLOAT | NOT NULL | Average return |
| total_return_pct | FLOAT | NOT NULL | Total return |
| max_drawdown_pct | FLOAT | NOT NULL | Maximum drawdown |
| parameters | JSONB | NOT NULL | Strategy parameters |
| status | VARCHAR(20) | NOT NULL | pending/running/completed/failed |
| error_message | TEXT | nullable | Failure reason |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Creation time |
| completed_at | TIMESTAMPTZ | nullable | Completion time |

---

## Migration History

| Migration | Description | Date |
|-----------|-------------|------|
| `b0396d5bb542` | Initial schema (market_data, signals, alert_configs, signal_history) | Phase 1 |
| `c4a8f2d1e3b5` | Add watchlist column to alert_configs | Phase 2 |
| `d5b9e3f4a6c7` | Add P3 tables (price_alerts, trades, signal_shares, backtest_runs) | Phase 3 |
| (pending) | Add signal_feedback table | v1.1 |
