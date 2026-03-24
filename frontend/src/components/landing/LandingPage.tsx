import Link from 'next/link';

const FEATURES = [
  {
    icon: '📊',
    title: 'AI-Powered Analysis',
    description: 'Claude AI analyzes technical indicators and market sentiment to generate actionable signals across stocks, crypto, and forex.',
  },
  {
    icon: '⚡',
    title: 'Real-Time Signals',
    description: 'Get instant notifications via Telegram and dashboard when new high-confidence trading opportunities are detected.',
  },
  {
    icon: '🎯',
    title: 'Clear Entry & Exit',
    description: 'Every signal includes entry price, target, stop-loss, and timeframe. No guesswork — just clear, actionable levels.',
  },
  {
    icon: '🧠',
    title: 'AI Reasoning',
    description: 'Understand WHY each signal was generated. Transparent explanations help you learn and build confidence.',
  },
  {
    icon: '📈',
    title: 'Full Track Record',
    description: 'Complete history of every signal with outcomes. See win rates, average returns, and accuracy by market.',
  },
  {
    icon: '🔔',
    title: 'Smart Alerts',
    description: 'Configure alerts by market, confidence level, and quiet hours. Get morning briefs and evening wraps on Telegram.',
  },
];

const MARKETS = [
  { name: 'Indian Stocks', symbols: 'NIFTY 50 · HDFCBANK · TCS · RELIANCE', icon: '🇮🇳' },
  { name: 'Cryptocurrency', symbols: 'BTC · ETH · SOL · Top 10 by market cap', icon: '₿' },
  { name: 'Forex', symbols: 'USD/INR · EUR/USD · GBP/JPY · Major pairs', icon: '💱' },
];

const STATS = [
  { value: '31', label: 'Symbols Tracked' },
  { value: '3', label: 'Markets Covered' },
  { value: '24/7', label: 'Monitoring' },
  { value: '1:2', label: 'Min Risk:Reward' },
];

const STEPS = [
  { step: '01', title: 'Data Ingestion', desc: 'Real-time price feeds from NSE, Binance, and forex markets every 30–60 seconds.' },
  { step: '02', title: 'Technical Analysis', desc: 'RSI, MACD, Bollinger Bands, volume, and SMA crossovers are calculated automatically.' },
  { step: '03', title: 'AI Sentiment', desc: 'Claude AI analyzes news and market context to score sentiment from 0 to 100.' },
  { step: '04', title: 'Signal Delivery', desc: 'Signals with entry, target, and stop-loss are delivered to your dashboard and Telegram.' },
];

export function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-accent-purple/[0.12] rounded-full blur-[120px]" />
          <div className="absolute top-40 left-0 w-[400px] h-[400px] bg-signal-buy/[0.06] rounded-full blur-[100px]" />
          <div className="absolute top-60 right-0 w-[300px] h-[300px] bg-signal-sell/[0.05] rounded-full blur-[80px]" />
        </div>

        <div className="relative max-w-5xl mx-auto px-4 pt-20 pb-16 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-accent-purple/10 border border-accent-purple/20 rounded-full px-4 py-1.5 mb-8 landing-fade-in" style={{ animationDelay: '0ms' }}>
            <span className="w-2 h-2 bg-signal-buy rounded-full animate-pulse motion-reduce:animate-none" aria-hidden="true" />
            <span className="text-xs font-mono text-accent-purple">AI-Powered Market Analysis</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-display font-bold leading-tight mb-6 landing-fade-in" style={{ animationDelay: '100ms' }}>
            <span className="text-text-primary">Turn Market Noise Into</span>
            <br />
            <span className="bg-gradient-to-r from-accent-purple via-signal-buy to-accent-purple bg-clip-text text-transparent">
              Clear Trading Signals
            </span>
          </h1>

          {/* Subheadline */}
          <p className="max-w-2xl mx-auto text-lg text-text-secondary mb-10 leading-relaxed landing-fade-in" style={{ animationDelay: '200ms' }}>
            AI analyzes technical indicators and market sentiment across Indian stocks, crypto, and forex —
            delivering actionable signals with entry, target, and stop-loss levels you can trust.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-4 landing-fade-in" style={{ animationDelay: '300ms' }}>
            <Link
              href="/auth/signin"
              className="px-8 py-3.5 bg-accent-purple text-white text-sm font-semibold rounded-xl hover:bg-accent-purple/90 transition-all shadow-lg shadow-accent-purple/25"
            >
              Start Exploring — Free
            </Link>
            <Link
              href="/how-it-works"
              className="px-8 py-3.5 border border-border-hover text-text-secondary text-sm font-medium rounded-xl hover:text-text-primary hover:border-accent-purple/30 transition-colors"
            >
              How It Works
            </Link>
          </div>
          <p className="text-xs text-text-muted landing-fade-in" style={{ animationDelay: '400ms' }}>
            No credit card required · AI-generated analysis, not financial advice
          </p>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-y border-border-default bg-bg-secondary/50">
        <div className="max-w-5xl mx-auto px-4 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl md:text-3xl font-display font-bold text-accent-purple">{stat.value}</div>
                <div className="text-xs text-text-muted mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Signal Preview */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-display font-bold text-text-primary mb-3">
            Every Signal, One Glance
          </h2>
          <p className="text-text-secondary max-w-xl mx-auto">
            Clear, actionable signals with AI reasoning you can understand and learn from.
          </p>
        </div>

        {/* Mock Signal Card */}
        <div className="max-w-md mx-auto bg-bg-card border border-border-default rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl" aria-hidden="true">🟢</span>
              <div>
                <div className="font-display font-bold text-text-primary">HDFCBANK</div>
                <div className="text-xs text-text-muted font-mono">NSE · Indian Stock</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xs font-mono text-signal-buy font-semibold">STRONGLY BULLISH</div>
              <div className="text-xs text-text-muted">92% confidence</div>
            </div>
          </div>

          {/* Confidence bar */}
          <div className="w-full bg-border-default rounded-full h-1.5" role="progressbar" aria-valuenow={92} aria-valuemin={0} aria-valuemax={100} aria-label="Signal confidence: 92%">
            <div className="bg-signal-buy h-1.5 rounded-full" style={{ width: '92%' }} />
          </div>

          {/* Price levels */}
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-bg-secondary/50 rounded-lg p-2">
              <div className="text-xs text-text-muted">Entry</div>
              <div className="text-sm font-mono text-text-primary">₹1,678.90</div>
            </div>
            <div className="bg-bg-secondary/50 rounded-lg p-2">
              <div className="text-xs text-signal-buy">Target</div>
              <div className="text-sm font-mono text-signal-buy">₹1,780.00</div>
            </div>
            <div className="bg-bg-secondary/50 rounded-lg p-2">
              <div className="text-xs text-signal-sell">Stop-Loss</div>
              <div className="text-sm font-mono text-signal-sell">₹1,630.00</div>
            </div>
          </div>

          {/* AI Reasoning */}
          <div className="bg-accent-purple/5 border border-accent-purple/10 rounded-lg p-3">
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-xs" aria-hidden="true">🤖</span>
              <span className="text-xs font-mono text-accent-purple">AI REASONING</span>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              Credit growth accelerating with NIM expansion confirmed in Q3 results.
              RSI at 62.7 with strong MACD bullish crossover. High volume confirms institutional buying interest.
            </p>
          </div>

          <div className="text-center">
            <span className="text-xs text-text-muted font-mono">Timeframe: 2–4 weeks</span>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="bg-bg-secondary/30 border-y border-border-default">
        <div className="max-w-5xl mx-auto px-4 py-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-display font-bold text-text-primary mb-3">
              Everything You Need to Trade Confidently
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              AI-powered tools designed to help you make informed trading decisions.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES.map((feature, i) => (
              <div
                key={feature.title}
                className="bg-bg-card border border-border-default rounded-xl p-6 hover:border-accent-purple/20 transition-colors landing-fade-in-up"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <span className="text-2xl mb-3 block" aria-hidden="true">{feature.icon}</span>
                <h3 className="font-display font-semibold text-text-primary mb-2">{feature.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Markets Section */}
      <section className="max-w-5xl mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-display font-bold text-text-primary mb-3">
            Three Markets, One Platform
          </h2>
          <p className="text-text-secondary">
            Comprehensive coverage across the markets that matter.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {MARKETS.map((market) => (
            <div
              key={market.name}
              className="bg-bg-card border border-border-default rounded-xl p-6 text-center hover:border-accent-purple/20 transition-colors"
            >
              <span className="text-3xl mb-3 block" aria-hidden="true">{market.icon}</span>
              <h3 className="font-display font-semibold text-text-primary mb-1">{market.name}</h3>
              <p className="text-xs text-text-muted font-mono">{market.symbols}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-bg-secondary/30 border-y border-border-default">
        <div className="max-w-5xl mx-auto px-4 py-20">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-display font-bold text-text-primary mb-3">
              How It Works
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {STEPS.map((item, i) => (
              <div key={item.step} className="text-center landing-fade-in-up" style={{ animationDelay: `${i * 100}ms` }}>
                <div className="w-10 h-10 rounded-full bg-accent-purple/10 border border-accent-purple/20 flex items-center justify-center mx-auto mb-3">
                  <span className="text-xs font-mono font-bold text-accent-purple">{item.step}</span>
                </div>
                <h3 className="font-display font-semibold text-text-primary text-sm mb-1">{item.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="max-w-5xl mx-auto px-4 py-20 text-center">
        <h2 className="text-2xl md:text-3xl font-display font-bold text-text-primary mb-4">
          Ready to Trade Smarter?
        </h2>
        <p className="text-text-secondary mb-8 max-w-lg mx-auto">
          Join SignalFlow AI and turn market noise into clear, actionable trading signals.
        </p>
        <Link
          href="/auth/signin"
          className="inline-block px-8 py-3.5 bg-accent-purple text-white text-sm font-semibold rounded-xl hover:bg-accent-purple/90 transition-all shadow-lg shadow-accent-purple/25"
        >
          Start Exploring — Free
        </Link>
        <p className="text-xs text-text-muted mt-3">No credit card required</p>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-default bg-bg-secondary/50">
        <div className="max-w-5xl mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-accent-purple">SignalFlow</span>
              <span className="text-xs font-mono text-text-muted bg-accent-purple/10 px-1.5 py-0.5 rounded">AI</span>
            </div>
            <div className="flex items-center gap-6 text-xs text-text-muted">
              <Link href="/privacy" className="hover:text-text-secondary transition-colors">Privacy</Link>
              <Link href="/terms" className="hover:text-text-secondary transition-colors">Terms</Link>
              <Link href="/contact" className="hover:text-text-secondary transition-colors">Contact</Link>
              <Link href="/how-it-works" className="hover:text-text-secondary transition-colors">How It Works</Link>
            </div>
          </div>
          <div className="mt-6 text-center text-xs text-text-muted leading-relaxed">
            <p>
              <span aria-hidden="true">⚠️</span> SignalFlow AI provides AI-generated analysis for educational purposes only. This is not financial advice.
            </p>
            <p className="mt-1">Always do your own research and consult a qualified financial advisor before making investment decisions.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
