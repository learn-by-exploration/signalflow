'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

interface ShareButtonProps {
  signalId: string;
}

export function ShareButton({ signalId }: ShareButtonProps) {
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleShare() {
    setLoading(true);
    try {
      const res = (await api.shareSignal(signalId)) as { data: { share_id: string } };
      const url = `${window.location.origin}/shared/${res.data.share_id}`;
      setShareUrl(url);
      await navigator.clipboard.writeText(url);
    } catch {
      // Silently fail — share is non-critical
    } finally {
      setLoading(false);
    }
  }

  if (shareUrl) {
    return (
      <span className="text-xs text-[var(--signal-buy)]">
        Link copied!
      </span>
    );
  }

  return (
    <button
      onClick={handleShare}
      disabled={loading}
      className="text-xs text-[var(--text-muted)] hover:text-[var(--accent-purple)] transition-colors disabled:opacity-50"
    >
      {loading ? '...' : '🔗 Share'}
    </button>
  );
}
