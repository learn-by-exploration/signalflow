'use client';

import { MarketOverview } from '@/components/markets/MarketOverview';
import { SignalFeed } from '@/components/signals/SignalFeed';
import { WinRateCard } from '@/components/signals/WinRateCard';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';
import { useSignals } from '@/hooks/useSignals';
import { useMarketData } from '@/hooks/useMarketData';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { WelcomeModal } from '@/components/shared/WelcomeModal';
import { GuidedTour } from '@/components/shared/GuidedTour';
import { useEffect } from 'react';

export default function Dashboard() {
  const { signals, isLoading, error } = useSignalStore();
  const { stocks, crypto, forex, isLoading: marketsLoading, lastUpdated } = useMarketStore();
  const resetUnseen = useSignalStore((s) => s.resetUnseen);

  // Fetch initial data via REST, subscribe to real-time via WebSocket
  useSignals();
  useMarketData();
  useWebSocket();

  // Reset notification badge when dashboard is viewed
  useEffect(() => { resetUnseen(); }, [resetUnseen]);

  return (
    <main className="min-h-screen pb-8">
      <WelcomeModal />
      <GuidedTour />

      {/* Market Overview Bar */}
      <div data-tour="market-overview">
        <ErrorBoundary name="Market Overview">
          <MarketOverview stocks={stocks} crypto={crypto} forex={forex} isLoading={marketsLoading} lastUpdated={lastUpdated} />
        </ErrorBoundary>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 py-6">
        {/* Performance Summary (compact inline bar) */}
        <div data-tour="win-rate">
          <ErrorBoundary name="Signal Performance">
            <WinRateCard />
          </ErrorBoundary>
        </div>

        {/* Signal Feed (full width) */}
        <div className="mt-6" data-tour="signal-feed">
          <ErrorBoundary name="Signal Feed">
            <SignalFeed signals={signals} isLoading={isLoading} error={error} />
          </ErrorBoundary>
        </div>

        {/* Inline disclaimer */}
        <div className="mt-8 text-center text-xs text-text-muted py-4 border-t border-border-default">
          <span className="text-signal-hold/60">This is AI-generated analysis, not financial advice.</span>
          {' '}Always do your own research before making investment decisions.
        </div>
      </div>
    </main>
  );
}
