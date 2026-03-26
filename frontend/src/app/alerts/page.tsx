'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { AlertConfig, PriceAlert, MarketType, SignalType } from '@/lib/types';
import { useToast } from '@/components/shared/Toast';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { SymbolAutocomplete } from '@/components/shared/SymbolAutocomplete';

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
  const [loading, setLoading] = useState(true);

  // Alert config state
  const [config, setConfig] = useState<AlertConfig | null>(null);
  const [markets, setMarkets] = useState<MarketType[]>(['stock', 'crypto', 'forex']);
  const [minConfidence, setMinConfidence] = useState(60);
  const [signalTypes, setSignalTypes] = useState<SignalType[]>(['STRONG_BUY', 'BUY', 'SELL', 'STRONG_SELL']);
  const [quietHoursEnabled, setQuietHoursEnabled] = useState(false);
  const [quietStart, setQuietStart] = useState('23:00');
  const [quietEnd, setQuietEnd] = useState('07:00');

  // Price alerts state
  const [priceAlerts, setPriceAlerts] = useState<PriceAlert[]>([]);
  const [newAlertSymbol, setNewAlertSymbol] = useState('');
  const [newAlertCondition, setNewAlertCondition] = useState<'above' | 'below'>('above');
  const [newAlertThreshold, setNewAlertThreshold] = useState('');

  // Watchlist state
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [newWatchSymbol, setNewWatchSymbol] = useState('');

  // Per-market confidence overrides
  const [marketConfidence, setMarketConfidence] = useState<Record<string, number>>({});
  const [showPerMarket, setShowPerMarket] = useState(false);

  useEffect(() => {
    async function loadAll() {
      try {
        const [configRes, alertsRes, watchRes] = await Promise.allSettled([
          api.getAlertConfig() as Promise<{ data: AlertConfig }>,
          api.getPriceAlerts() as Promise<{ data: PriceAlert[] }>,
          api.getWatchlist() as Promise<{ data: { watchlist: string[] } }>,
        ]);

        if (configRes.status === 'fulfilled' && configRes.value?.data) {
          const c = configRes.value.data;
          setConfig(c);
          setMarkets(c.markets);
          setMinConfidence(c.min_confidence);
          setSignalTypes(c.signal_types);
          if (c.quiet_hours?.start && c.quiet_hours?.end) {
            setQuietHoursEnabled(true);
            setQuietStart(c.quiet_hours.start);
            setQuietEnd(c.quiet_hours.end);
          }
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
  }, []);

  // ── Alert Config Actions ──
  async function saveConfig() {
    const payload: Record<string, unknown> = {
      markets,
      min_confidence: minConfidence,
      signal_types: signalTypes,
      quiet_hours: quietHoursEnabled ? { start: quietStart, end: quietEnd } : null,
    };
    try {
      if (config?.id) {
        await api.updateAlertConfig(config.id, payload);
      } else {
        await api.createAlertConfig(payload);
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
      await api.updateWatchlist(symbol, 'add');
      setWatchlist((prev) => [...prev, symbol]);
      setNewWatchSymbol('');
      toast(`${symbol} added to watchlist`, 'success');
    } catch {
      toast('Failed to update watchlist', 'error');
    }
  }

  async function removeFromWatchlist(symbol: string) {
    try {
      await api.updateWatchlist(symbol, 'remove');
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

              {/* Per-market confidence overrides */}
              <button
                onClick={() => setShowPerMarket(!showPerMarket)}
                className="text-xs text-accent-purple hover:underline mt-2"
              >
                {showPerMarket ? '▼ Hide' : '▶ Per-market'} confidence overrides
              </button>
              {showPerMarket && (
                <div className="mt-2 space-y-2 pl-2 border-l-2 border-accent-purple/20">
                  {MARKET_OPTIONS.filter(m => markets.includes(m.value)).map((opt) => (
                    <div key={opt.value} className="flex items-center gap-3">
                      <span className="text-xs text-text-secondary w-16">{opt.icon} {opt.label}</span>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        step={5}
                        value={marketConfidence[opt.value] ?? minConfidence}
                        onChange={(e) => setMarketConfidence(prev => ({ ...prev, [opt.value]: Number(e.target.value) }))}
                        className="flex-1 accent-accent-purple"
                        aria-label={`${opt.label} minimum confidence`}
                      />
                      <span className="text-xs font-mono text-accent-purple w-10 text-right">
                        {marketConfidence[opt.value] ?? minConfidence}%
                      </span>
                    </div>
                  ))}
                  <p className="text-[10px] text-text-muted">Override the global minimum for specific markets. e.g. require 80% for stocks but 60% for crypto.</p>
                </div>
              )}
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

            {/* Quiet Hours */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm text-text-secondary">🌙 Quiet Hours</label>
                <button
                  onClick={() => setQuietHoursEnabled(!quietHoursEnabled)}
                  className={`relative w-10 h-5 rounded-full transition-colors ${
                    quietHoursEnabled ? 'bg-accent-purple' : 'bg-bg-secondary border border-border-default'
                  }`}
                  aria-pressed={quietHoursEnabled}
                  aria-label="Toggle quiet hours"
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      quietHoursEnabled ? 'translate-x-5' : ''
                    }`}
                  />
                </button>
              </div>
              <p className="text-xs text-text-muted mb-2">Suppress alerts during sleep hours (IST)</p>
              {quietHoursEnabled && (
                <div className="flex items-center gap-3">
                  <div className="flex-1">
                    <label className="text-xs text-text-muted block mb-1">From</label>
                    <input
                      type="time"
                      value={quietStart}
                      onChange={(e) => setQuietStart(e.target.value)}
                      className="w-full bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:border-accent-purple"
                    />
                  </div>
                  <span className="text-text-muted mt-4">→</span>
                  <div className="flex-1">
                    <label className="text-xs text-text-muted block mb-1">To</label>
                    <input
                      type="time"
                      value={quietEnd}
                      onChange={(e) => setQuietEnd(e.target.value)}
                      className="w-full bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:border-accent-purple"
                    />
                  </div>
                </div>
              )}
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
              <SymbolAutocomplete
                value={newWatchSymbol}
                onChange={setNewWatchSymbol}
                onSubmit={addToWatchlist}
                placeholder="e.g. HDFCBANK.NS, BTCUSDT"
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
                      className="text-text-muted hover:text-signal-sell transition-colors text-xs sm:opacity-0 sm:group-hover:opacity-100"
                      title="Remove"
                      aria-label={`Remove ${symbol} from watchlist`}
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
            <SymbolAutocomplete
              value={newAlertSymbol}
              onChange={setNewAlertSymbol}
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

        {/* Cross-link to Settings */}
        <div className="text-center text-xs text-text-muted pt-2">
          <Link href="/settings" className="text-accent-purple hover:underline">
            🎨 Display preferences, theme & account settings →
          </Link>
        </div>
      </div>
    </main>
  );
}
