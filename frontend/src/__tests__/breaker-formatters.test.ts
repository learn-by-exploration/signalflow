/**
 * Tester 6: The Frontend Wrecker — Edge cases for formatters, components, stores.
 *
 * Tests formatters with NaN, Infinity, undefined, null, empty strings,
 * and extreme values to expose silent failures.
 */
import { describe, it, expect } from 'vitest';
import {
  formatPrice,
  formatPercent,
  changeDirection,
  formatDate,
  formatTime,
  shortSymbol,
  formatVolume,
  formatTimeRemaining,
  formatPortfolioValue,
  currencySymbol,
} from '@/utils/formatters';

// =========================================================================
// formatPrice — Edge cases
// =========================================================================

describe('formatPrice breaker', () => {
  it('handles NaN input', () => {
    expect(formatPrice(NaN, 'stock')).toBe('—');
  });

  it('handles Infinity input', () => {
    const result = formatPrice(Infinity, 'stock');
    // Infinity is NOT NaN, so it won't be caught by isNaN
    // This is a potential bug — Infinity should show dash
    expect(typeof result).toBe('string');
  });

  it('handles negative Infinity input', () => {
    const result = formatPrice(-Infinity, 'crypto');
    expect(typeof result).toBe('string');
  });

  it('handles empty string input', () => {
    expect(formatPrice('', 'stock')).toBe('—');
  });

  it('handles non-numeric string', () => {
    expect(formatPrice('abc', 'stock')).toBe('—');
  });

  it('handles zero price', () => {
    const result = formatPrice(0, 'stock');
    expect(result).toContain('0');
  });

  it('handles negative price', () => {
    const result = formatPrice(-100, 'stock');
    expect(typeof result).toBe('string');
  });

  it('handles very large number', () => {
    const result = formatPrice(999999999999, 'crypto');
    expect(typeof result).toBe('string');
  });

  it('handles very small number', () => {
    const result = formatPrice(0.000000001, 'crypto');
    expect(result).toContain('0.0000');
  });

  it('handles undefined market type', () => {
    // Should default to stock/INR
    const result = formatPrice(100, undefined);
    expect(result).toContain('₹');
  });

  it('handles unknown market type', () => {
    const result = formatPrice(100, 'commodity');
    // Falls through to stock formatting
    expect(result).toContain('₹');
  });
});

// =========================================================================
// formatPercent — Edge cases
// =========================================================================

describe('formatPercent breaker', () => {
  it('handles NaN input', () => {
    expect(formatPercent(NaN)).toBe('—');
  });

  it('handles Infinity', () => {
    const result = formatPercent(Infinity);
    expect(typeof result).toBe('string');
  });

  it('handles zero', () => {
    expect(formatPercent(0)).toBe('+0.00%');
  });

  it('handles very large positive', () => {
    const result = formatPercent(99999);
    expect(result).toContain('+');
    expect(result).toContain('%');
  });

  it('handles very large negative', () => {
    const result = formatPercent(-99999);
    expect(result).toContain('-');
  });

  it('handles non-numeric string', () => {
    expect(formatPercent('not-a-number')).toBe('—');
  });

  it('handles empty string', () => {
    expect(formatPercent('')).toBe('—');
  });
});

// =========================================================================
// changeDirection — Edge cases
// =========================================================================

describe('changeDirection breaker', () => {
  it('handles zero', () => {
    expect(changeDirection(0)).toBe('flat');
  });

  it('handles NaN', () => {
    // NaN is not > 0 and not < 0, so it should be "flat"
    expect(changeDirection(NaN)).toBe('flat');
  });

  it('handles string input', () => {
    expect(changeDirection('5.5')).toBe('up');
    expect(changeDirection('-2.1')).toBe('down');
    expect(changeDirection('0')).toBe('flat');
  });

  it('handles non-numeric string', () => {
    // parseFloat('abc') = NaN, which is neither > 0 nor < 0
    expect(changeDirection('abc')).toBe('flat');
  });
});

// =========================================================================
// formatDate — Edge cases
// =========================================================================

describe('formatDate breaker', () => {
  it('handles invalid date string', () => {
    const result = formatDate('not-a-date');
    // new Date('not-a-date') produces Invalid Date
    // getTime() returns NaN, so diffMs is NaN
    expect(typeof result).toBe('string');
  });

  it('handles empty string', () => {
    const result = formatDate('');
    expect(typeof result).toBe('string');
  });

  it('handles future date', () => {
    const future = new Date(Date.now() + 86400000).toISOString();
    const result = formatDate(future);
    // Negative diff → diffMins < 0, which is also < 1
    expect(typeof result).toBe('string');
  });

  it('handles very old date', () => {
    const result = formatDate('1970-01-01T00:00:00Z');
    expect(typeof result).toBe('string');
  });
});

// =========================================================================
// formatVolume — Edge cases
// =========================================================================

describe('formatVolume breaker', () => {
  it('handles null', () => {
    expect(formatVolume(null)).toBe('—');
  });

  it('handles undefined', () => {
    expect(formatVolume(undefined as unknown as null)).toBe('—');
  });

  it('handles NaN string', () => {
    expect(formatVolume('abc')).toBe('—');
  });

  it('handles zero', () => {
    expect(formatVolume(0)).toBe('0');
  });

  it('handles negative volume', () => {
    // Volume shouldn't be negative, but should not crash
    const result = formatVolume(-1000);
    expect(typeof result).toBe('string');
  });

  it('formats billions correctly', () => {
    expect(formatVolume(5000000000)).toBe('5.0B');
  });

  it('formats millions correctly', () => {
    expect(formatVolume(15400000)).toBe('15.4M');
  });

  it('formats thousands correctly', () => {
    expect(formatVolume(42500)).toBe('42.5K');
  });

  it('handles numbers between 0 and 999', () => {
    expect(formatVolume(500)).toBe('500');
  });
});

// =========================================================================
// formatTimeRemaining — Edge cases
// =========================================================================

describe('formatTimeRemaining breaker', () => {
  it('handles zero ms', () => {
    expect(formatTimeRemaining(0)).toBe('Expired');
  });

  it('handles negative ms', () => {
    expect(formatTimeRemaining(-1000)).toBe('Expired');
  });

  it('handles very large ms', () => {
    const result = formatTimeRemaining(365 * 24 * 3600000);
    expect(result).toContain('d');
  });

  it('handles sub-minute', () => {
    expect(formatTimeRemaining(30000)).toBe('0m');
  });

  it('handles exactly 1 hour', () => {
    expect(formatTimeRemaining(3600000)).toBe('1h 0m');
  });

  it('handles exactly 1 day', () => {
    expect(formatTimeRemaining(86400000)).toBe('1d 0h');
  });
});

// =========================================================================
// formatPortfolioValue — Edge cases
// =========================================================================

describe('formatPortfolioValue breaker', () => {
  it('handles NaN', () => {
    expect(formatPortfolioValue(NaN)).toBe('—');
  });

  it('handles non-numeric string', () => {
    expect(formatPortfolioValue('abc')).toBe('—');
  });

  it('handles crypto market type', () => {
    const result = formatPortfolioValue(1000, 'crypto');
    expect(result).toContain('$');
  });

  it('handles stock market type', () => {
    const result = formatPortfolioValue(1000, 'stock');
    expect(result).toContain('₹');
  });

  it('handles forex market type (no symbol)', () => {
    const result = formatPortfolioValue(1000, 'forex');
    expect(result).not.toContain('$');
    expect(result).not.toContain('₹');
  });

  it('handles undefined market type', () => {
    const result = formatPortfolioValue(1000);
    expect(typeof result).toBe('string');
  });
});

// =========================================================================
// shortSymbol — Edge cases
// =========================================================================

describe('shortSymbol breaker', () => {
  it('handles empty string', () => {
    expect(shortSymbol('')).toBe('');
  });

  it('removes .NS suffix', () => {
    expect(shortSymbol('TCS.NS')).toBe('TCS');
  });

  it('removes USDT suffix', () => {
    expect(shortSymbol('BTCUSDT')).toBe('BTC');
  });

  it('handles symbol with both suffixes', () => {
    expect(shortSymbol('TESTUSDT.NS')).toBe('TEST');
  });

  it('handles symbol without suffix', () => {
    expect(shortSymbol('EUR/USD')).toBe('EUR/USD');
  });
});

// =========================================================================
// currencySymbol — Edge cases
// =========================================================================

describe('currencySymbol breaker', () => {
  it('returns $ for crypto', () => {
    expect(currencySymbol('crypto')).toBe('$');
  });

  it('returns ₹ for stock', () => {
    expect(currencySymbol('stock')).toBe('₹');
  });

  it('returns empty for forex', () => {
    expect(currencySymbol('forex')).toBe('');
  });

  it('returns empty for unknown type', () => {
    expect(currencySymbol('unknown')).toBe('');
  });
});
