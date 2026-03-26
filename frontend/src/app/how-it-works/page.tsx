'use client';

const INDICATOR_WEIGHTS = [
  { name: 'SMA Crossover', weight: 25, description: 'When short-term moving average crosses above long-term, it signals bullish momentum.' },
  { name: 'MACD', weight: 25, description: 'Moving Average Convergence Divergence tracks trend strength and direction.' },
  { name: 'RSI', weight: 20, description: 'Relative Strength Index measures overbought (>70) or oversold (<30) conditions.' },
  { name: 'Bollinger Bands', weight: 15, description: 'Price relative to volatility bands — touching lower band may signal buying opportunity.' },
  { name: 'Volume', weight: 15, description: 'Trading volume confirms the strength of price movements.' },
];

const SIGNAL_TYPES = [
  { type: 'STRONG BUY', range: '80–100%', color: '#00E676', emoji: '🟢' },
  { type: 'BUY', range: '65–79%', color: '#00E676', emoji: '🟢' },
  { type: 'HOLD', range: '36–64%', color: '#FFD740', emoji: '🟡' },
  { type: 'SELL', range: '21–35%', color: '#FF5252', emoji: '🔴' },
  { type: 'STRONG SELL', range: '0–20%', color: '#FF5252', emoji: '🔴' },
];

export default function HowItWorksPage() {
  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-10">
        {/* Hero */}
        <div>
          <h1 className="text-3xl font-display font-bold mb-3">How SignalFlow AI Works</h1>
          <p className="text-text-secondary leading-relaxed">
            SignalFlow AI combines technical analysis with AI-powered sentiment analysis
            to generate actionable trading signals. Here&apos;s the complete breakdown
            of how every signal is created.
          </p>
        </div>

        {/* Step 1: Data Collection */}
        <section className="space-y-3">
          <h2 className="text-xl font-display font-semibold flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-accent-purple/20 text-accent-purple text-sm flex items-center justify-center font-mono">1</span>
            Data Collection
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed">
            We fetch real-time OHLCV (Open, High, Low, Close, Volume) data for 31 symbols
            across three markets — Indian stocks from NSE via Yahoo Finance, cryptocurrency
            from Binance, and forex from Alpha Vantage. Data is refreshed every 30–60 seconds
            during market hours.
          </p>
        </section>

        {/* Step 2: Technical Analysis */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-semibold flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-accent-purple/20 text-accent-purple text-sm flex items-center justify-center font-mono">2</span>
            Technical Analysis (50% of score)
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed">
            Five technical indicators are computed and each produces a buy/sell/neutral signal.
            These are combined using a weighted average:
          </p>
          <div className="space-y-2">
            {INDICATOR_WEIGHTS.map((ind) => (
              <div key={ind.name} className="bg-bg-card border border-border-default rounded-lg p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-display font-medium text-text-primary">{ind.name}</span>
                  <span className="text-xs font-mono text-accent-purple">{ind.weight}%</span>
                </div>
                <div className="w-full bg-bg-secondary rounded-full h-1.5 mb-2">
                  <div className="bg-accent-purple h-full rounded-full" style={{ width: `${ind.weight}%` }} />
                </div>
                <p className="text-xs text-text-muted">{ind.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Step 3: AI Sentiment & Event Chain Analysis */}
        <section className="space-y-3">
          <h2 className="text-xl font-display font-semibold flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-accent-purple/20 text-accent-purple text-sm flex items-center justify-center font-mono">3</span>
            AI Sentiment & Event Chain Analysis (50% of score)
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed">
            Recent news articles for each symbol are fetched from financial RSS feeds
            and analyzed by Claude AI (Anthropic). The AI produces a sentiment score (0–100,
            bearish to bullish), identifies key factors, and extracts causal event chains
            — sequences of events that may propagate through markets.
          </p>
          <p className="text-text-secondary text-sm leading-relaxed">
            When event chains are detected, the AI layer contributes 50% of the final score:
            35% from event chain analysis and 15% from raw sentiment. When no causal chains
            are found, sentiment contributes 40% alongside 60% technical.
          </p>
          <div className="bg-bg-card border border-border-default rounded-lg p-4 space-y-2">
            <p className="text-xs font-display font-medium text-accent-purple mb-2">Formula</p>
            <p className="text-sm font-mono text-text-primary">
              With event chains: final = (technical × 0.50) + (event_chain × 0.35) + (sentiment × 0.15)
            </p>
            <p className="text-sm font-mono text-text-muted">
              Without chains: final = (technical × 0.60) + (sentiment × 0.40)
            </p>
          </div>
        </section>

        {/* Step 4: Signal Generation */}
        <section className="space-y-4">
          <h2 className="text-xl font-display font-semibold flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-accent-purple/20 text-accent-purple text-sm flex items-center justify-center font-mono">4</span>
            Signal Generation
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed">
            The final confidence score determines the signal type:
          </p>
          <div className="space-y-1.5">
            {SIGNAL_TYPES.map((s) => (
              <div key={s.type} className="flex items-center gap-3 bg-bg-card border border-border-default rounded-lg px-3 py-2">
                <span>{s.emoji}</span>
                <span className="text-sm font-display font-medium" style={{ color: s.color }}>{s.type}</span>
                <span className="text-xs font-mono text-text-muted ml-auto">{s.range}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Step 5: Target & Stop-Loss */}
        <section className="space-y-3">
          <h2 className="text-xl font-display font-semibold flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-accent-purple/20 text-accent-purple text-sm flex items-center justify-center font-mono">5</span>
            Target & Stop-Loss
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed">
            Every signal includes a target price and stop-loss, calculated using the
            Average True Range (ATR, 14-period). The risk-to-reward ratio is always at
            least 1:2 — meaning the potential gain is at least twice the potential loss.
          </p>
          <div className="bg-bg-card border border-border-default rounded-lg p-4 space-y-2 font-mono text-sm">
            <p className="text-signal-buy">🎯 Target = Price + (ATR × 2.0)</p>
            <p className="text-signal-sell">🛑 Stop-Loss = Price - (ATR × 1.0)</p>
          </div>
        </section>

        {/* Step 6: AI Reasoning */}
        <section className="space-y-3">
          <h2 className="text-xl font-display font-semibold flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-accent-purple/20 text-accent-purple text-sm flex items-center justify-center font-mono">6</span>
            AI Reasoning
          </h2>
          <p className="text-text-secondary text-sm leading-relaxed">
            Claude AI generates a 2–3 sentence explanation for each signal, describing which
            indicators and news drove the decision. This is written for someone with finance
            knowledge (like an M.Com) — specific enough to be useful, clear enough to learn from.
          </p>
        </section>

        {/* Disclaimer */}
        <div className="bg-signal-sell/5 border border-signal-sell/20 rounded-xl p-4">
          <p className="text-xs text-text-muted leading-relaxed">
            <strong className="text-text-secondary">Disclaimer:</strong> SignalFlow AI generates
            AI-assisted trading signals based on technical analysis and news sentiment. These
            signals are <strong>not financial advice</strong>. Past performance does not guarantee
            future results. Always do your own research and consider your risk tolerance before
            making investment decisions.
          </p>
        </div>
      </div>
    </main>
  );
}
