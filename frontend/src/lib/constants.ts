/**
 * Application constants — colors, thresholds, market config.
 */

export const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Derive WebSocket URL dynamically from window.location.
 * Connects to the backend directly on port 8000 using the same hostname
 * the user is already accessing the frontend from.
 * Falls back to env var or localhost for SSR/test contexts.
 */
export function getWsUrl(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.hostname}:8000`;
  }
  return 'ws://localhost:8000';
}

/** @deprecated Use getWsUrl() instead */
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export const SIGNAL_COLORS = {
  STRONG_BUY: '#00E676',
  BUY: '#66BB6A',
  HOLD: '#FFD740',
  SELL: '#EF5350',
  STRONG_SELL: '#D50000',
} as const;

export const CONFIDENCE_THRESHOLDS = {
  STRONG_BUY: 80,
  BUY: 65,
  HOLD_LOW: 36,
  SELL: 21,
  STRONG_SELL: 0,
} as const;

export const MARKET_LABELS = {
  stock: 'Stocks',
  crypto: 'Crypto',
  forex: 'Forex',
} as const;

export const BADGE_LABELS = {
  STRONG_BUY: 'STRONGLY BULLISH',
  BUY: 'BULLISH',
  HOLD: 'HOLD',
  SELL: 'BEARISH',
  STRONG_SELL: 'STRONGLY BEARISH',
} as const;

export const NAV_PRIMARY_LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/watchlist', label: 'Watchlist' },
  { href: '/portfolio', label: 'Portfolio' },
  { href: '/brief', label: 'Brief' },
  { href: '/track-record', label: 'Track Record' },
];

export const NAV_RESEARCH_LINKS = [
  { href: '/news', label: 'News', icon: '📰' },
  { href: '/calendar', label: 'Calendar', icon: '📅' },
  { href: '/backtest', label: 'Backtest', icon: '🔬' },
  { href: '/history', label: 'Signal History', icon: '📜' },
  { href: '/alerts', label: 'Alerts', icon: '🔔' },
];

export const NAV_INFO_LINKS = [
  { href: '/how-it-works', label: 'How It Works', icon: '❓' },
  { href: '/research', label: 'Research Library', icon: '📚' },
  { href: '/pricing', label: 'Pricing', icon: '💎' },
];

export const NAV_MOBILE_TABS = [
  { href: '/', label: 'Home', id: 'home' },
  { href: '/watchlist', label: 'Watchlist', id: 'watchlist' },
  { href: '/brief', label: 'Brief', id: 'brief' },
  { href: '/portfolio', label: 'Portfolio', id: 'portfolio' },
  { id: 'menu', label: 'Menu' },
] as const;

export const NAV_MOBILE_MENU_GROUPS = [
  {
    title: 'Performance',
    links: [
      { href: '/track-record', label: 'Track Record', icon: '📊' },
      { href: '/history', label: 'Signal History', icon: '📜' },
    ],
  },
  {
    title: 'Research',
    links: [
      { href: '/news', label: 'News', icon: '📰' },
      { href: '/calendar', label: 'Calendar', icon: '📅' },
      { href: '/backtest', label: 'Backtest', icon: '🔬' },
    ],
  },
  {
    title: 'Account',
    links: [
      { href: '/alerts', label: 'Alert Settings', icon: '🔔' },
      { href: '/settings', label: 'Settings', icon: '⚙️' },
    ],
  },
  {
    title: 'About',
    links: [
      { href: '/how-it-works', label: 'How It Works', icon: '❓' },
      { href: '/research', label: 'Research Library', icon: '📚' },
      { href: '/pricing', label: 'Pricing', icon: '💎' },
    ],
  },
];

export const NAV_LEGAL_LINKS = [
  { href: '/privacy', label: 'Privacy' },
  { href: '/terms', label: 'Terms' },
  { href: '/refund-policy', label: 'Refund Policy' },
  { href: '/contact', label: 'Contact' },
];

export const NAV_PUBLIC_LINKS = [
  { href: '/how-it-works', label: 'How It Works' },
  { href: '/pricing', label: 'Pricing' },
];
