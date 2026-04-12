/**
 * REST API client for SignalFlow backend.
 */

import { API_URL } from './constants';

function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem('signalflow_access_token');
}

function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem('signalflow_refresh_token');
}

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  try {
    const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });

    if (!res.ok) {
      // Refresh failed — clear all tokens
      sessionStorage.removeItem('signalflow_access_token');
      sessionStorage.removeItem('signalflow_refresh_token');
      return false;
    }

    const json = await res.json();
    const tokens = json.data?.tokens;
    if (tokens?.access_token && tokens?.refresh_token) {
      sessionStorage.setItem('signalflow_access_token', tokens.access_token);
      sessionStorage.setItem('signalflow_refresh_token', tokens.refresh_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add Bearer token if available
  const token = getAccessToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const res = await fetch(`${API_URL}${path}`, {
      headers,
      ...init,
      signal: controller.signal,
    });

    if (!res.ok) {
      // Handle 401 — attempt token refresh once
      if (res.status === 401 && typeof window !== 'undefined') {
        // Deduplicate concurrent refresh attempts
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = tryRefreshToken().finally(() => {
            isRefreshing = false;
            refreshPromise = null;
          });
        }

        const refreshed = await (refreshPromise ?? Promise.resolve(false));
        if (refreshed) {
          // Retry original request with new token
          const newToken = getAccessToken();
          const retryHeaders: Record<string, string> = {
            'Content-Type': 'application/json',
          };
          if (newToken) {
            retryHeaders['Authorization'] = `Bearer ${newToken}`;
          }
          const retryController = new AbortController();
          const retryTimeoutId = setTimeout(() => retryController.abort(), 15000);
          try {
            const retryRes = await fetch(`${API_URL}${path}`, {
              headers: retryHeaders,
              ...init,
              signal: retryController.signal,
            });
            if (retryRes.ok) {
              return retryRes.json() as Promise<T>;
            }
          } finally {
            clearTimeout(retryTimeoutId);
          }
        }

        // Refresh failed — clear auth state
        sessionStorage.removeItem('signalflow_access_token');
        sessionStorage.removeItem('signalflow_refresh_token');
    }
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json() as Promise<T>;
  } finally {
    clearTimeout(timeoutId);
  }
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

  getAccuracyTrend: (weeks?: number) =>
    apiFetch(`/api/v1/signals/stats/trend${weeks ? `?weeks=${weeks}` : ''}`),

  getMarketOverview: () =>
    apiFetch('/api/v1/markets/overview'),

  getAlertConfig: () =>
    apiFetch('/api/v1/alerts/config'),

  createAlertConfig: (data: Record<string, unknown>) =>
    apiFetch('/api/v1/alerts/config', { method: 'POST', body: JSON.stringify(data) }),

  updateAlertConfig: (id: string, data: Record<string, unknown>) =>
    apiFetch(`/api/v1/alerts/config/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  getWatchlist: () =>
    apiFetch('/api/v1/alerts/watchlist'),

  updateWatchlist: (symbol: string, action: 'add' | 'remove') =>
    apiFetch('/api/v1/alerts/watchlist', {
      method: 'POST',
      body: JSON.stringify({ symbol, action }),
    }),

  // ── P3: Price Alerts ──
  getPriceAlerts: () =>
    apiFetch('/api/v1/alerts/price'),

  createPriceAlert: (data: { symbol: string; market_type: string; condition: string; threshold: string }) =>
    apiFetch('/api/v1/alerts/price', { method: 'POST', body: JSON.stringify(data) }),

  deletePriceAlert: (alertId: string) =>
    apiFetch(`/api/v1/alerts/price/${alertId}`, { method: 'DELETE' }),

  // ── P3: Portfolio ──
  getTrades: (symbol?: string) =>
    apiFetch(`/api/v1/portfolio/trades${symbol ? `?symbol=${symbol}` : ''}`),

  logTrade: (data: { symbol: string; market_type: string; side: string; quantity: string; price: string; notes?: string }) =>
    apiFetch('/api/v1/portfolio/trades', { method: 'POST', body: JSON.stringify(data) }),

  getPortfolioSummary: () =>
    apiFetch('/api/v1/portfolio/summary'),

  // ── P3: Signal Sharing ──
  shareSignal: (signalId: string) =>
    apiFetch(`/api/v1/signals/${signalId}/share`, { method: 'POST' }),

  getSharedSignal: (shareId: string) =>
    apiFetch(`/api/v1/signals/shared/${shareId}`),

  // ── Signal Feedback ──
  submitSignalFeedback: (signalId: string, data: { action: 'took' | 'skipped' | 'watching'; entry_price?: string; notes?: string }) =>
    apiFetch(`/api/v1/signals/${signalId}/feedback`, { method: 'POST', body: JSON.stringify(data) }),

  getSignalFeedback: (signalId: string) =>
    apiFetch(`/api/v1/signals/${signalId}/feedback`),

  // ── P3: AI Q&A ──
  askAboutSymbol: (symbol: string, question: string) =>
    apiFetch('/api/v1/ai/ask', { method: 'POST', body: JSON.stringify({ symbol, question }) }),

  // ── P3: Backtesting ──
  startBacktest: (data: { symbol: string; market_type: string; days?: number }) =>
    apiFetch('/api/v1/backtest/run', { method: 'POST', body: JSON.stringify(data) }),

  getBacktest: (backtestId: string) =>
    apiFetch(`/api/v1/backtest/${backtestId}`),

  // ── News & Event Chain ──
  getNews: (params?: URLSearchParams) =>
    apiFetch(`/api/v1/news${params ? `?${params}` : ''}`),

  getNewsForSignal: (signalId: string) =>
    apiFetch(`/api/v1/news/signal/${signalId}`),

  getEvents: (params?: URLSearchParams) =>
    apiFetch(`/api/v1/news/events${params ? `?${params}` : ''}`),

  getEvent: (eventId: string) =>
    apiFetch(`/api/v1/news/events/${eventId}`),

  getCausalChains: (symbol: string) =>
    apiFetch(`/api/v1/news/chains/${encodeURIComponent(symbol)}`),

  getEventCalendar: (params?: URLSearchParams) =>
    apiFetch(`/api/v1/news/calendar${params ? `?${params}` : ''}`),

  createCalendarEvent: (data: { title: string; event_type: string; scheduled_at: string; affected_symbols?: string[]; impact_magnitude?: number; is_recurring?: boolean }) =>
    apiFetch('/api/v1/news/calendar', { method: 'POST', body: JSON.stringify(data) }),

  // ── Auth ──
  register: (data: { email: string; password: string; telegram_chat_id?: number }) =>
    apiFetch('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    apiFetch('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(data) }),

  forgotPassword: (email: string) =>
    apiFetch('/api/v1/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),

  resetPassword: (data: { email: string; code: string; new_password: string }) =>
    apiFetch('/api/v1/auth/reset-password', { method: 'POST', body: JSON.stringify(data) }),

  refreshToken: (refreshToken: string) =>
    apiFetch('/api/v1/auth/refresh', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }),

  logout: (refreshToken: string) =>
    apiFetch('/api/v1/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: refreshToken }) }),

  getProfile: () =>
    apiFetch('/api/v1/auth/profile'),

  logoutAll: () =>
    apiFetch('/api/v1/auth/logout-all', { method: 'POST' }),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiFetch('/api/v1/auth/password', { method: 'PUT', body: JSON.stringify(data) }),

  deleteAccount: (data: { password: string; confirm: boolean }) =>
    apiFetch('/api/v1/auth/account', { method: 'DELETE', body: JSON.stringify(data) }),
};
