'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import type { AlertConfig, PriceAlert, MarketType, SignalType } from '@/lib/types';
import { useToast } from '@/components/shared/Toast';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { useUserStore } from '@/store/userStore';

const MARKET_OPTIONS: { value: MarketType; label: string; icon: string }[] = [
  { value: 'stock', label: 'Stocks', icon: '📈' },
  { value: 'crypto', label: 'Crypto', icon: '🪙' },
  { value: 'forex', label: 'Forex', icon: '💱' },
];

const SIGNAL_OPTIONS: { value: SignalType; label: string }[] = [
  { value: 'STRONG_BUY', label: 'Strong Buy' },
  { value: 'BUY', label: 'Buy' },
  { value: 'SELL', label: 'Sell' },
  { value: 'STRONG_SELL', label: 'Strong Sell' },
];

export default function AlertsPage() {
  const { toast } = useToast();
  const chatId = useUserStore((s) => s.chatId) ?? 1;
  const [loading, setLoading] = useState(true);

  // Alert config state
  const [config, setConfig] = useState<AlertConfig | null>(null);
  const [markets, setMarkets] = useState<MarketType[]>(['stock', 'crypto', 'forex']);
  const [minConfidence, setMinConfidence] = useState(60);
  const [signalTypes, setSignalTypes] = useState<SignalType[]>(['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL']);

  // Price alerts state
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);
  const [newAlertSymbol, setNewAlertSymbol] = useState('');
  const [newAlertCondition, setNewAlertCondition] = useState<'above' | 'below'>('above');
  const [newAlertThreshold, setNewAlertThreshold] = useState('');

  // Watchlist state
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [newWatchSymbol, setNewWatchSymbol] = useState('');

  useEffect(() => {
    async function loadAll() {
      try {
        const [configRes, alertsRes, watchRes] = await Promise.allSettled([
          api.getAlertConfig(chatId) as Promise<{ data: AlertConfig }>,
          api.getPriceAlerts(chatId) as Promise<{ data: PriceAlert[] }>,
          api.getWatchlist(chatId) as Promise<{ data: { watchlist: string[] } }>,
        ]);

        if (configRes.status === 'fulfilled' && configRes.value?.data) {
          const c = configRes.value.data;
          setConfig(c);
          setMarkets(c.markets);
          setMinConfidence(c.min_confidence);
          setSignalTypes(c.signal_types);
        }
        if (alertsRes.status === 'fulfilled') {
          setPriceAlerts(alertsRes.value.data);
        }
        if (watchRes.status === 'fulfilled') {
          setWatchlist(watchRes.value.data?.watchlist ?? []);
        }
      } catch {
        // Partial load is fine
      } finally {
        setLoading(false);
      }
    }
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatId]);

  // ── Alert Config Actions ──
  async function saveConfig() {
    try {
      if (config?.id) {
        await api.updateAlertConfig(config.id, {
          markets,
          min_confidence: minConfidence,
          signal_types: signalTypes,
        });
      } else {
        await api.createAlertConfig({
          telegram_chat_id: chatId,
          markets,
          min_confidence: minConfidence,
          signal_types: signalTypes,
        });
      }
      toast('Preferences saved!', 'success');
    } catch {
      toast('Failed to save preferences', 'error');
    }
  }

  const toggleMarket = (m: MarketType) => {
    setMarkets((prev) => (prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]));
  };

  const toggleSignalType = (s: SignalType) => {
    setSignalTypes((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  };

  // ── Price Alert Actions ──
  async function createPriceAlert() {
    if (!newAlertSymbol || !newAlertThreshold) return;
    const symbol = newAlertSymbol.toUpperCase().trim();
    const marketType = symbol.includes('USDT') ? 'crypto' : symbol.includes('/') ? 'forex' : 'stock';
    try {
      const res = (await api.createPriceAlert({
        telegram_chat_id: chatId,
        symbol,
        market_type: marketType,
        condition: newAlertCondition,
        threshold: newAlertThreshold,
      })) as { data: PriceAlert };
      setPriceAlerts((prev) => [res.data, ...prev]);
      setNewAlertSymbol('');
      setNewAlertThreshold('');
      toast(`Alert set: ${symbol} ${newAlertCondition} ${newAlertThreshold}`, 'success');
    } catch {
      toast('Failed to create alert', 'error');
    }
  }

  async function deletePriceAlert(id: string) {
    try {
      await api.deletePriceAlert(id);
      setPriceAlerts((prev) => prev.filter((a) => a.id !== id));
      toast('Alert removed', 'success');
    } catch {
      toast('Failed to delete alert', 'error');
    }
  }

  // ── Watchlist Actions ──
  async function addToWatchlist() {
    const symbol = newWatchSymbol.toUpperCase().trim();
    if (!symbol || watchlist.includes(symbol)) return;
    try {
      await api.updateWatchlist(chatId, symbol, 'add');
      setWatchlist((prev) => [...prev, symbol]);
      setNewWatchSymbol('');
      toast(`${symbol} added to watchlist`, 'success');
    } catch {
      toast('Failed to update watchlist', 'error');
    }
  }

  async function removeFromWatchlist(symbol: string) {
    try {
      await api.updateWatchlist(chatId, symbol, 'remove');
      setWatchlist((prev) => prev.filter((s) => s !== symbol));
      toast(`${symbol} removed`, 'success');
    } catch {
      toast('Failed to update watchlist', 'error');
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen pb-12 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-8">
        <h1 className="text-2xl font-display font-semibold">Alerts & Settings</h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ── Left Column: Alert Preferences ── */}
          <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-5">
            <h2 className="text-base font-display font-semibold">⚙️ Alert Preferences</h2>

            {/* Markets */}
            <div>
              <label className="text-sm text-text-secondary mb-2 block">Markets</label>
              <div className="flex gap-2">
                {MARKET_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => toggleMarket(opt.value)}
                    className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                      markets.includes(opt.value)
                        ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                        : 'border-border-default text-text-muted hover:border-border-hover'
                    }`}
                  >
                    {opt.icon} {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Min confidence — preset buttons + slider */}
            <div>
              <label className="text-sm text-text-secondary mb-2 block">
                Minimum Confidence: <span className="font-mono text-accent-purple">{minConfidence}%</span>
              </label>
              <div className="flex gap-2 mb-2">
                {[60, 70, 80, 90].map((preset) => (
                  <button
                    key={preset}
                    onClick={() => setMinConfidence(preset)}
                    className={`flex-1 py-1.5 text-xs font-mono rounded-lg border transition-colors ${
                      minConfidence === preset
                        ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                        : 'border-border-default text-text-muted hover:border-border-hover'
                    }`}
                  >
                    {preset}%
                  </button>
                ))}
              </div>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))}
                aria-label="Minimum confidence threshold"
                className="w-full accent-accent-purple"
              />
              <div className="flex justify-between text-xs text-text-muted mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Signal types */}
            <div>
              <label className="text-sm text-text-secondary mb-2 block">Signal Types</label>
              <div className="flex flex-wrap gap-2">
                {SIGNAL_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => toggleSignalType(opt.value)}
                    className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                      signalTypes.includes(opt.value)
                        ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                        : 'border-border-default text-text-muted hover:border-border-hover'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={saveConfig}
              className="w-full py-2.5 bg-accent-purple text-white text-sm font-medium rounded-lg hover:bg-accent-purple/90 transition-colors"
            >
              Save Preferences
            </button>
          </section>

          {/* ── Right Column: Watchlist ── */}
          <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
            <h2 className="text-base font-display font-semibold">👁 Watchlist</h2>
            <p className="text-xs text-text-muted">Get priority signals for symbols you care about.</p>

            {/* Add symbol */}
            <div className="flex gap-2">
              <input
                type="text"
                value={newWatchSymbol}
                onChange={(e) => setNewWatchSymbol(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && addToWatchlist()}
                placeholder="e.g. HDFCBANK, BTCUSDT"
                className="flex-1 bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
              />
              <button
                onClick={addToWatchlist}
                disabled={!newWatchSymbol.trim()}
                className="px-4 py-2 bg-accent-purple text-white text-sm rounded-lg hover:bg-accent-purple/90 transition-colors disabled:opacity-40"
              >
                Add
              </button>
            </div>

            {/* Watchlist items */}
            {watchlist.length === 0 ? (
              <div className="text-center py-6 text-text-muted text-sm">
                <p>No symbols in your watchlist yet.</p>
                <p className="mt-1 text-xs">Add symbols to get prioritized alerts.</p>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {watchlist.map((symbol) => (
                  <div
                    key={symbol}
                    className="flex items-center gap-1.5 bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 group"
                  >
                    <span className="text-sm font-mono text-text-primary">{symbol}</span>
                    <button
                      onClick={() => removeFromWatchlist(symbol)}
                      className="text-text-muted hover:text-signal-sell transition-colors text-xs opacity-0 group-hover:opacity-100"
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        {/* ── Price Alerts Section ── */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">🔔 Price Alerts</h2>
          <p className="text-xs text-text-muted">Get notified when a symbol crosses a price level.</p>

          {/* Create new price alert */}
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={newAlertSymbol}
              onChange={(e) => setNewAlertSymbol(e.target.value.toUpperCase())}
              placeholder="Symbol (e.g. BTCUSDT)"
              className="flex-1 bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
            />
            <select
              value={newAlertCondition}
              onChange={(e) => setNewAlertCondition(e.target.value as 'above' | 'below')}
              className="bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-purple"
            >
              <option value="above">Above ↑</option>
              <option value="below">Below ↓</option>
            </select>
            <input
              type="number"
              value={newAlertThreshold}
              onChange={(e) => setNewAlertThreshold(e.target.value)}
              placeholder="Price"
              className="w-32 bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
            />
            <button
              onClick={createPriceAlert}
              disabled={!newAlertSymbol.trim() || !newAlertThreshold}
              className="px-5 py-2 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-40"
            >
              Set Alert
            </button>
          </div>

          {/* Active price alerts */}
          {priceAlerts.length === 0 ? (
            <div className="text-center py-6 text-text-muted text-sm">
              No active price alerts. Set one above to get notified via Telegram.
            </div>
          ) : (
            <div className="space-y-2">
              {priceAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-center justify-between bg-bg-secondary border border-border-default rounded-lg px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <span className={`text-lg ${alert.condition === 'above' ? 'text-signal-buy' : 'text-signal-sell'}`}>
                      {alert.condition === 'above' ? '📈' : '📉'}
                    </span>
                    <div>
                      <span className="text-sm font-mono font-medium text-text-primary">
                        {alert.symbol.replace('.NS', '').replace('USDT', '')}
                      </span>
                      <span className="text-xs text-text-muted ml-2">
                        {alert.condition} {parseFloat(alert.threshold).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {alert.is_triggered && (
                      <span className="text-xs text-signal-buy font-medium">✓ Triggered</span>
                    )}
                    <button
                      onClick={() => deletePriceAlert(alert.id)}
                      className="text-text-muted hover:text-signal-sell transition-colors text-sm"
                      title="Remove alert"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
