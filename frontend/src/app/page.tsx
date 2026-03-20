'use client';

import { MarketOverview } from '@/components/markets/MarketOverview';
import { SignalFeed } from '@/components/signals/SignalFeed';
import { AlertTimeline } from '@/components/alerts/AlertTimeline';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';
import { useSignals } from '@/hooks/useSignals';
import { useMarketData } from '@/hooks/useMarketData';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

export default function Dashboard() {
  const { signals, isLoading, error } = useSignalStore();
  const { stocks, crypto, forex, isLoading: marketsLoading } = useMarketStore();

  // Fetch initial data via REST, subscribe to real-time via WebSocket
  useSignals();
  useMarketData();
  useWebSocket();

  return (
    <main className="min-h-screen pb-12">
      {/* Market Overview Bar */}
      <ErrorBoundary>
        <MarketOverview stocks={stocks} crypto={crypto} forex={forex} isLoading={marketsLoading} />
      </ErrorBoundary>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Signal Feed */}
          <div className="lg:col-span-2">
            <ErrorBoundary>
              <SignalFeed signals={signals} isLoading={isLoading} error={error} />
            </ErrorBoundary>
          </div>

          {/* Alert Timeline */}
          <div>
            <ErrorBoundary>
              <AlertTimeline signals={signals} />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </main>
  );
}
