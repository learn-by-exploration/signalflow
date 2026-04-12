'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { Signal, SymbolTrackRecord, SignalNewsContext } from '@/lib/types';
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
import { PipCalculator } from '@/components/signals/PipCalculator';
import { TrailingStopSuggestion } from '@/components/signals/TrailingStopSuggestion';
import { CollapsibleSection } from '@/components/shared/CollapsibleSection';
import { SupplyChainContext } from '@/components/graph/SupplyChainContext';

interface SignalDetailResponse {
  data: Signal;
  news?: SignalNewsContext[];
}

export default function SignalDetailPage() {
  const params = useParams();
  const signalId = params.id as string;
  const [signal, setSignal] = useState<Signal | null>(null);
  const [newsContext, setNewsContext] = useState<SignalNewsContext[]>([]);
  const [trackRecord, setTrackRecord] = useState<SymbolTrackRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showAllIndicators, setShowAllIndicators] = useState(false);

  // Live price from market store
  const { stocks, crypto, forex } = useMarketStore();

  useEffect(() => {
    async function load() {
      try {
        const res = (await api.getSignal(signalId)) as SignalDetailResponse;
        setSignal(res.data);
        setNewsContext(res.news ?? []);
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
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-sm rounded-lg border border-accent-purple/50 text-accent-purple hover:bg-accent-purple/10 transition-colors"
          >
            Retry
          </button>
          <Link href="/" className="block text-accent-purple text-sm hover:underline">← Back to Dashboard</Link>
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

        {/* Tier lock banner — shown when free-tier quota is exhausted */}
        {signal.is_locked && (
          <div className="bg-accent-purple/10 border border-accent-purple/30 rounded-xl px-4 py-4 flex items-start gap-3">
            <span className="text-2xl">🔒</span>
            <div className="flex-1">
              <p className="text-sm font-display font-semibold text-accent-purple">
                Weekly limit reached
              </p>
              <p className="text-xs text-text-muted mt-0.5">
                Free accounts get 3 full signal views per week. Upgrade to Pro for unlimited access to AI reasoning, target prices, and stop-losses.
              </p>
              <a
                href="/pricing"
                className="inline-block mt-2 px-4 py-1.5 bg-accent-purple text-white text-xs rounded-lg font-medium hover:bg-accent-purple/90 transition-colors"
              >
                Upgrade to Pro →
              </a>
            </div>
          </div>
        )}

        {/* Earnings proximity warning for stocks */}
        {signal.market_type === 'stock' && (() => {
          const month = new Date().getMonth();
          // Earnings seasons: Jan (Q3), Apr (Q4), Jul (Q1), Oct (Q2)
          const isEarningsSeason = [0, 3, 6, 9].includes(month);
          return isEarningsSeason ? (
            <div className="bg-signal-hold/10 border border-signal-hold/20 rounded-xl px-4 py-3 flex items-start gap-2">
              <span className="text-base">📊</span>
              <div>
                <p className="text-xs font-display font-medium text-signal-hold">Earnings Season Active</p>
                <p className="text-xs text-text-muted mt-0.5">
                  Quarterly results may be upcoming for this stock. Signals near earnings dates carry higher uncertainty. Consider waiting for results before acting.
                </p>
              </div>
            </div>
          ) : null;
        })()}

        {/* Price + Target/Stop — Position 2 (most actionable info first) */}
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
                {signal.is_locked || !signal.target_price
                  ? <p className="text-sm text-accent-purple/70">🔒 Pro only</p>
                  : <p className="text-sm font-mono text-signal-buy">🎯 {formatPrice(signal.target_price, signal.market_type)}</p>
                }
              </div>
              <div>
                <p className="text-xs text-text-muted">Stop-Loss</p>
                {signal.is_locked || !signal.stop_loss
                  ? <p className="text-sm text-accent-purple/70">🔒 Pro only</p>
                  : <p className="text-sm font-mono text-signal-sell">🛑 {formatPrice(signal.stop_loss, signal.market_type)}</p>
                }
              </div>
            </div>
          </div>

          <TargetProgressBar signal={signal} livePrice={livePrice ?? undefined} />

          {signal.timeframe && (
            <p className="text-xs text-text-muted mt-2">Timeframe: {signal.timeframe}</p>
          )}
        </div>

        {/* ── Signal Analysis ── */}
        <h3 className="text-xs text-text-muted uppercase tracking-wider mt-2">Signal Analysis</h3>

        {/* Price chart */}
        {recentCloses.length >= 2 && (
          <div className="bg-bg-card border border-border-default rounded-xl p-5">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-display font-semibold">Price History</h2>
            </div>
            <p className="text-xs text-text-muted mb-2">
              <span className="text-signal-buy">green: target</span> · <span className="text-signal-sell">red: stop-loss</span>
            </p>
            <Sparkline
              data={recentCloses}
              positive={isBuyish}
              width={600}
              height={100}
              target={parseFloat(signal.target_price)}
              stopLoss={parseFloat(signal.stop_loss)}
              responsive
            />
          </div>
        )}

        {/* Technical Indicators — Full Grid */}
        <div className="bg-bg-card border border-border-default rounded-xl p-5">
          <h2 className="text-sm font-display font-semibold mb-3">Technical Indicators</h2>
          {(() => {
            const indicators = [
              rsi?.value != null && <IndicatorDetail key="rsi" label="RSI (14)" value={String(rsi.value)} signal={rsi.signal as string} description={Number(rsi.value) > 70 ? 'Overbought' : Number(rsi.value) < 30 ? 'Oversold' : 'Neutral zone'} />,
              macd?.signal != null && <IndicatorDetail key="macd" label="MACD" value={macd.signal === 'buy' ? 'Bullish' : macd.signal === 'sell' ? 'Bearish' : 'Neutral'} signal={macd.signal as string} description={macd.histogram ? `Histogram: ${macd.histogram}` : undefined} />,
              volume?.ratio != null && <IndicatorDetail key="vol" label="Volume" value={`${volume.ratio}x avg`} signal={volume.signal as string} description={Number(volume.ratio) > 1.5 ? 'High activity' : 'Normal'} />,
              bollinger?.signal != null && <IndicatorDetail key="bb" label="Bollinger" value={bollinger.signal === 'buy' ? 'Near Lower' : bollinger.signal === 'sell' ? 'Near Upper' : 'Middle'} signal={bollinger.signal as string} />,
              sma?.signal != null && <IndicatorDetail key="sma" label="SMA Cross" value={sma.signal === 'buy' ? 'Golden Cross' : sma.signal === 'sell' ? 'Death Cross' : 'No Cross'} signal={sma.signal as string} />,
            ].filter(Boolean);
            const visibleOnMobile = showAllIndicators ? indicators : indicators.slice(0, 2);
            return (
              <>
                {/* Mobile: show limited, Desktop: show all */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:hidden">
                  {visibleOnMobile.map((ind) => ind)}
                </div>
                <div className="hidden sm:grid sm:grid-cols-3 gap-3">
                  {indicators.map((ind) => ind)}
                </div>
                {!showAllIndicators && indicators.length > 2 && (
                  <button
                    type="button"
                    onClick={() => setShowAllIndicators(true)}
                    className="mt-2 text-xs text-accent-purple hover:underline sm:hidden"
                  >
                    Show all {indicators.length} indicators
                  </button>
                )}
              </>
            );
          })()}
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
              {/* News sources */}
              {sentimentData?.source_count != null && (
                <p className="mt-2 text-xs text-text-muted">
                  Based on {String(sentimentData.source_count)} news article{Number(sentimentData.source_count) !== 1 ? 's' : ''} analyzed
                </p>
              )}
              {Array.isArray(sentimentData?.sources) && (sentimentData.sources as { title: string; url: string }[]).length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-text-muted">Sources:</p>
                  {(sentimentData.sources as { title: string; url: string }[]).slice(0, 3).map((src, i) => (
                    <a
                      key={i}
                      href={src.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-accent-purple hover:underline truncate"
                    >
                      {src.title || src.url}
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Context & History ── */}
        <h3 className="text-xs text-text-muted uppercase tracking-wider mt-2">Context & History</h3>

        {/* News Context — linked news events that drove this signal */}
        {newsContext.length > 0 && (
          <CollapsibleSection title={`📰 News Context (${newsContext.length})`} storageKey={`news-${signalId}`} defaultOpen={false}>
            <div className="space-y-2">
              {newsContext.map((item) => (
                <div key={item.id} className="flex items-start gap-2 py-1.5 border-b border-border-default last:border-b-0">
                  <span className={`shrink-0 mt-0.5 text-xs ${
                    item.sentiment_direction === 'bullish' ? 'text-signal-buy' :
                    item.sentiment_direction === 'bearish' ? 'text-signal-sell' :
                    'text-text-muted'
                  }`}>
                    {item.sentiment_direction === 'bullish' ? '📈' :
                     item.sentiment_direction === 'bearish' ? '📉' : '➡️'}
                  </span>
                  <div className="min-w-0 flex-1">
                    {item.source_url ? (
                      <a href={item.source_url} target="_blank" rel="noopener noreferrer"
                         className="text-xs text-text-primary hover:text-accent-purple transition-colors leading-snug block">
                        {item.headline}
                      </a>
                    ) : (
                      <p className="text-xs text-text-primary leading-snug">{item.headline}</p>
                    )}
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-text-muted">
                      {item.source && <span>{item.source}</span>}
                      {item.event_category && (
                        <span className="px-1 py-0.5 rounded bg-accent-purple/10 text-accent-purple">
                          {item.event_category}
                        </span>
                      )}
                      {item.published_at && (
                        <span>{new Date(item.published_at).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CollapsibleSection>
        )}

        {/* Track Record */}
        {trackRecord && trackRecord.total_signals_30d > 0 && (
          <CollapsibleSection title="📊 Symbol Track Record (30d)" storageKey={`track-${signalId}`} defaultOpen={false}>
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
          </CollapsibleSection>
        )}

        {/* ── Supply Chain Context ── */}
        <CollapsibleSection title="🔗 Supply Chain Context" storageKey={`supply-chain-${signalId}`} defaultOpen={false}>
          <SupplyChainContext symbol={signal.symbol} marketType={signal.market_type} />
        </CollapsibleSection>

        {/* ── Trading Tools ── */}
        <h3 className="text-xs text-text-muted uppercase tracking-wider mt-2">Trading Tools</h3>

        <CollapsibleSection title="🧮 Risk Calculator" storageKey={`risk-${signalId}`} defaultOpen={false}>
          <RiskCalculator signal={signal} />
        </CollapsibleSection>

        {signal.market_type === 'forex' && (
          <CollapsibleSection title="💱 Pip Calculator" storageKey={`pip-${signalId}`} defaultOpen={false}>
            <PipCalculator signal={signal} />
          </CollapsibleSection>
        )}

        {(signal.signal_type.includes('BUY') || signal.signal_type.includes('SELL')) && signal.signal_type !== 'HOLD' && (
          <CollapsibleSection title="📏 Trailing Stop Suggestion" storageKey={`trail-${signalId}`} defaultOpen={false}>
            <TrailingStopSuggestion signal={signal} livePrice={livePrice ?? undefined} />
          </CollapsibleSection>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between">
          <Link href="/" className="text-xs text-accent-purple hover:underline">← Back to Dashboard</Link>
          <ShareButton signalId={signal.id} />
        </div>

        {/* Disclaimer */}
        <p className="text-xs text-text-muted text-center">
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
      <p className="text-xs text-text-muted uppercase mb-1">
        <IndicatorTooltip term={label}>{label}</IndicatorTooltip>
      </p>
      <p className={`text-sm font-mono font-semibold ${colorClass}`}>{value}</p>
      {description && <p className="text-xs text-text-muted mt-0.5">{description}</p>}
    </div>
  );
}
