/**
 * Shared test helpers: factory functions, mock data, and utilities.
 */

import type { Signal, MarketSnapshot, AlertConfig, SignalHistoryItem, Trade, PortfolioSummary, BacktestRun } from '@/lib/types';

// ── Signal Factory ──

export function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'sig-test-1',
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    signal_type: 'BUY',
    confidence: 72,
    current_price: '1678.90',
    target_price: '1780.00',
    stop_loss: '1630.00',
    timeframe: '2-4 weeks',
    ai_reasoning: 'Credit growth is accelerating. NIM expansion confirmed.',
    technical_data: {
      rsi: { value: 62, signal: 'neutral' },
      macd: { signal: 'buy' },
      bollinger: { signal: 'buy' },
    },
    sentiment_data: {
      score: 75,
      key_factors: ['Positive earnings', 'Strong FII inflows'],
    },
    is_active: true,
    created_at: new Date().toISOString(),
    expires_at: null,
    ...overrides,
  };
}

// ── Market Snapshot Factory ──

export function makeSnapshot(overrides: Partial<MarketSnapshot> = {}): MarketSnapshot {
  return {
    symbol: 'RELIANCE.NS',
    price: '2450.50',
    change_pct: '1.25',
    volume: '12500000',
    market_type: 'stock',
    ...overrides,
  };
}

// ── Alert Config Factory ──

export function makeAlertConfig(overrides: Partial<AlertConfig> = {}): AlertConfig {
  return {
    id: 'alert-1',
    telegram_chat_id: 123456,
    username: 'testuser',
    markets: ['stock', 'crypto', 'forex'],
    min_confidence: 60,
    signal_types: ['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL'],
    quiet_hours: null,
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Signal History Factory ──

export function makeHistoryItem(overrides: Partial<SignalHistoryItem & { signal?: Signal }> = {}): SignalHistoryItem & { signal?: Signal } {
  return {
    id: 'hist-1',
    signal_id: 'sig-test-1',
    outcome: 'hit_target',
    exit_price: '1780.00',
    return_pct: '6.02',
    resolved_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    signal: makeSignal(),
    ...overrides,
  };
}

// ── Trade Factory ──

export function makeTrade(overrides: Partial<Trade> = {}): Trade {
  return {
    id: 'trade-1',
    telegram_chat_id: 123456,
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    side: 'buy',
    quantity: '10',
    price: '1678.90',
    notes: null,
    signal_id: null,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Portfolio Summary Factory ──

export function makePortfolioSummary(overrides: Partial<PortfolioSummary> = {}): PortfolioSummary {
  return {
    total_invested: '50000.00',
    current_value: '52500.00',
    total_pnl: '2500.00',
    total_pnl_pct: 5.0,
    positions: [
      {
        symbol: 'HDFCBANK.NS',
        market_type: 'stock',
        quantity: '10',
        avg_price: '1678.90',
        current_price: '1730.00',
        value: '17300.00',
        pnl: '511.00',
        pnl_pct: 3.04,
      },
    ],
    ...overrides,
  };
}

// ── Backtest Factory ──

export function makeBacktestRun(overrides: Partial<BacktestRun> = {}): BacktestRun {
  return {
    id: 'bt-1',
    symbol: 'RELIANCE.NS',
    market_type: 'stock',
    start_date: '2025-01-01T00:00:00Z',
    end_date: '2025-12-31T00:00:00Z',
    total_signals: 50,
    wins: 30,
    losses: 20,
    win_rate: 60.0,
    avg_return_pct: 2.5,
    total_return_pct: 18.0,
    max_drawdown_pct: 8.5,
    status: 'completed',
    error_message: null,
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    ...overrides,
  };
}

// ── Stock snapshots set ──

export function makeStockSnapshots(): MarketSnapshot[] {
  return [
    makeSnapshot({ symbol: 'RELIANCE.NS', price: '2450.50', change_pct: '1.25' }),
    makeSnapshot({ symbol: 'HDFCBANK.NS', price: '1680.00', change_pct: '-0.50' }),
    makeSnapshot({ symbol: 'TCS.NS', price: '3890.00', change_pct: '0.75' }),
  ];
}

export function makeCryptoSnapshots(): MarketSnapshot[] {
  return [
    makeSnapshot({ symbol: 'BTCUSDT', price: '97842.00', change_pct: '3.87', market_type: 'crypto' }),
    makeSnapshot({ symbol: 'ETHUSDT', price: '3250.00', change_pct: '-1.20', market_type: 'crypto' }),
  ];
}

export function makeForexSnapshots(): MarketSnapshot[] {
  return [
    makeSnapshot({ symbol: 'USDINR', price: '83.42', change_pct: '0.15', market_type: 'forex', volume: null }),
    makeSnapshot({ symbol: 'EURUSD', price: '1.0850', change_pct: '-0.30', market_type: 'forex', volume: null }),
  ];
}
