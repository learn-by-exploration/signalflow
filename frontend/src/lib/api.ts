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

  getMarketOverview: () =>
    apiFetch('/api/v1/markets/overview'),

  getAlertConfig: (chatId: number) =>
    apiFetch(`/api/v1/alerts/config?telegram_chat_id=${chatId}`),

  createAlertConfig: (data: Record<string, unknown>) =>
    apiFetch('/api/v1/alerts/config', { method: 'POST', body: JSON.stringify(data) }),

  updateAlertConfig: (id: string, data: Record<string, unknown>) =>
    apiFetch(`/api/v1/alerts/config/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
};
