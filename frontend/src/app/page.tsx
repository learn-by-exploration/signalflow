export default function Dashboard() {
  return (
    <main className="min-h-screen pb-12">
      {/* Market Overview Bar */}
      <div className="sticky top-0 z-10 bg-bg-secondary/90 backdrop-blur-sm border-b border-border-default px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-display font-semibold text-accent-purple">
            SignalFlow AI
          </h1>
          <div className="flex gap-4 text-sm font-mono text-text-secondary">
            <span>NIFTY 50 —</span>
            <span>BTC —</span>
            <span>EUR/USD —</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Signal Feed */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-display font-semibold">Active Signals</h2>
              <div className="flex gap-2">
                {['All', 'Stocks', 'Crypto', 'Forex'].map((filter) => (
                  <button
                    key={filter}
                    className="px-3 py-1 text-sm rounded-full border border-border-default text-text-secondary hover:border-accent-purple hover:text-accent-purple transition-colors"
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>

            {/* Placeholder signal cards */}
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="bg-bg-card border border-border-default rounded-xl p-4 hover:border-border-hover transition-colors animate-pulse"
                >
                  <div className="h-4 bg-bg-secondary rounded w-1/3 mb-3" />
                  <div className="h-3 bg-bg-secondary rounded w-2/3 mb-2" />
                  <div className="h-3 bg-bg-secondary rounded w-1/2" />
                </div>
              ))}
            </div>
          </div>

          {/* Alert Timeline */}
          <div className="space-y-4">
            <h2 className="text-xl font-display font-semibold">Recent Alerts</h2>
            <div className="bg-bg-card border border-border-default rounded-xl p-4">
              <p className="text-text-muted text-sm">
                Alerts will appear here as signals are generated.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
