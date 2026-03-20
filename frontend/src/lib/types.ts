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
