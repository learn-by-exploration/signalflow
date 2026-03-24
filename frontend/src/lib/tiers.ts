/**
 * User tier and feature gating configuration.
 *
 * Free: Limited signals/day, no AI Q&A, no backtesting
 * Pro ($9/mo): Unlimited signals, AI Q&A, backtesting, priority support
 */

export type UserTier = 'free' | 'pro';

export interface TierConfig {
  name: string;
  price: string;
  signalsPerDay: number | null; // null = unlimited
  features: Record<string, boolean>;
}

export const TIER_CONFIG: Record<UserTier, TierConfig> = {
  free: {
    name: 'Free',
    price: '₹0',
    signalsPerDay: 5,
    features: {
      viewSignals: true,
      viewHistory: true,
      trackRecord: true,
      calendar: true,
      watchlist: true,
      aiQA: false,
      backtesting: false,
      portfolio: false,
      telegramAlerts: false,
      exportData: false,
    },
  },
  pro: {
    name: 'Pro',
    price: '₹749/mo',
    signalsPerDay: null, // unlimited
    features: {
      viewSignals: true,
      viewHistory: true,
      trackRecord: true,
      calendar: true,
      watchlist: true,
      aiQA: true,
      backtesting: true,
      portfolio: true,
      telegramAlerts: true,
      exportData: true,
    },
  },
};

export const FEATURE_LABELS: Record<string, { label: string; description: string }> = {
  viewSignals: { label: 'View Signals', description: 'Access AI-generated trading signals' },
  viewHistory: { label: 'Signal History', description: 'View past signal outcomes' },
  trackRecord: { label: 'Track Record', description: 'Public performance dashboard' },
  calendar: { label: 'Economic Calendar', description: 'Key market events' },
  watchlist: { label: 'Watchlist', description: 'Custom symbol watchlist' },
  aiQA: { label: 'Ask AI', description: 'Ask questions about any signal or market' },
  backtesting: { label: 'Backtesting', description: 'Test strategies on historical data' },
  portfolio: { label: 'Portfolio Tracking', description: 'Log and track your trades' },
  telegramAlerts: { label: 'Telegram Alerts', description: 'Real-time signal notifications' },
  exportData: { label: 'Export Data', description: 'Download signals as CSV/JSON' },
};
