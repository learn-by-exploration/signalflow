'use client';

/**
 * Skeleton loading screens that match the layout of actual content.
 * Used instead of generic spinners for better perceived performance.
 */

export function SignalCardSkeleton() {
  return (
    <div className="bg-bg-card/[0.04] border border-border-default rounded-xl p-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-4 w-20 bg-bg-secondary rounded" />
          <div className="h-5 w-24 bg-bg-secondary rounded-full" />
        </div>
        <div className="text-right space-y-1">
          <div className="h-4 w-16 bg-bg-secondary rounded ml-auto" />
          <div className="h-3 w-12 bg-bg-secondary rounded ml-auto" />
        </div>
      </div>
      <div className="flex items-center justify-between mt-2">
        <div className="h-3 w-28 bg-bg-secondary rounded" />
        <div className="flex gap-3">
          <div className="h-3 w-14 bg-bg-secondary rounded" />
          <div className="h-3 w-14 bg-bg-secondary rounded" />
        </div>
      </div>
    </div>
  );
}

export function SignalFeedSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <SignalCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function MarketOverviewSkeleton() {
  return (
    <div className="bg-bg-secondary/60 border-b border-border-default px-4 py-2 animate-pulse">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-bg-secondary" />
          <div className="h-3 w-10 bg-bg-secondary rounded" />
        </div>
        <div className="flex gap-6">
          <div className="flex items-center gap-2">
            <div className="h-3 w-10 bg-bg-secondary rounded" />
            <div className="h-3 w-16 bg-bg-secondary rounded" />
            <div className="h-3 w-12 bg-bg-secondary rounded" />
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-10 bg-bg-secondary rounded" />
            <div className="h-3 w-16 bg-bg-secondary rounded" />
            <div className="h-3 w-12 bg-bg-secondary rounded" />
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-10 bg-bg-secondary rounded" />
            <div className="h-3 w-16 bg-bg-secondary rounded" />
            <div className="h-3 w-12 bg-bg-secondary rounded" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function WinRateCardSkeleton() {
  return (
    <div className="bg-bg-card/[0.04] border border-border-default rounded-lg px-4 py-2.5 animate-pulse">
      <div className="flex items-center gap-6">
        <div className="h-4 w-20 bg-bg-secondary rounded" />
        <div className="h-4 w-24 bg-bg-secondary rounded" />
        <div className="h-3 w-16 bg-bg-secondary rounded ml-auto" />
      </div>
    </div>
  );
}

export function HistoryTableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="bg-bg-card/[0.04] border border-border-default rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-5 w-5 bg-bg-secondary rounded" />
            <div className="h-4 w-20 bg-bg-secondary rounded" />
            <div className="h-3 w-16 bg-bg-secondary rounded" />
          </div>
          <div className="flex items-center gap-4">
            <div className="h-4 w-16 bg-bg-secondary rounded" />
            <div className="h-3 w-20 bg-bg-secondary rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function PortfolioSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-bg-card/[0.04] border border-border-default rounded-xl p-4">
            <div className="h-3 w-20 bg-bg-secondary rounded mb-2" />
            <div className="h-6 w-24 bg-bg-secondary rounded" />
          </div>
        ))}
      </div>
      <div className="bg-bg-card/[0.04] border border-border-default rounded-xl p-5">
        <div className="h-4 w-24 bg-bg-secondary rounded mb-4" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex justify-between py-2 border-b border-border-default last:border-0">
            <div className="h-4 w-20 bg-bg-secondary rounded" />
            <div className="h-4 w-16 bg-bg-secondary rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
