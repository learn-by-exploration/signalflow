'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { Signal, SymbolTrackRecord } from '@/lib/types';
import { formatPrice, formatPercent, formatDate, shortSymbol, formatTimeRemaining } from '@/utils/formatters';
import { SIGNAL_COLORS, MARKET_LABELS } from '@/lib/constants';
import { useMarketStore } from '@/store/marketStore';
import { SignalBadge } from '@/components/signals/SignalBadge';
import { ConfidenceGauge } from '@/components/signals/ConfidenceGauge';
import { TargetProgressBar } from '@/components/signals/TargetProgressBar';
import { RiskCalculator } from '@/components/signals/RiskCalculator';
import { ShareButton } from '@/components/signals/ShareButton';
import { Sparkline } from '@/components/markets/Sparkline';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { IndicatorTooltip } from '@/components/shared/IndicatorTooltip';
import { CandlestickChart } from '@/components/charts/CandlestickChart';

interface SignalDetailResponse {
  data: Signal;
}

export default function SignalDetailPage() {
  const params = useParams();
  const signalId = params.id as string;
  const [signal, setSignal] = useState<Signal | null>(null);
  const [trackRecord, setTrackRecord] = useState<SymbolTrackRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [chartView, setChartView] = useState<'line' | 'candle'>('candle');

  // Live price from market store
  const { stocks, crypto, forex } = useMarketStore();

  useEffect(() => {
    async function load() {
      try {
        const res = (await api.getSignal(signalId)) as SignalDetailResponse;
        setSignal(res.data);
        // Fetch track record
        try {
          const tr = await api.getSymbolTrackRecord(res.data.symbol);
          const data = (tr as { data?: SymbolTrackRecord })?.data ?? (tr as SymbolTrackRecord);
          if (data && typeof data.total_signals_30d === 'number') setTrackRecord(data);
        } catch { /* non-critical */ }
      } catch {
        setError('Signal not found.');
      } finally {
        setLoading(false);
      }
    }
    if (signalId) load();
  }, [signalId]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </main>
    );
  }

  if (error || !signal) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-3">
          <p className="text-3xl">🔍</p>
          <p className="text-text-secondary">{error ?? 'Signal not found.'}</p>
          <Link href="/" className="text-accent-purple text-sm hover:underline">← Back to Dashboard</Link>
        </div>
      </main>
    );
  }

  const color = SIGNAL_COLORS[signal.signal_type];
  const technicalData = signal.technical_data as Record<string, Record<string, unknown>>;
  const rsi = technicalData?.rsi;
  const macd = technicalData?.macd;
  const volume = technicalData?.volume;
  const bollinger = technicalData?.bollinger;
  const sma = technicalData?.sma;
  const recentCloses = (signal.technical_data?.recent_closes ?? []) as number[];
  const isBuyish = signal.signal_type.includes('BUY');

  // Sentiment
  const sentimentData = signal.sentiment_data as Record<string, unknown> | null;
  const marketImpact = sentimentData?.market_impact as string | undefined;
  const sentimentScore = sentimentData?.sentiment_score as number | undefined;
  const keyFactors = sentimentData?.key_factors as string[] | undefined;

  // Live price
  const normalizedSymbol = shortSymbol(signal.symbol);
  const allSnapshots = [...stocks, ...crypto, ...forex];
  const liveSnapshot = allSnapshots.find((s) => shortSymbol(s.symbol) === normalizedSymbol);
  const signalPrice = parseFloat(signal.current_price);
  const livePrice = liveSnapshot ? parseFloat(String(liveSnapshot.price)) : null;
  const priceChangePct = livePrice ? ((livePrice - signalPrice) / signalPrice) * 100 : null;

  // Expiry / age
  const expiresAt = signal.expires_at ? new Date(signal.expires_at).getTime() : null;
  const timeRemaining = expiresAt ? expiresAt - Date.now() : null;
  const ageHours = (Date.now() - new Date(signal.created_at).getTime()) / 3600000;
  const ageDays = Math.floor(ageHours / 24);

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
        {/* Back link */}
        <Link href="/" className="text-xs text-accent-purple hover:underline">← Back to Dashboard</Link>

        {/* Header */}
        <div className="flex items-center gap-4">
          <ConfidenceGauge confidence={signal.confidence} signalType={signal.signal_type} size={72} />
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-display font-bold text-text-primary">
                {shortSymbol(signal.symbol)}
              </h1>
              <SignalBadge signalType={signal.signal_type} />
            </div>
            <p className="text-sm text-text-muted">
              {MARKET_LABELS[signal.market_type]} · {formatDate(signal.created_at)}
              {timeRemaining != null && timeRemaining > 0 && (
                <span className="ml-2 text-text-muted">· ⏱ {formatTimeRemaining(timeRemaining)} left</span>
              )}
            </p>
            {ageHours > 48 && (
              <p className="text-xs mt-1 text-signal-hold">
                ⚠️ Signal is {ageDays}d old{ageHours > 120 ? ' — expiring soon' : ''}
              </p>
            )}
          </div>
        </div>

        {/* Price + Target/Stop */}
        <div className="bg-bg-card border border-border-default rounded-xl p-5" style={{ borderLeftColor: color, borderLeftWidth: 3 }}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs text-text-muted uppercase mb-1">Entry Price</p>
              <p className="text-xl font-mono text-text-primary">
                {formatPrice(signal.current_price, signal.market_type)}
              </p>
              {livePrice != null && priceChangePct != null && Math.abs(priceChangePct) >= 0.01 && (
                <p className={`text-sm font-mono mt-0.5 ${priceChangePct >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                  → {formatPrice(String(livePrice), signal.market_type)} ({priceChangePct >= 0 ? '+' : ''}{priceChangePct.toFixed(2)}%)
                </p>
              )}
            </div>
            <div className="text-right space-y-1">
              <div>
                <p className="text-xs text-text-muted">Target</p>
                <p className="text-sm font-mono text-signal-buy">🎯 {formatPrice(signal.target_price, signal.market_type)}</p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Stop-Loss</p>
                <p className="text-sm font-mono text-signal-sell">🛑 {formatPrice(signal.stop_loss, signal.market_type)}</p>
              </div>
            </div>
          </div>

          <TargetProgressBar signal={signal} livePrice={livePrice ?? undefined} />

          {signal.timeframe && (
            <p className="text-xs text-text-muted mt-2">Timeframe: {signal.timeframe}</p>
          )}
        </div>

        {/* Price chart */}
        {recentCloses.length >= 2 && (
          <div className="bg-bg-card border border-border-default rounded-xl p-5">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-display font-semibold">Price History</h2>
              <div className="flex gap-1">
                <button
                  onClick={() => setChartView('candle')}
                  className={`px-2 py-1 text-[10px] rounded border transition-colors ${
                    chartView === 'candle'
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-muted'
                  }`}
                >
                  Candlestick
                </button>
                <button
                  onClick={() => setChartView('line')}
                  className={`px-2 py-1 text-[10px] rounded border transition-colors ${
                    chartView === 'line'
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-muted'
                  }`}
                >
                  Line
                </button>
              </div>
            </div>
            <p className="text-[10px] text-text-muted mb-2">
              <span className="text-signal-buy">green: target</span> · <span className="text-signal-sell">red: stop-loss</span>
            </p>
            {chartView === 'candle' ? (
              <CandlestickChart
                data={recentCloses.map((close, i) => {
                  const d = new Date();
                  d.setDate(d.getDate() - (recentCloses.length - 1 - i));
                  const open = i > 0 ? recentCloses[i - 1] : close;
                  const high = Math.max(open, close) * (1 + Math.random() * 0.01);
                  const low = Math.min(open, close) * (1 - Math.random() * 0.01);
                  return {
                    time: d.toISOString().split('T')[0],
                    open,
                    high,
                    low,
                    close,
                  };
                })}
                targetPrice={parseFloat(signal.target_price)}
                stopLoss={parseFloat(signal.stop_loss)}
                height={250}
              />
            ) : (
              <Sparkline
                data={recentCloses}
                positive={isBuyish}
                width={600}
                height={100}
                target={parseFloat(signal.target_price)}
                stopLoss={parseFloat(signal.stop_loss)}
                responsive
              />
            )}
          </div>
        )}

        {/* Technical Indicators — Full Grid */}
        <div className="bg-bg-card border border-border-default rounded-xl p-5">
          <h2 className="text-sm font-display font-semibold mb-3">Technical Indicators</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {rsi?.value != null && (
              <IndicatorDetail label="RSI (14)" value={String(rsi.value)} signal={rsi.signal as string} description={Number(rsi.value) > 70 ? 'Overbought' : Number(rsi.value) < 30 ? 'Oversold' : 'Neutral zone'} />
            )}
            {macd?.signal != null && (
              <IndicatorDetail label="MACD" value={macd.signal === 'buy' ? 'Bullish' : macd.signal === 'sell' ? 'Bearish' : 'Neutral'} signal={macd.signal as string} description={macd.histogram ? `Histogram: ${macd.histogram}` : undefined} />
            )}
            {volume?.ratio != null && (
              <IndicatorDetail label="Volume" value={`${volume.ratio}x avg`} signal={volume.signal as string} description={Number(volume.ratio) > 1.5 ? 'High activity' : 'Normal'} />
            )}
            {bollinger?.signal != null && (
              <IndicatorDetail label="Bollinger" value={bollinger.signal === 'buy' ? 'Near Lower' : bollinger.signal === 'sell' ? 'Near Upper' : 'Middle'} signal={bollinger.signal as string} />
            )}
            {sma?.signal != null && (
              <IndicatorDetail label="SMA Cross" value={sma.signal === 'buy' ? 'Golden Cross' : sma.signal === 'sell' ? 'Death Cross' : 'No Cross'} signal={sma.signal as string} />
            )}
          </div>
        </div>

        {/* AI Reasoning — Full */}
        <div className="bg-bg-card border border-border-default rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-base">🤖</span>
            <h2 className="text-sm font-display font-semibold">AI Reasoning</h2>
          </div>
          <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{signal.ai_reasoning}</p>
          {/* Sentiment details */}
          {sentimentData && (
            <div className="mt-4 pt-3 border-t border-border-default">
              <p className="text-xs text-text-muted mb-2">Sentiment Analysis</p>
              <div className="flex items-center gap-3 text-xs">
                {marketImpact && (
                  <span className={`font-mono ${marketImpact === 'positive' ? 'text-signal-buy' : marketImpact === 'negative' ? 'text-signal-sell' : 'text-signal-hold'}`}>
                    {marketImpact === 'positive' ? '📈 Bullish' : marketImpact === 'negative' ? '📉 Bearish' : '➡️ Neutral'}
                    {sentimentScore != null && ` (${sentimentScore}/100)`}
                  </span>
                )}
              </div>
              {keyFactors && keyFactors.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {keyFactors.map((f, i) => (
                    <li key={i} className="text-xs text-text-secondary">• {f}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Risk Calculator */}
        <div className="bg-bg-card border border-border-default rounded-xl p-5">
          <RiskCalculator signal={signal} />
        </div>

        {/* Track Record */}
        {trackRecord && trackRecord.total_signals_30d > 0 && (
          <div className="bg-bg-card border border-border-default rounded-xl p-5">
            <h2 className="text-sm font-display font-semibold mb-2">📊 Symbol Track Record (30d)</h2>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 text-center">
              <div>
                <p className="text-lg font-mono text-text-primary">{trackRecord.total_signals_30d}</p>
                <p className="text-xs text-text-muted">Total</p>
              </div>
              <div>
                <p className="text-lg font-mono text-signal-buy">{trackRecord.hit_target}</p>
                <p className="text-xs text-text-muted">Hit Target</p>
              </div>
              <div>
                <p className="text-lg font-mono text-signal-sell">{trackRecord.hit_stop}</p>
                <p className="text-xs text-text-muted">Hit Stop</p>
              </div>
              <div>
                <p className={`text-lg font-mono ${trackRecord.win_rate >= 60 ? 'text-signal-buy' : trackRecord.win_rate >= 40 ? 'text-signal-hold' : 'text-signal-sell'}`}>
                  {trackRecord.win_rate.toFixed(1)}%
                </p>
                <p className="text-xs text-text-muted">Win Rate</p>
              </div>
              <div>
                <p className={`text-lg font-mono ${trackRecord.avg_return_pct >= 0 ? 'text-signal-buy' : 'text-signal-sell'}`}>
                  {trackRecord.avg_return_pct >= 0 ? '+' : ''}{trackRecord.avg_return_pct.toFixed(2)}%
                </p>
                <p className="text-xs text-text-muted">Avg Return</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between">
          <Link href="/" className="text-xs text-accent-purple hover:underline">← Back to Dashboard</Link>
          <ShareButton signalId={signal.id} />
        </div>

        {/* Disclaimer */}
        <p className="text-[10px] text-text-muted text-center">
          This is AI-generated analysis, not financial advice. Always do your own research before trading.
        </p>
      </div>
    </main>
  );
}

/** Detailed indicator card for the full grid */
function IndicatorDetail({ label, value, signal, description }: {
  label: string;
  value: string;
  signal: string;
  description?: string;
}) {
  const colorClass = signal === 'buy' ? 'text-signal-buy' : signal === 'sell' ? 'text-signal-sell' : 'text-signal-hold';
  return (
    <div className="bg-bg-secondary rounded-lg p-3">
      <p className="text-[10px] text-text-muted uppercase mb-1">
        <IndicatorTooltip term={label}>{label}</IndicatorTooltip>
      </p>
      <p className={`text-sm font-mono font-semibold ${colorClass}`}>{value}</p>
      {description && <p className="text-[10px] text-text-muted mt-0.5">{description}</p>}
    </div>
  );
}
