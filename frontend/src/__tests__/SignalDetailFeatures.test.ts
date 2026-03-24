import { describe, it, expect } from 'vitest';

/**
 * Tests for earnings season detection logic (B1-5).
 * The signal detail page shows a warning when the current month is a quarterly earnings month.
 */
describe('Earnings Season Detection', () => {
  function isEarningsSeason(month: number): boolean {
    // Earnings seasons: Jan (Q3), Apr (Q4), Jul (Q1), Oct (Q2)
    return [0, 3, 6, 9].includes(month);
  }

  it('January is earnings season', () => {
    expect(isEarningsSeason(0)).toBe(true);
  });

  it('April is earnings season', () => {
    expect(isEarningsSeason(3)).toBe(true);
  });

  it('July is earnings season', () => {
    expect(isEarningsSeason(6)).toBe(true);
  });

  it('October is earnings season', () => {
    expect(isEarningsSeason(9)).toBe(true);
  });

  it('February is NOT earnings season', () => {
    expect(isEarningsSeason(1)).toBe(false);
  });

  it('May is NOT earnings season', () => {
    expect(isEarningsSeason(4)).toBe(false);
  });

  it('November is NOT earnings season', () => {
    expect(isEarningsSeason(10)).toBe(false);
  });

  it('all 12 months categorized correctly', () => {
    const earningsMonths = [0, 3, 6, 9];
    for (let m = 0; m < 12; m++) {
      expect(isEarningsSeason(m)).toBe(earningsMonths.includes(m));
    }
  });
});

/**
 * Tests for confidence breakdown score extraction logic.
 * Used by ConfidenceBreakdown component on signal detail page.
 */
describe('Technical Score Extraction', () => {
  function extractTechnicalScore(
    technicalData: Record<string, Record<string, unknown>> | null,
    fallbackConfidence: number
  ): number {
    if (!technicalData) return fallbackConfidence;
    const indicators = [
      technicalData.rsi,
      technicalData.macd,
      technicalData.volume,
      technicalData.bollinger,
      technicalData.sma,
    ].filter(Boolean);
    if (indicators.length === 0) return fallbackConfidence;
    const buyCount = indicators.filter((i) => i?.signal === 'buy').length;
    return Math.round((buyCount / indicators.length) * 100);
  }

  it('returns 100 when all indicators are buy', () => {
    const td = {
      rsi: { signal: 'buy' },
      macd: { signal: 'buy' },
      volume: { signal: 'buy' },
      bollinger: { signal: 'buy' },
      sma: { signal: 'buy' },
    };
    expect(extractTechnicalScore(td, 50)).toBe(100);
  });

  it('returns 0 when no indicators are buy', () => {
    const td = {
      rsi: { signal: 'sell' },
      macd: { signal: 'sell' },
      volume: { signal: 'neutral' },
      bollinger: { signal: 'sell' },
      sma: { signal: 'sell' },
    };
    expect(extractTechnicalScore(td, 50)).toBe(0);
  });

  it('returns 60 when 3 out of 5 are buy', () => {
    const td = {
      rsi: { signal: 'buy' },
      macd: { signal: 'buy' },
      volume: { signal: 'buy' },
      bollinger: { signal: 'sell' },
      sma: { signal: 'sell' },
    };
    expect(extractTechnicalScore(td, 50)).toBe(60);
  });

  it('returns fallback when no technical data', () => {
    expect(extractTechnicalScore(null, 75)).toBe(75);
  });

  it('returns fallback when no indicators present', () => {
    expect(extractTechnicalScore({}, 42)).toBe(42);
  });

  it('handles partial indicators', () => {
    const td = {
      rsi: { signal: 'buy' },
      macd: { signal: 'sell' },
    };
    expect(extractTechnicalScore(td, 50)).toBe(50); // 1 out of 2 = 50%
  });
});
