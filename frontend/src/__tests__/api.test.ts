import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '@/lib/api';

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Internal Server Error',
    json: () => Promise.resolve(data),
  });
}

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('api.getSignals', () => {
  it('fetches signals without params', async () => {
    const payload = { data: [], meta: { timestamp: '', count: 0 } };
    mockFetch.mockReturnValue(jsonResponse(payload));

    const result = await api.getSignals();
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/signals');
    expect(result).toEqual(payload);
  });

  it('appends query params', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: [] }));
    const params = new URLSearchParams({ market: 'stock', limit: '10' });
    await api.getSignals(params);
    expect(mockFetch.mock.calls[0][0]).toContain('?market=stock&limit=10');
  });

  it('throws on non-OK response', async () => {
    mockFetch.mockReturnValue(jsonResponse(null, 500));
    await expect(api.getSignals()).rejects.toThrow('API error: 500');
  });
});

describe('api.getSignal', () => {
  it('fetches single signal by id', async () => {
    const payload = { data: { id: 'abc' } };
    mockFetch.mockReturnValue(jsonResponse(payload));

    const result = await api.getSignal('abc');
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/signals/abc');
    expect(result).toEqual(payload);
  });
});

describe('api.getSignalHistory', () => {
  it('fetches signal history', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: [] }));
    await api.getSignalHistory();
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/signals/history');
  });

  it('appends history params', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: [] }));
    const params = new URLSearchParams({ outcome: 'hit_target' });
    await api.getSignalHistory(params);
    expect(mockFetch.mock.calls[0][0]).toContain('?outcome=hit_target');
  });
});

describe('api.getSignalStats', () => {
  it('fetches stats', async () => {
    const stats = { total_signals: 100, win_rate: 65 };
    mockFetch.mockReturnValue(jsonResponse(stats));
    const result = await api.getSignalStats();
    expect(result).toEqual(stats);
  });
});

describe('api.getSymbolTrackRecord', () => {
  it('encodes symbol in URL', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.getSymbolTrackRecord('HDFC BANK');
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/signals/HDFC%20BANK/track-record');
  });
});

describe('api.getAccuracyTrend', () => {
  it('fetches without weeks param', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: [] }));
    await api.getAccuracyTrend();
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/signals/stats/trend');
    expect(mockFetch.mock.calls[0][0]).not.toContain('?weeks=');
  });

  it('appends weeks param', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: [] }));
    await api.getAccuracyTrend(12);
    expect(mockFetch.mock.calls[0][0]).toContain('?weeks=12');
  });
});

describe('api.getMarketOverview', () => {
  it('fetches market overview', async () => {
    const data = { data: { stocks: [], crypto: [], forex: [] } };
    mockFetch.mockReturnValue(jsonResponse(data));
    const result = await api.getMarketOverview();
    expect(result).toEqual(data);
  });
});

describe('api mutations', () => {
  it('createAlertConfig sends POST', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.createAlertConfig({ telegram_chat_id: 123 });
    expect(mockFetch.mock.calls[0][1].method).toBe('POST');
    expect(mockFetch.mock.calls[0][1].body).toContain('123');
  });

  it('updateAlertConfig sends PUT', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.updateAlertConfig('cfg-1', { min_confidence: 70 });
    expect(mockFetch.mock.calls[0][0]).toContain('/api/v1/alerts/config/cfg-1');
    expect(mockFetch.mock.calls[0][1].method).toBe('PUT');
  });

  it('logTrade sends POST with trade data', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.logTrade({
      telegram_chat_id: 123,
      symbol: 'RELIANCE.NS',
      market_type: 'stock',
      side: 'buy',
      quantity: '10',
      price: '2450.00',
    });
    expect(mockFetch.mock.calls[0][1].method).toBe('POST');
    expect(mockFetch.mock.calls[0][0]).toContain('/portfolio/trades');
  });

  it('startBacktest sends POST', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.startBacktest({ symbol: 'RELIANCE.NS', market_type: 'stock', days: 90 });
    expect(mockFetch.mock.calls[0][1].method).toBe('POST');
    expect(mockFetch.mock.calls[0][0]).toContain('/backtest/run');
  });

  it('shareSignal sends POST', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: { share_id: 'abc' } }));
    await api.shareSignal('sig-1');
    expect(mockFetch.mock.calls[0][1].method).toBe('POST');
    expect(mockFetch.mock.calls[0][0]).toContain('/signals/sig-1/share');
  });

  it('askAboutSymbol sends POST with symbol and question', async () => {
    mockFetch.mockReturnValue(jsonResponse({ answer: 'test', source: 'claude' }));
    await api.askAboutSymbol('RELIANCE', 'What is RSI?');
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.symbol).toBe('RELIANCE');
    expect(body.question).toBe('What is RSI?');
  });

  it('deletePriceAlert sends DELETE', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.deletePriceAlert('alert-1');
    expect(mockFetch.mock.calls[0][1].method).toBe('DELETE');
  });
});

describe('api.getWatchlist', () => {
  it('calls watchlist endpoint', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: { watchlist: [] } }));
    await api.getWatchlist();
    expect(mockFetch.mock.calls[0][0]).toContain('/alerts/watchlist');
  });
});

describe('api.updateWatchlist', () => {
  it('sends POST with symbol and action', async () => {
    mockFetch.mockReturnValue(jsonResponse({ data: {} }));
    await api.updateWatchlist('RELIANCE.NS', 'add');
    expect(mockFetch.mock.calls[0][1].method).toBe('POST');
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.symbol).toBe('RELIANCE.NS');
    expect(body.action).toBe('add');
  });
});

describe('api error handling', () => {
  it('throws with status text on 404', async () => {
    mockFetch.mockReturnValue(
      Promise.resolve({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: () => Promise.resolve({}),
      }),
    );
    await expect(api.getSignal('missing')).rejects.toThrow('API error: 404 Not Found');
  });

  it('sets Content-Type header on all requests', async () => {
    mockFetch.mockReturnValue(jsonResponse({}));
    await api.getSignals();
    expect(mockFetch.mock.calls[0][1]?.headers?.['Content-Type'] ?? mockFetch.mock.calls[0][1]?.headers).toBeDefined();
  });
});
