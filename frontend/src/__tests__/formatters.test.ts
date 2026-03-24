import { describe, it, expect } from 'vitest';
import {
  formatPrice,
  formatPercent,
  changeDirection,
  formatDate,
  shortSymbol,
  formatVolume,
  formatTimeRemaining,
} from '@/utils/formatters';

describe('formatPrice', () => {
  it('formats stock prices with rupee symbol and 2 decimals', () => {
    expect(formatPrice('1678.90', 'stock')).toBe('₹1,678.90');
    expect(formatPrice(1678.9, 'stock')).toBe('₹1,678.90');
  });

  it('formats forex prices with 4 decimal places', () => {
    expect(formatPrice('1.0845', 'forex')).toBe('1.0845');
    expect(formatPrice('83.4500', 'forex')).toBe('83.4500');
    expect(formatPrice(1.08452, 'forex')).toBe('1.0845');
  });

  it('formats crypto prices >= 1000 with 2 decimals', () => {
    const result = formatPrice('97842.00', 'crypto');
    expect(result).toContain('97');
    expect(result).toContain('.00');
  });

  it('formats crypto prices < 1000 with 4 decimals', () => {
    expect(formatPrice('0.5432', 'crypto')).toBe('0.5432');
  });

  it('returns dash for NaN', () => {
    expect(formatPrice('invalid')).toBe('—');
    expect(formatPrice(NaN)).toBe('—');
  });
});

describe('formatPercent', () => {
  it('formats positive percentages with + sign', () => {
    expect(formatPercent(3.87)).toBe('+3.87%');
    expect(formatPercent('1.42')).toBe('+1.42%');
  });

  it('formats negative percentages', () => {
    expect(formatPercent(-2.5)).toBe('-2.50%');
  });

  it('formats zero', () => {
    expect(formatPercent(0)).toBe('+0.00%');
  });

  it('returns dash for NaN', () => {
    expect(formatPercent('invalid')).toBe('—');
  });
});

describe('changeDirection', () => {
  it('returns up for positive', () => {
    expect(changeDirection(1.5)).toBe('up');
    expect(changeDirection('3.2')).toBe('up');
  });

  it('returns down for negative', () => {
    expect(changeDirection(-0.5)).toBe('down');
  });

  it('returns flat for zero', () => {
    expect(changeDirection(0)).toBe('flat');
  });
});

describe('shortSymbol', () => {
  it('removes .NS suffix', () => {
    expect(shortSymbol('HDFCBANK.NS')).toBe('HDFCBANK');
  });

  it('removes USDT suffix', () => {
    expect(shortSymbol('BTCUSDT')).toBe('BTC');
  });

  it('keeps forex symbols as-is', () => {
    expect(shortSymbol('USD/INR')).toBe('USD/INR');
  });
});

describe('formatVolume', () => {
  it('formats billions', () => {
    expect(formatVolume(1500000000)).toBe('1.5B');
  });

  it('formats millions', () => {
    expect(formatVolume(2500000)).toBe('2.5M');
  });

  it('formats thousands', () => {
    expect(formatVolume(45000)).toBe('45.0K');
  });

  it('handles null', () => {
    expect(formatVolume(null)).toBe('—');
  });
});

describe('formatTimeRemaining', () => {
  it('shows days and hours', () => {
    expect(formatTimeRemaining(5 * 24 * 3600000 + 14 * 3600000)).toBe('5d 14h');
  });

  it('shows hours and minutes', () => {
    expect(formatTimeRemaining(2 * 3600000 + 30 * 60000)).toBe('2h 30m');
  });

  it('shows minutes only', () => {
    expect(formatTimeRemaining(45 * 60000)).toBe('45m');
  });

  it('shows Expired for 0 or negative', () => {
    expect(formatTimeRemaining(0)).toBe('Expired');
    expect(formatTimeRemaining(-1000)).toBe('Expired');
  });
});

describe('formatDate', () => {
  it('shows "Just now" for very recent dates', () => {
    const now = new Date().toISOString();
    expect(formatDate(now)).toBe('Just now');
  });

  it('shows minutes ago', () => {
    const fiveMinAgo = new Date(Date.now() - 5 * 60000).toISOString();
    expect(formatDate(fiveMinAgo)).toBe('5m ago');
  });

  it('shows hours ago', () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 3600000).toISOString();
    expect(formatDate(threeHoursAgo)).toBe('3h ago');
  });

  it('shows days ago', () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 86400000).toISOString();
    expect(formatDate(twoDaysAgo)).toBe('2d ago');
  });
});
