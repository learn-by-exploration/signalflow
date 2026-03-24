'use client';

import { useEffect } from 'react';
import { MarketOverview } from '@/components/markets/MarketOverview';
import { SignalFeed } from '@/components/signals/SignalFeed';
import { WinRateCard } from '@/components/signals/WinRateCard';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';
import { useSignalsQuery, useMarketOverviewQuery } from '@/hooks/useQueries';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { WelcomeModal } from '@/components/shared/WelcomeModal';
import { GuidedTour } from '@/components/shared/GuidedTour';
import { AskAI } from '@/components/signals/AskAI';
import type { MarketSnapshot } from '@/lib/types';

export default function DashboardContent() {
  const resetUnseen = useSignalStore((s) => s.resetUnseen);

  // React Query: signals
  const signalsQuery = useSignalsQuery();
  const signals = signalsQuery.data?.data ?? [];
  const signalsLoading = signalsQuery.isLoading;
  const signalsError = signalsQuery.error?.message ?? null;

  // Sync signals to store for WebSocket/other consumers
  const setSignals = useSignalStore((s) => s.setSignals);
  useEffect(() => {
    if (signalsQuery.data) {
      setSignals(signalsQuery.data.data, signalsQuery.data.meta?.total);
    }
  }, [signalsQuery.data, setSignals]);

  // React Query: market overview
  const marketsQuery = useMarketOverviewQuery();
  const marketsData = marketsQuery.data as { data?: { stocks?: MarketSnapshot[]; crypto?: MarketSnapshot[]; forex?: MarketSnapshot[] } } | undefined;
  const stocks = marketsData?.data?.stocks ?? [];
  const crypto = marketsData?.data?.crypto ?? [];
  const forex = marketsData?.data?.forex ?? [];
  const marketsLoading = marketsQuery.isLoading;
  const lastUpdated = marketsQuery.dataUpdatedAt ? new Date(marketsQuery.dataUpdatedAt).toISOString() : null;

  // Sync markets to store for WebSocket/other consumers
  const setMarkets = useMarketStore((s) => s.setMarkets);
  useEffect(() => {
    if (marketsData?.data) {
      setMarkets(marketsData.data as { stocks: MarketSnapshot[]; crypto: MarketSnapshot[]; forex: MarketSnapshot[] });
    }
  }, [marketsData, setMarkets]);

  useWebSocket();

  useEffect(() => { resetUnseen(); }, [resetUnseen]);

  return (
    <main className="min-h-screen pb-8">
      <WelcomeModal />
      <GuidedTour />

      <div data-tour="market-overview">
        <ErrorBoundary name="Market Overview">
          <MarketOverview stocks={stocks} crypto={crypto} forex={forex} isLoading={marketsLoading} lastUpdated={lastUpdated} />
        </ErrorBoundary>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <div data-tour="win-rate">
          <ErrorBoundary name="Signal Performance">
            <WinRateCard />
          </ErrorBoundary>
        </div>

        <div className="mt-6" data-tour="signal-feed">
          <ErrorBoundary name="Signal Feed">
            <SignalFeed signals={signals} isLoading={signalsLoading} error={signalsError} />
          </ErrorBoundary>
        </div>

        <div className="mt-6">
          <ErrorBoundary name="Ask AI">
            <AskAI />
          </ErrorBoundary>
        </div>

        <div className="mt-8 text-center text-xs text-text-muted py-4 border-t border-border-default">
          <span className="text-signal-hold/60">This is AI-generated analysis, not financial advice.</span>
          {' '}Always do your own research before making investment decisions.
        </div>
      </div>
    </main>
  );
}
