'use client';

import { useSession } from 'next-auth/react';
import dynamic from 'next/dynamic';
import { LandingPage } from '@/components/landing/LandingPage';

function DashboardSkeleton() {
  return (
    <main className="min-h-screen pb-8">
      {/* Market overview skeleton */}
      <div className="border-b border-border-default bg-bg-secondary/50">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-lg bg-bg-card animate-pulse" />
            ))}
          </div>
        </div>
      </div>
      {/* Content skeleton */}
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-6">
        <div className="h-24 rounded-xl bg-bg-card animate-pulse" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 rounded-xl bg-bg-card animate-pulse" />
          ))}
        </div>
      </div>
    </main>
  );
}

const DashboardContent = dynamic(
  () => import('@/components/dashboard/DashboardContent'),
  { ssr: false, loading: () => <DashboardSkeleton /> }
);

export default function HomePage() {
  const { status } = useSession();

  if (status === 'loading') {
    return <DashboardSkeleton />;
  }

  if (status === 'authenticated') {
    return <DashboardContent />;
  }

  return <LandingPage />;
}
