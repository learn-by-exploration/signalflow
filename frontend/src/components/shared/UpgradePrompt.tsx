'use client';

import Link from 'next/link';
import { FEATURE_LABELS, TIER_CONFIG } from '@/lib/tiers';

interface UpgradePromptProps {
  feature: string;
}

export function UpgradePrompt({ feature }: UpgradePromptProps) {
  const featureInfo = FEATURE_LABELS[feature];
  const proConfig = TIER_CONFIG.pro;

  return (
    <div className="bg-bg-card border border-accent-purple/20 rounded-xl p-6 text-center space-y-3 max-w-md mx-auto">
      <div className="w-10 h-10 rounded-full bg-accent-purple/10 flex items-center justify-center mx-auto">
        <span className="text-accent-purple text-lg">⚡</span>
      </div>
      <h3 className="text-lg font-display font-semibold">
        {featureInfo?.label ?? feature} is a Pro feature
      </h3>
      <p className="text-sm text-text-secondary">
        {featureInfo?.description ?? 'This feature'} is available on the Pro plan.
        Upgrade for {proConfig.price} to unlock all features.
      </p>
      <div className="pt-2">
        <Link
          href="/pricing"
          className="inline-block px-6 py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors"
        >
          View Plans
        </Link>
      </div>
    </div>
  );
}
