'use client';

import { MarketOverview } from '@/components/markets/MarketOverview';
import { MarketHeatmap } from '@/components/markets/MarketHeatmap';
import { SignalFeed } from '@/components/signals/SignalFeed';
import { WinRateCard } from '@/components/signals/WinRateCard';
import { AccuracyChart } from '@/components/signals/AccuracyChart';
import { AskAI } from '@/components/signals/AskAI';
import { AlertTimeline } from '@/components/alerts/AlertTimeline';
import { useSignalStore } from '@/store/signalStore';
import { useMarketStore } from '@/store/marketStore';
import { useSignals } from '@/hooks/useSignals';
import { useMarketData } from '@/hooks/useMarketData';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';
import { WelcomeModal } from '@/components/shared/WelcomeModal';
import { ChatIdPrompt } from '@/components/shared/ChatIdPrompt';
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
    <main className="min-h-screen pb-12">
      <WelcomeModal />
      <ChatIdPrompt />

      {/* Market Overview Bar */}
      <ErrorBoundary name="Market Overview">
        <MarketOverview stocks={stocks} crypto={crypto} forex={forex} isLoading={marketsLoading} lastUpdated={lastUpdated} />
      </ErrorBoundary>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Signal Feed */}
          <div className="lg:col-span-2">
            <ErrorBoundary name="Signal Feed">
              <SignalFeed signals={signals} isLoading={isLoading} error={error} />
            </ErrorBoundary>
          </div>

          {/* Alert Timeline */}
          <div className="space-y-6">
            <ErrorBoundary name="Signal Performance">
              <WinRateCard />
            </ErrorBoundary>
            <ErrorBoundary name="Accuracy Trend">
              <AccuracyChart />
            </ErrorBoundary>
            <ErrorBoundary name="Market Heatmap">
              <MarketHeatmap />
            </ErrorBoundary>
            <ErrorBoundary name="Ask AI">
              <AskAI />
            </ErrorBoundary>
            <ErrorBoundary name="Alert Timeline">
              <AlertTimeline signals={signals} />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </main>
  );
}
