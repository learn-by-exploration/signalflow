/**
 * Application constants — colors, thresholds, market config.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export const SIGNAL_COLORS = {
  STRONG_BUY: '#00E676',
  BUY: '#66BB6A',
  HOLD: '#FFD740',
  SELL: '#EF5350',
  STRONG_SELL: '#D50000',
} as const;

export const CONFIDENCE_THRESHOLDS = {
  STRONG_BUY: 80,
  BUY: 65,
  HOLD_LOW: 36,
  SELL: 21,
  STRONG_SELL: 0,
} as const;

export const MARKET_LABELS = {
  stock: 'Stocks',
  crypto: 'Crypto',
  forex: 'Forex',
} as const;

export const BADGE_LABELS = {
  STRONG_BUY: 'STRONG BUY',
  BUY: 'BUY',
  HOLD: 'HOLD',
  SELL: 'SELL',
  STRONG_SELL: 'STRONG SELL',
} as const;
