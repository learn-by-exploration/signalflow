/**
 * GraphSkeletons — loading placeholder components for MKG pages.
 */
'use client';

/** Skeleton for an EntityCard (full mode). */
export function EntityCardSkeleton() {
  return (
    <div className="rounded-xl border border-border-default bg-bg-secondary p-5 animate-pulse">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-white/5" />
        <div className="flex-1">
          <div className="h-5 w-32 bg-white/5 rounded mb-2" />
          <div className="h-4 w-20 bg-white/5 rounded" />
        </div>
      </div>
      <div className="flex gap-2 mb-4">
        <div className="h-5 w-16 bg-white/5 rounded-md" />
        <div className="h-5 w-20 bg-white/5 rounded-md" />
      </div>
      <div className="h-4 w-40 bg-white/5 rounded" />
    </div>
  );
}

/** Skeleton for an EntityCard (compact mode). */
export function EntityCardCompactSkeleton() {
  return (
    <div className="p-3 rounded-lg border border-border-default bg-bg-secondary animate-pulse">
      <div className="flex items-center gap-2">
        <div className="w-2.5 h-2.5 rounded-full bg-white/5" />
        <div className="h-4 w-24 bg-white/5 rounded" />
        <div className="h-3 w-14 bg-white/5 rounded ml-auto" />
      </div>
    </div>
  );
}

/** Skeleton for the graph canvas area. */
export function GraphCanvasSkeleton() {
  return (
    <div className="w-full h-[500px] rounded-xl border border-border-default bg-bg-primary flex items-center justify-center animate-pulse">
      <div className="flex flex-col items-center gap-3 opacity-20">
        {/* Simulated nodes */}
        <div className="flex gap-8">
          <div className="w-16 h-8 rounded-lg bg-white/10" />
          <div className="w-20 h-8 rounded-lg bg-white/10" />
        </div>
        <div className="w-24 h-10 rounded-lg bg-white/10 border-2 border-accent-purple/20" />
        <div className="flex gap-8">
          <div className="w-18 h-8 rounded-lg bg-white/10" />
          <div className="w-16 h-8 rounded-lg bg-white/10" />
        </div>
      </div>
    </div>
  );
}

/** Skeleton for the RelationshipTable. */
export function RelationshipTableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-xl border border-border-default overflow-hidden animate-pulse">
      <div className="px-4 py-3 bg-bg-secondary border-b border-border-default">
        <div className="h-4 w-32 bg-white/5 rounded" />
      </div>
      <div className="divide-y divide-border-default">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-4 py-3 flex items-center gap-4">
            <div className="h-4 w-24 bg-white/5 rounded" />
            <div className="h-5 w-20 bg-white/5 rounded-full" />
            <div className="h-4 w-24 bg-white/5 rounded" />
            <div className="h-4 w-12 bg-white/5 rounded ml-auto" />
            <div className="h-4 w-12 bg-white/5 rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Skeleton for stat cards. */
export function StatCardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="flex flex-wrap gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="px-4 py-3 rounded-lg border border-border-default bg-bg-secondary animate-pulse">
          <div className="h-6 w-12 bg-white/5 rounded mb-1" />
          <div className="h-3 w-16 bg-white/5 rounded" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton for an ImpactTable. */
export function ImpactTableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-xl border border-border-default overflow-hidden animate-pulse">
      <div className="px-4 py-3 bg-bg-secondary">
        <div className="flex gap-4">
          <div className="h-3 w-6 bg-white/5 rounded" />
          <div className="h-3 w-16 bg-white/5 rounded" />
          <div className="h-3 w-12 bg-white/5 rounded" />
          <div className="h-3 w-12 bg-white/5 rounded ml-auto" />
        </div>
      </div>
      <div className="divide-y divide-border-default">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-4 py-3 flex items-center gap-4">
            <div className="h-4 w-6 bg-white/5 rounded" />
            <div className="h-4 w-20 bg-white/5 rounded" />
            <div className="h-5 w-14 bg-white/5 rounded-full" />
            <div className="h-4 w-10 bg-white/5 rounded ml-auto" />
            <div className="h-5 w-14 bg-white/5 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
