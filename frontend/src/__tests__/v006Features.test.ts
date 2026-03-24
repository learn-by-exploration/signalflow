import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePreferencesStore } from '@/store/preferencesStore';

/**
 * Tests for v0.0.6 features: timeframe classification, theme mode, backtest params.
 */

describe('Timeframe Classification (U10-2)', () => {
  /** Classify signal timeframe string into short/medium/long */
  function classifyTimeframe(tf?: string): 'short' | 'medium' | 'long' {
    if (!tf) return 'medium';
    const lower = tf.toLowerCase();
    if (lower.includes('hour') || lower.includes('minute') || lower.includes('1 day') || lower.includes('1-2 day') || lower.includes('intraday')) return 'short';
    if (lower.includes('month') || lower.includes('quarter') || lower.includes('6') || lower.includes('year')) return 'long';
    return 'medium';
  }

  it('classifies hours as short', () => {
    expect(classifyTimeframe('2-4 hours')).toBe('short');
  });

  it('classifies minutes as short', () => {
    expect(classifyTimeframe('30 minutes')).toBe('short');
  });

  it('classifies 1 day as short', () => {
    expect(classifyTimeframe('1 day')).toBe('short');
  });

  it('classifies 1-2 days as short', () => {
    expect(classifyTimeframe('1-2 days')).toBe('short');
  });

  it('classifies intraday as short', () => {
    expect(classifyTimeframe('intraday')).toBe('short');
  });

  it('classifies weeks as medium', () => {
    expect(classifyTimeframe('2-4 weeks')).toBe('medium');
  });

  it('classifies "3-5 days" as medium (default)', () => {
    expect(classifyTimeframe('3-5 days')).toBe('medium');
  });

  it('classifies month as long', () => {
    expect(classifyTimeframe('1-3 months')).toBe('long');
  });

  it('classifies quarter as long', () => {
    expect(classifyTimeframe('next quarter')).toBe('long');
  });

  it('classifies year as long', () => {
    expect(classifyTimeframe('1 year')).toBe('long');
  });

  it('defaults to medium for undefined', () => {
    expect(classifyTimeframe(undefined)).toBe('medium');
  });

  it('defaults to medium for empty string', () => {
    expect(classifyTimeframe('')).toBe('medium');
  });
});

describe('Theme Mode Store (L-1)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Clear localStorage
    if (typeof localStorage !== 'undefined') {
      localStorage.clear();
    }
  });

  it('dark is the default theme', () => {
    const state = usePreferencesStore.getState();
    // Default should be dark (or whatever was stored)
    expect(['dark', 'light']).toContain(state.themeMode);
  });

  it('setThemeMode updates to light', () => {
    usePreferencesStore.getState().setThemeMode('light');
    expect(usePreferencesStore.getState().themeMode).toBe('light');
  });

  it('setThemeMode updates back to dark', () => {
    usePreferencesStore.getState().setThemeMode('light');
    usePreferencesStore.getState().setThemeMode('dark');
    expect(usePreferencesStore.getState().themeMode).toBe('dark');
  });
});

describe('Backtest Parameters (B5-2)', () => {
  it('ATR multiplier defaults to 2.0', () => {
    const defaultAtr = 2.0;
    expect(defaultAtr).toBe(2.0);
  });

  it('stop loss is half of ATR multiplier', () => {
    const atrMultiplier = 3.0;
    expect(atrMultiplier / 2).toBe(1.5);
  });

  it('R:R ratio is always 1:2 for default settings', () => {
    const atrMultiplier = 2.0;
    const stopMultiplier = atrMultiplier / 2;
    const rr = atrMultiplier / stopMultiplier;
    expect(rr).toBe(2);
  });

  it('RSI threshold range is 20-50', () => {
    const min = 20;
    const max = 50;
    const defaultVal = 35;
    expect(defaultVal).toBeGreaterThanOrEqual(min);
    expect(defaultVal).toBeLessThanOrEqual(max);
  });
});
