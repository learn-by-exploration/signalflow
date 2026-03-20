'use client';

import { MarketOverview } from '@/components/markets/MarketOverview';
import { SignalFeed } from '@/components/signals/SignalFeed';
import { WinRateCard } from '@/components/signals/WinRateCard';
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

export default function Dashboard() {
  const { signals, isLoading, error } = useSignalStore();
  const { stocks, crypto, forex, isLoading: marketsLoading, lastUpdated } = useMarketStore();

  // Fetch initial data via REST, subscribe to real-time via WebSocket
  useSignals();
  useMarketData();
  useWebSocket();

  return (
    <main className="min-h-screen pb-12">
      <WelcomeModal />
      <ChatIdPrompt />

      {/* Market Overview Bar */}
      <ErrorBoundary>
        <MarketOverview stocks={stocks} crypto={crypto} forex={forex} isLoading={marketsLoading} lastUpdated={lastUpdated} />
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
          <div className="space-y-6">
            <ErrorBoundary>
              <WinRateCard />
            </ErrorBoundary>
            <ErrorBoundary>
              <AskAI />
            </ErrorBoundary>
            <ErrorBoundary>
              <AlertTimeline signals={signals} />
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </main>
  );
}
