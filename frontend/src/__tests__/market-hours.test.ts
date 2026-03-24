import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { isNSEOpen, isCryptoOpen, isForexOpen, getMarketStatus, getMarketBadge } from '@/utils/market-hours';

// market-hours.ts uses: new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }))
// We use vi.useFakeTimers to control Date for deterministic tests.

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('isCryptoOpen', () => {
  it('is always open', () => {
    expect(isCryptoOpen()).toBe(true);
  });
});

describe('isNSEOpen', () => {
  it('is open on a weekday during market hours (Mon 10:00 IST)', () => {
    // Monday March 24, 2026 10:00 AM IST = 04:30 UTC
    vi.setSystemTime(new Date('2026-03-24T04:30:00Z'));
    expect(isNSEOpen()).toBe(true);
  });

  it('is closed on Saturday', () => {
    // Saturday March 28, 2026 10:00 AM IST = 04:30 UTC
    vi.setSystemTime(new Date('2026-03-28T04:30:00Z'));
    expect(isNSEOpen()).toBe(false);
  });

  it('is closed on Sunday', () => {
    // Sunday March 29, 2026 10:00 AM IST = 04:30 UTC
    vi.setSystemTime(new Date('2026-03-29T04:30:00Z'));
    expect(isNSEOpen()).toBe(false);
  });

  it('is closed before 9:15 AM IST on weekday', () => {
    // Monday March 24, 2026 9:00 AM IST = 03:30 UTC
    vi.setSystemTime(new Date('2026-03-24T03:30:00Z'));
    expect(isNSEOpen()).toBe(false);
  });

  it('is closed after 3:30 PM IST on weekday', () => {
    // Monday March 24, 2026 4:00 PM IST = 10:30 UTC
    vi.setSystemTime(new Date('2026-03-24T10:30:00Z'));
    expect(isNSEOpen()).toBe(false);
  });

  it('is open at exactly 9:15 AM IST', () => {
    // Monday March 24, 2026 9:15 AM IST = 03:45 UTC
    vi.setSystemTime(new Date('2026-03-24T03:45:00Z'));
    expect(isNSEOpen()).toBe(true);
  });

  it('is open at exactly 3:30 PM IST', () => {
    // Monday March 24, 2026 3:30 PM IST = 10:00 UTC
    vi.setSystemTime(new Date('2026-03-24T10:00:00Z'));
    expect(isNSEOpen()).toBe(true);
  });
});

describe('isForexOpen', () => {
  it('is open during weekday hours', () => {
    // Wednesday March 26, 2026 12:00 PM IST = 06:30 UTC
    vi.setSystemTime(new Date('2026-03-26T06:30:00Z'));
    expect(isForexOpen()).toBe(true);
  });

  it('is closed on Sunday morning IST', () => {
    // Sunday March 29, 2026 10:00 AM IST = 04:30 UTC
    vi.setSystemTime(new Date('2026-03-29T04:30:00Z'));
    expect(isForexOpen()).toBe(false);
  });

  it('is open on Sunday evening after 5:30 PM IST', () => {
    // Sunday March 29, 2026 6:00 PM IST = 12:30 UTC
    vi.setSystemTime(new Date('2026-03-29T12:30:00Z'));
    expect(isForexOpen()).toBe(true);
  });
});

describe('getMarketStatus', () => {
  it('returns 24/7 for crypto', () => {
    const status = getMarketStatus('crypto');
    expect(status.isOpen).toBe(true);
    expect(status.label).toBe('24/7');
  });

  it('returns Unknown for invalid market type', () => {
    const status = getMarketStatus('unknown');
    expect(status.isOpen).toBe(false);
    expect(status.label).toBe('Unknown');
  });
});

describe('getMarketBadge', () => {
  it('returns 24/7 badge for crypto', () => {
    const badge = getMarketBadge('crypto');
    expect(badge.isOpen).toBe(true);
    expect(badge.badge).toContain('24/7');
    expect(badge.hint).toBeNull();
  });

  it('returns Unknown badge for invalid type', () => {
    const badge = getMarketBadge('xyz');
    expect(badge.isOpen).toBe(false);
    expect(badge.badge).toContain('Unknown');
  });
});
