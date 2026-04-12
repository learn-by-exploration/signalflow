/**
 * Shared TypeScript types for SignalFlow frontend.
 */

export type MarketType = 'stock' | 'crypto' | 'forex';
export type SignalType = 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';

export interface Signal {
  id: string;
  symbol: string;
  market_type: MarketType;
  signal_type: SignalType;
  confidence: number;
  current_price: string;
  target_price: string;
  stop_loss: string;
  timeframe: string | null;
  ai_reasoning: string;
  technical_data: Record<string, unknown>;
  sentiment_data: Record<string, unknown> | null;
  is_active: boolean;
  is_locked?: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface MarketSnapshot {
  symbol: string;
  price: string;
  change_pct: string;
  volume: string | null;
  market_type: MarketType;
}

export interface AlertConfig {
  id: string;
  telegram_chat_id: number;
  username: string | null;
  markets: MarketType[];
  min_confidence: number;
  signal_types: SignalType[];
  quiet_hours: { start: string; end: string } | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SignalHistoryItem {
  id: string;
  signal_id: string;
  outcome: 'hit_target' | 'hit_stop' | 'expired' | 'pending' | null;
  exit_price: string | null;
  return_pct: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface SignalStats {
  total_signals: number;
  hit_target: number;
  hit_stop: number;
  expired: number;
  pending: number;
  win_rate: number;
  avg_return_pct: number;
  last_updated: string | null;
}

export interface WSMessage {
  type: 'signal' | 'market_update' | 'ping';
  data?: Signal | MarketSnapshot;
}

export interface SymbolTrackRecord {
  symbol: string;
  total_signals_30d: number;
  hit_target: number;
  hit_stop: number;
  expired: number;
  win_rate: number;
  avg_return_pct: number;
}

export interface WeeklyTrendItem {
  week: string;
  start_date: string;
  total: number;
  hit_target: number;
  win_rate: number;
}

// ── P3: Future Features ──

export interface PriceAlert {
  id: string;
  telegram_chat_id: number;
  symbol: string;
  market_type: MarketType;
  condition: 'above' | 'below';
  threshold: string;
  is_triggered: boolean;
  is_active: boolean;
  triggered_at: string | null;
  created_at: string;
}

export interface Trade {
  id: string;
  telegram_chat_id: number;
  symbol: string;
  market_type: MarketType;
  side: 'buy' | 'sell';
  quantity: string;
  price: string;
  notes: string | null;
  signal_id: string | null;
  created_at: string;
}

export interface PortfolioPosition {
  symbol: string;
  market_type: MarketType;
  quantity: string;
  avg_price: string;
  current_price: string;
  value: string;
  pnl: string;
  pnl_pct: number;
}

export interface CurrencyBreakdown {
  currency: string;
  market_type: MarketType;
  invested: string;
  current_value: string;
  pnl: string;
  pnl_pct: number;
}

export interface PortfolioSummary {
  total_invested: string;
  current_value: string;
  total_pnl: string;
  total_pnl_pct: number;
  positions: PortfolioPosition[];
  by_currency: CurrencyBreakdown[];
}

export interface BacktestRun {
  id: string;
  symbol: string;
  market_type: MarketType;
  start_date: string;
  end_date: string;
  total_signals: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_return_pct: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface AskResponse {
  answer: string;
  source: 'claude' | 'fallback';
}

// ── News & Event Chain Types ──

export interface NewsEvent {
  id: string;
  headline: string;
  source: string | null;
  source_url: string | null;
  symbol: string;
  market_type: MarketType;
  sentiment_direction: 'bullish' | 'bearish' | 'neutral' | null;
  impact_magnitude: number | null;
  event_category: string | null;
  published_at: string | null;
  fetched_at: string;
}

export interface EventEntity {
  id: string;
  title: string;
  description: string | null;
  event_category: string;
  affected_symbols: string[];
  affected_sectors: string[];
  impact_magnitude: number;
  sentiment_direction: 'bullish' | 'bearish' | 'neutral' | 'mixed';
  confidence: number;
  article_count: number;
  occurred_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface CausalLink {
  id: string;
  source_event_id: string;
  target_event_id: string;
  relationship_type: 'causes' | 'amplifies' | 'dampens' | 'contradicts' | 'precedes';
  propagation_delay: string | null;
  impact_decay: number;
  confidence: number;
  reasoning: string | null;
}

export interface CausalChain {
  root_event: EventEntity;
  links: CausalLink[];
  downstream_events: EventEntity[];
  chain_score: number;
  net_direction: string;
}

export interface EventCalendar {
  id: string;
  title: string;
  event_type: string;
  scheduled_at: string;
  affected_symbols: string[];
  impact_magnitude: number;
  is_recurring: boolean;
  outcome: string | null;
  is_completed: boolean;
  created_at: string;
}

export interface SignalNewsContext {
  id: string;
  headline: string;
  source: string | null;
  source_url: string | null;
  sentiment_direction: string | null;
  impact_magnitude: number | null;
  event_category: string | null;
  published_at: string | null;
}
