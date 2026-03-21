/**
 * REST API client for SignalFlow backend.
 */

import { API_URL } from './constants';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  getSignals: (params?: URLSearchParams) =>
    apiFetch(`/api/v1/signals${params ? `?${params}` : ''}`),

  getSignal: (id: string) =>
    apiFetch(`/api/v1/signals/${id}`),

  getSignalHistory: (params?: URLSearchParams) =>
    apiFetch(`/api/v1/signals/history${params ? `?${params}` : ''}`),

  getSignalStats: () =>
    apiFetch('/api/v1/signals/stats'),

  getSymbolTrackRecord: (symbol: string) =>
    apiFetch(`/api/v1/signals/${encodeURIComponent(symbol)}/track-record`),

  getMarketOverview: () =>
    apiFetch('/api/v1/markets/overview'),

  getAlertConfig: (chatId: number) =>
    apiFetch(`/api/v1/alerts/config?telegram_chat_id=${chatId}`),

  createAlertConfig: (data: Record<string, unknown>) =>
    apiFetch('/api/v1/alerts/config', { method: 'POST', body: JSON.stringify(data) }),

  updateAlertConfig: (id: string, data: Record<string, unknown>) =>
    apiFetch(`/api/v1/alerts/config/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getWatchlist: (chatId: number) =>
    apiFetch(`/api/v1/alerts/watchlist?telegram_chat_id=${chatId}`),

  updateWatchlist: (chatId: number, symbol: string, action: 'add' | 'remove') =>
    apiFetch(`/api/v1/alerts/watchlist?telegram_chat_id=${chatId}`, {
      method: 'POST',
      body: JSON.stringify({ symbol, action }),
    }),

  // ── P3: Price Alerts ──
  getPriceAlerts: (chatId: number) =>
    apiFetch(`/api/v1/alerts/price?telegram_chat_id=${chatId}`),

  createPriceAlert: (data: { telegram_chat_id: number; symbol: string; market_type: string; condition: string; threshold: string }) =>
    apiFetch('/api/v1/alerts/price', { method: 'POST', body: JSON.stringify(data) }),

  deletePriceAlert: (alertId: string) =>
    apiFetch(`/api/v1/alerts/price/${alertId}`, { method: 'DELETE' }),

  // ── P3: Portfolio ──
  getTrades: (chatId: number, symbol?: string) =>
    apiFetch(`/api/v1/portfolio/trades?telegram_chat_id=${chatId}${symbol ? `&symbol=${symbol}` : ''}`),

  logTrade: (data: { telegram_chat_id: number; symbol: string; market_type: string; side: string; quantity: string; price: string; notes?: string }) =>
    apiFetch('/api/v1/portfolio/trades', { method: 'POST', body: JSON.stringify(data) }),

  getPortfolioSummary: (chatId: number) =>
    apiFetch(`/api/v1/portfolio/summary?telegram_chat_id=${chatId}`),

  // ── P3: Signal Sharing ──
  shareSignal: (signalId: string) =>
    apiFetch(`/api/v1/signals/${signalId}/share`, { method: 'POST' }),

  getSharedSignal: (shareId: string) =>
    apiFetch(`/api/v1/signals/shared/${shareId}`),

  // ── P3: AI Q&A ──
  askAboutSymbol: (symbol: string, question: string) =>
    apiFetch('/api/v1/ai/ask', { method: 'POST', body: JSON.stringify({ symbol, question }) }),

  // ── P3: Backtesting ──
  startBacktest: (data: { symbol: string; market_type: string; days?: number }) =>
    apiFetch('/api/v1/backtest/run', { method: 'POST', body: JSON.stringify(data) }),

  getBacktest: (backtestId: string) =>
    apiFetch(`/api/v1/backtest/${backtestId}`),
};
