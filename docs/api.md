# SignalFlow AI — API Reference

> **Version:** v1.0.0 | **Base URL:** `http://localhost:8000` | **API Prefix:** `/api/v1`

---

## Overview

SignalFlow AI exposes a RESTful API for accessing trading signals, market data, alert configuration, portfolio management, and AI-powered analysis. All endpoints return JSON. A WebSocket endpoint provides real-time signal and market updates.

**Authentication:** None required (single-user personal deployment).

**Response Envelope:** Most endpoints wrap responses in a standard envelope:

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-21T12:00:00Z",
    "count": 5,
    "total": 23
  }
}
```

**Decimal Precision:** All prices and financial values are returned as strings (e.g., `"1678.90"`) to preserve decimal precision. Parse them as `Decimal`, never `float`.

---

## Table of Contents

- [Health Check](#health-check)
- [Signals](#signals)
- [Signal History & Stats](#signal-history--stats)
- [Markets](#markets)
- [Alert Configuration](#alert-configuration)
- [Price Alerts](#price-alerts)
- [Portfolio](#portfolio)
- [AI Q&A](#ai-qa)
- [Backtesting](#backtesting)
- [Signal Sharing](#signal-sharing)
- [WebSocket](#websocket)
- [Schema Definitions](#schema-definitions)
- [Rate Limiting](#rate-limiting)
- [Error Responses](#error-responses)

---

## Health Check

### `GET /health`

System status and diagnostics. No `/api/v1` prefix.

**Response:**

```json
{
  "status": "healthy",
  "uptime": "0:05:23.123456",
  "environment": "production",
  "disclaimer": "SignalFlow AI generates AI-powered signals for educational purposes. Not financial advice.",
  "db_status": "ok",
  "active_signals_count": 23,
  "last_data_fetch": "2026-03-21T12:00:00Z",
  "redis_status": "ok",
  "ai_budget_remaining_pct": 75.3
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"healthy"` or `"degraded"` |
| `db_status` | string | `"ok"` or `"error"` |
| `redis_status` | string | `"ok"` or `"error"` |
| `ai_budget_remaining_pct` | float | Remaining monthly Claude API budget (0–100) |

---

## Signals

### `GET /api/v1/signals` — List Active Signals

Returns currently active trading signals, sorted by creation time (newest first).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `market` | string | — | Filter: `stock`, `crypto`, `forex` |
| `signal_type` | string | — | Filter: `STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL` |
| `symbol` | string | — | Filter by symbol substring match |
| `min_confidence` | integer | 0 | Only signals with confidence ≥ this value (0–100) |
| `limit` | integer | 20 | Page size (1–100) |
| `offset` | integer | 0 | Pagination offset |

**Response:**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "symbol": "HDFCBANK",
      "market_type": "stock",
      "signal_type": "STRONG_BUY",
      "confidence": 92,
      "current_price": "1678.90",
      "target_price": "1780.00",
      "stop_loss": "1630.00",
      "timeframe": "2-4 weeks",
      "ai_reasoning": "Credit growth accelerating. NIM expansion confirmed...",
      "technical_data": {
        "rsi": { "value": 62.7, "signal": "neutral" },
        "macd": { "value": 12.5, "signal": "bullish", "histogram": 3.2 },
        "bollinger": { "position": "middle", "signal": "neutral" },
        "volume": { "ratio": 1.8, "signal": "high" },
        "sma": { "sma_20": 1650.0, "sma_50": 1620.0, "signal": "bullish" }
      },
      "sentiment_data": {
        "score": 75,
        "key_factors": ["Strong Q3 results", "Credit growth outlook positive"],
        "source_count": 8
      },
      "is_active": true,
      "created_at": "2026-03-20T10:30:00Z",
      "expires_at": null
    }
  ],
  "meta": {
    "timestamp": "2026-03-21T12:00:00Z",
    "count": 5,
    "total": 23
  }
}
```

---

### `GET /api/v1/signals/{signal_id}` — Get Signal Detail

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `signal_id` | UUID | Signal ID |

**Response:**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "symbol": "HDFCBANK",
    "market_type": "stock",
    "signal_type": "STRONG_BUY",
    "confidence": 92,
    "current_price": "1678.90",
    "target_price": "1780.00",
    "stop_loss": "1630.00",
    "timeframe": "2-4 weeks",
    "ai_reasoning": "Credit growth accelerating...",
    "technical_data": { "..." },
    "sentiment_data": { "..." },
    "is_active": true,
    "created_at": "2026-03-20T10:30:00Z",
    "expires_at": null
  }
}
```

**Errors:** `404` if signal not found.

---

## Signal History & Stats

### `GET /api/v1/signals/history` — List Signal History

Past signals with their outcomes (hit target, hit stop, expired).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `outcome` | string | — | Filter: `hit_target`, `hit_stop`, `expired`, `pending` |
| `limit` | integer | 20 | Page size (1–100) |
| `offset` | integer | 0 | Pagination offset |

**Response:**

```json
{
  "data": [
    {
      "id": "uuid",
      "signal_id": "uuid",
      "outcome": "hit_target",
      "exit_price": "1780.00",
      "return_pct": "6.07",
      "resolved_at": "2026-03-20T15:30:00Z",
      "created_at": "2026-03-20T10:30:00Z",
      "signal": {
        "symbol": "HDFCBANK",
        "market_type": "stock",
        "signal_type": "STRONG_BUY",
        "current_price": "1678.90",
        "target_price": "1780.00",
        "stop_loss": "1630.00"
      }
    }
  ],
  "meta": {
    "timestamp": "2026-03-21T12:00:00Z",
    "count": 5,
    "total": 125
  }
}
```

---

### `GET /api/v1/signals/stats` — Aggregate Signal Stats

Overall signal performance statistics.

**Response:**

```json
{
  "total_signals": 125,
  "hit_target": 78,
  "hit_stop": 32,
  "expired": 10,
  "pending": 5,
  "win_rate": 70.9,
  "avg_return_pct": 2.45,
  "last_updated": "2026-03-21T12:00:00Z"
}
```

---

### `GET /api/v1/signals/stats/trend` — Weekly Win Rate Trend

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `weeks` | integer | 8 | Number of weeks to include (1–52) |

**Response:**

```json
[
  {
    "week": "2026-W11",
    "start_date": "2026-03-16",
    "total": 12,
    "hit_target": 9,
    "win_rate": 75.0
  }
]
```

---

### `GET /api/v1/signals/{symbol}/track-record` — Per-Symbol Track Record

30-day performance history for a specific symbol.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `symbol` | string | Trading symbol (e.g., `HDFCBANK`, `BTC`, `USD/INR`) |

**Response:**

```json
{
  "symbol": "HDFCBANK",
  "total_signals_30d": 12,
  "hit_target": 9,
  "hit_stop": 2,
  "expired": 1,
  "win_rate": 81.8,
  "avg_return_pct": 3.21
}
```

---

## Markets

### `GET /api/v1/markets/overview` — Live Market Snapshot

Current prices and changes for all tracked symbols, grouped by market type.

**Response:**

```json
{
  "data": {
    "stocks": [
      {
        "symbol": "HDFCBANK",
        "price": "1678.90",
        "change_pct": "1.42",
        "volume": "250000",
        "market_type": "stock"
      }
    ],
    "crypto": [
      {
        "symbol": "BTC",
        "price": "97842.00",
        "change_pct": "3.87",
        "volume": "50000",
        "market_type": "crypto"
      }
    ],
    "forex": [
      {
        "symbol": "USD/INR",
        "price": "83.45",
        "change_pct": "0.12",
        "volume": null,
        "market_type": "forex"
      }
    ]
  }
}
```

---

## Alert Configuration

### `GET /api/v1/alerts/config` — Get Alert Preferences

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `telegram_chat_id` | integer | Yes | User's Telegram chat ID |

**Response:**

```json
{
  "data": {
    "id": "uuid",
    "telegram_chat_id": 123456789,
    "username": "john_doe",
    "markets": ["stock", "crypto", "forex"],
    "min_confidence": 60,
    "signal_types": ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
    "quiet_hours": { "start": "23:00", "end": "07:00" },
    "watchlist": ["HDFCBANK", "BTC", "USD/INR"],
    "is_active": true,
    "created_at": "2026-03-01T08:00:00Z",
    "updated_at": "2026-03-21T10:00:00Z"
  }
}
```

---

### `POST /api/v1/alerts/config` — Create Alert Config

**Status Code:** 201

**Request Body:**

```json
{
  "telegram_chat_id": 123456789,
  "username": "john_doe",
  "markets": ["stock", "crypto", "forex"],
  "min_confidence": 60,
  "signal_types": ["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"],
  "quiet_hours": { "start": "23:00", "end": "07:00" }
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `telegram_chat_id` | integer | Yes | — | Telegram chat ID |
| `username` | string | No | null | Display name |
| `markets` | string[] | No | `["stock", "crypto", "forex"]` | Markets to receive alerts for |
| `min_confidence` | integer | No | 60 | Minimum confidence threshold (0–100) |
| `signal_types` | string[] | No | `["STRONG_BUY", "BUY", "SELL", "STRONG_SELL"]` | Signal types to alert on |
| `quiet_hours` | object | No | null | `{ start, end }` in 24h format |

**Response:** Same structure as GET.

---

### `PUT /api/v1/alerts/config/{config_id}` — Update Alert Config

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config_id` | UUID | Alert config ID |

**Request Body:** Same fields as POST (all optional for partial update).

**Response:** Updated alert config.

---

### `GET /api/v1/alerts/watchlist` — Get User Watchlist

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `telegram_chat_id` | integer | Yes | User's Telegram chat ID |

**Response:**

```json
{
  "data": ["HDFCBANK", "INFY", "BTC", "USD/INR"]
}
```

---

### `POST /api/v1/alerts/watchlist` — Modify Watchlist

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `telegram_chat_id` | integer | Yes | User's Telegram chat ID |

**Request Body:**

```json
{
  "symbol": "HDFCBANK",
  "action": "add"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Trading symbol |
| `action` | string | `"add"` or `"remove"` |

**Response:** Updated watchlist array.

---

## Price Alerts

### `GET /api/v1/alerts/price` — List Price Alerts

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `telegram_chat_id` | integer | Yes | User's Telegram chat ID |

**Response:**

```json
{
  "data": [
    {
      "id": "uuid",
      "telegram_chat_id": 123456789,
      "symbol": "HDFCBANK",
      "market_type": "stock",
      "condition": "above",
      "threshold": "1700.00",
      "is_triggered": false,
      "is_active": true,
      "triggered_at": null,
      "created_at": "2026-03-20T10:00:00Z"
    }
  ]
}
```

---

### `POST /api/v1/alerts/price` — Create Price Alert

**Status Code:** 201

**Request Body:**

```json
{
  "telegram_chat_id": 123456789,
  "symbol": "HDFCBANK",
  "market_type": "stock",
  "condition": "above",
  "threshold": "1700.00"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `condition` | string | `"above"` or `"below"` |
| `threshold` | string | Price level (decimal string) |

**Response:** Created price alert object.

---

### `DELETE /api/v1/alerts/price/{alert_id}` — Deactivate Price Alert

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `alert_id` | UUID | Price alert ID |

**Response:**

```json
{
  "data": "deleted"
}
```

---

## Portfolio

### `GET /api/v1/portfolio/trades` — List User Trades

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `telegram_chat_id` | integer | Yes | — | User's Telegram chat ID |
| `symbol` | string | No | — | Filter by symbol |
| `limit` | integer | No | 50 | Page size (1–200) |

**Response:**

```json
{
  "data": [
    {
      "id": "uuid",
      "telegram_chat_id": 123456789,
      "symbol": "HDFCBANK",
      "market_type": "stock",
      "side": "buy",
      "quantity": "100",
      "price": "1650.25",
      "notes": "Entry at support level",
      "signal_id": "uuid",
      "created_at": "2026-03-20T10:00:00Z"
    }
  ]
}
```

---

### `POST /api/v1/portfolio/trades` — Log a New Trade

**Status Code:** 201

**Request Body:**

```json
{
  "telegram_chat_id": 123456789,
  "symbol": "HDFCBANK",
  "market_type": "stock",
  "side": "buy",
  "quantity": "100",
  "price": "1650.25",
  "notes": "Entry at support level",
  "signal_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `telegram_chat_id` | integer | Yes | User's Telegram chat ID |
| `symbol` | string | Yes | Trading symbol |
| `market_type` | string | Yes | `stock`, `crypto`, or `forex` |
| `side` | string | Yes | `"buy"` or `"sell"` |
| `quantity` | string | Yes | Amount (decimal string) |
| `price` | string | Yes | Price per unit (decimal string) |
| `notes` | string | No | Optional trade notes |
| `signal_id` | UUID | No | Link to originating signal |

**Response:** Created trade object.

---

### `GET /api/v1/portfolio/summary` — Portfolio Positions & P&L

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `telegram_chat_id` | integer | Yes | User's Telegram chat ID |

**Response:**

```json
{
  "data": {
    "total_invested": "165025.00",
    "current_value": "178910.50",
    "total_pnl": "13885.50",
    "total_pnl_pct": 8.41,
    "positions": [
      {
        "symbol": "HDFCBANK",
        "market_type": "stock",
        "quantity": "100",
        "avg_price": "1650.2500",
        "current_price": "1678.9",
        "value": "167890.00",
        "pnl": "2885.00",
        "pnl_pct": 1.74
      }
    ]
  }
}
```

---

## AI Q&A

### `POST /api/v1/ai/ask` — Ask Claude About a Symbol

Ask a natural-language question about any tracked symbol. Claude analyzes available market data and news to provide an answer.

**Rate Limit:** 5 requests per minute (to control Claude API costs).

**Request Body:**

```json
{
  "symbol": "HDFCBANK",
  "question": "Why is HDFC Bank a good long-term hold?"
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `symbol` | string | Required | Trading symbol |
| `question` | string | Required, max 500 chars | Question to ask |

**Response:**

```json
{
  "data": {
    "answer": "HDFC Bank shows strong fundamentals with consistent credit growth...",
    "source": "claude"
  }
}
```

| Source Value | Meaning |
|-------------|---------|
| `"claude"` | Real Claude API response |
| `"fallback"` | Budget exhausted or API error — generic response provided |

---

## Backtesting

### `POST /api/v1/backtest/run` — Start Backtest

Run a historical backtest of the signal generation algorithm on a specific symbol.

**Status Code:** 201

**Request Body:**

```json
{
  "symbol": "HDFCBANK",
  "market_type": "stock",
  "days": 90
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `symbol` | string | Required | Trading symbol |
| `market_type` | string | Required | `stock`, `crypto`, or `forex` |
| `days` | integer | 90 | Lookback period (7–365) |

**Response:**

```json
{
  "data": {
    "id": "uuid",
    "symbol": "HDFCBANK",
    "market_type": "stock",
    "start_date": "2025-12-21T00:00:00Z",
    "end_date": "2026-03-21T00:00:00Z",
    "total_signals": 0,
    "wins": 0,
    "losses": 0,
    "win_rate": 0.0,
    "avg_return_pct": 0.0,
    "total_return_pct": 0.0,
    "max_drawdown_pct": 0.0,
    "status": "pending",
    "error_message": null,
    "created_at": "2026-03-21T12:00:00Z",
    "completed_at": null
  }
}
```

| Status | Meaning |
|--------|---------|
| `pending` | Queued for processing |
| `running` | Currently executing |
| `completed` | Finished successfully |
| `error` | Failed (see `error_message`) |

---

### `GET /api/v1/backtest/{backtest_id}` — Get Backtest Results

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `backtest_id` | UUID | Backtest run ID |

**Response:** Same structure as POST response. Poll this endpoint until `status` is `completed` or `error`.

---

## Signal Sharing

### `POST /api/v1/signals/{signal_id}/share` — Create Shareable Link

Generate a public, read-only link for a signal.

**Status Code:** 201

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `signal_id` | UUID | Signal ID to share |

**Response:**

```json
{
  "data": {
    "share_id": "uuid",
    "signal_id": "uuid"
  }
}
```

The shareable URL is: `{frontend_url}/shared/{share_id}`

---

### `GET /api/v1/signals/shared/{share_id}` — View Shared Signal

Public endpoint — no authentication required. Returns a read-only view of the shared signal.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `share_id` | UUID | Share token ID |

**Response:**

```json
{
  "data": {
    "symbol": "HDFCBANK",
    "market_type": "stock",
    "signal_type": "STRONG_BUY",
    "confidence": 92,
    "current_price": "1678.90",
    "target_price": "1780.00",
    "stop_loss": "1630.00",
    "timeframe": "2-4 weeks",
    "ai_reasoning": "Credit growth accelerating...",
    "created_at": "2026-03-20T10:30:00Z"
  }
}
```

---

## WebSocket

### `WS /ws/signals` — Real-Time Signal Stream

No `/api/v1` prefix. Connect via WebSocket for live signal and market updates.

**Connection:** `ws://localhost:8000/ws/signals`

---

### Client → Server Messages

**Subscribe to markets:**

```json
{
  "type": "subscribe",
  "markets": ["stock", "crypto", "forex"]
}
```

**Heartbeat response:**

```json
{
  "type": "pong"
}
```

---

### Server → Client Messages

**New signal:**

```json
{
  "type": "signal",
  "data": {
    "id": "uuid",
    "symbol": "HDFCBANK",
    "market_type": "stock",
    "signal_type": "STRONG_BUY",
    "confidence": 92,
    "current_price": "1678.90",
    "target_price": "1780.00",
    "stop_loss": "1630.00",
    "timeframe": "2-4 weeks",
    "ai_reasoning": "Credit growth accelerating...",
    "created_at": "2026-03-20T10:30:00Z"
  }
}
```

**Market price update:**

```json
{
  "type": "market_update",
  "data": {
    "symbol": "BTC",
    "price": "97842.00",
    "change_pct": 3.87
  }
}
```

**Heartbeat (every 30 seconds):**

```json
{
  "type": "ping"
}
```

Client should respond with `{ "type": "pong" }` to keep the connection alive.

---

## Schema Definitions

### Signal

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique signal identifier |
| `symbol` | string | Trading symbol |
| `market_type` | string | `stock`, `crypto`, or `forex` |
| `signal_type` | string | `STRONG_BUY`, `BUY`, `HOLD`, `SELL`, `STRONG_SELL` |
| `confidence` | integer | 0–100 confidence score |
| `current_price` | Decimal | Price at signal generation |
| `target_price` | Decimal | Recommended take-profit level |
| `stop_loss` | Decimal | Recommended stop-loss level |
| `timeframe` | string? | Expected duration (e.g., "2-4 weeks") |
| `ai_reasoning` | string | Claude-generated explanation |
| `technical_data` | object | RSI, MACD, Bollinger, Volume, SMA indicators |
| `sentiment_data` | object? | Score, key factors, source count |
| `is_active` | boolean | Whether signal is still active |
| `created_at` | datetime | Signal creation timestamp |
| `expires_at` | datetime? | Auto-expiry timestamp |

### SignalHistory

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | History record ID |
| `signal_id` | UUID | Reference to original signal |
| `outcome` | string? | `hit_target`, `hit_stop`, `expired`, `pending` |
| `exit_price` | Decimal? | Price at resolution |
| `return_pct` | Decimal? | Percentage return |
| `resolved_at` | datetime? | When the signal was resolved |
| `signal` | object? | Summary of the original signal |

### MarketSnapshot

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Trading symbol |
| `price` | Decimal | Current price |
| `change_pct` | Decimal | Percentage change |
| `volume` | Decimal? | Trading volume |
| `market_type` | string | `stock`, `crypto`, or `forex` |

### AlertConfig

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Config ID |
| `telegram_chat_id` | integer | Telegram chat ID |
| `username` | string? | Display name |
| `markets` | string[] | Subscribed markets |
| `min_confidence` | integer | Minimum confidence threshold (0–100) |
| `signal_types` | string[] | Signal types to alert on |
| `quiet_hours` | object? | `{ start, end }` in 24h format |
| `watchlist` | string[]? | Tracked symbols |
| `is_active` | boolean | Whether alerts are enabled |

### PriceAlert

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Alert ID |
| `telegram_chat_id` | integer | Telegram chat ID |
| `symbol` | string | Trading symbol |
| `market_type` | string | Market type |
| `condition` | string | `"above"` or `"below"` |
| `threshold` | Decimal | Target price level |
| `is_triggered` | boolean | Whether the alert has fired |
| `is_active` | boolean | Whether the alert is still active |

### Trade

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Trade ID |
| `telegram_chat_id` | integer | User's chat ID |
| `symbol` | string | Trading symbol |
| `market_type` | string | Market type |
| `side` | string | `"buy"` or `"sell"` |
| `quantity` | Decimal | Amount traded |
| `price` | Decimal | Price per unit |
| `notes` | string? | Optional notes |
| `signal_id` | UUID? | Linked signal |

### BacktestRun

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Backtest run ID |
| `symbol` | string | Symbol tested |
| `market_type` | string | Market type |
| `start_date` | datetime | Backtest start |
| `end_date` | datetime | Backtest end |
| `total_signals` | integer | Signals generated |
| `wins` | integer | Signals that hit target |
| `losses` | integer | Signals that hit stop |
| `win_rate` | float | Win percentage |
| `avg_return_pct` | float | Average return per signal |
| `total_return_pct` | float | Cumulative return |
| `max_drawdown_pct` | float | Maximum drawdown |
| `status` | string | `pending`, `running`, `completed`, `error` |

---

## Rate Limiting

| Endpoint | Limit | Notes |
|----------|-------|-------|
| `POST /api/v1/ai/ask` | 5/minute | Strict — controls Claude API costs |
| All other endpoints | Default | Global rate limiting via SlowAPI |

When rate-limited, the API returns:

```json
{
  "detail": "Rate limit exceeded"
}
```

**Status Code:** `429 Too Many Requests`

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error description"
}
```

| Status Code | Meaning |
|-------------|---------|
| `400` | Bad request — invalid parameters |
| `404` | Resource not found |
| `422` | Validation error — request body doesn't match schema |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

**Validation errors (422)** include field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "symbol"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

*Last updated: 21 March 2026 | SignalFlow AI v1.0.0*
