/**
 * Formatting utilities for prices, percentages, dates, and numbers.
 */

/**
 * Format a price string with appropriate currency symbol and precision.
 */
export function formatPrice(price: string | number, marketType?: string): string {
  const num = typeof price === 'string' ? parseFloat(price) : price;
  if (isNaN(num)) return '—';

  if (marketType === 'forex') {
    return num.toFixed(4);
  }
  if (marketType === 'crypto' && num >= 1000) {
    return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (marketType === 'crypto') {
    return num.toFixed(4);
  }
  // Stocks — Indian rupee formatting
  return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Format a percentage change with + or - sign and color hint.
 */
export function formatPercent(pct: string | number): string {
  const num = typeof pct === 'string' ? parseFloat(pct) : pct;
  if (isNaN(num)) return '—';
  const sign = num >= 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
}

/**
 * Determine if a percentage change is positive, negative, or neutral.
 */
export function changeDirection(pct: string | number): 'up' | 'down' | 'flat' {
  const num = typeof pct === 'string' ? parseFloat(pct) : pct;
  if (num > 0) return 'up';
  if (num < 0) return 'down';
  return 'flat';
}

/**
 * Format an ISO date string to a human-readable relative or absolute form.
 */
export function formatDate(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

/**
 * Format a timestamp to time-only display (HH:MM).
 */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

/**
 * Shorten a symbol for display (remove .NS suffix, USDT suffix).
 */
export function shortSymbol(symbol: string): string {
  return symbol.replace('.NS', '').replace('USDT', '');
}

/**
 * Format large volume numbers with K/M/B suffixes.
 */
export function formatVolume(vol: string | number | null): string {
  if (vol === null || vol === undefined) return '—';
  const num = typeof vol === 'string' ? parseFloat(vol) : vol;
  if (isNaN(num)) return '—';
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return num.toString();
}

/**
 * Format milliseconds remaining into a human-readable countdown.
 * e.g. "5d 14h", "2h 30m", "45m"
 */
export function formatTimeRemaining(ms: number): string {
  if (ms <= 0) return 'Expired';
  const hours = Math.floor(ms / 3600000);
  const days = Math.floor(hours / 24);
  const remainHours = hours % 24;
  const mins = Math.floor((ms % 3600000) / 60000);

  if (days > 0) return `${days}d ${remainHours}h`;
  if (hours > 0) return `${hours}h ${mins}m`;
  return `${mins}m`;
}
