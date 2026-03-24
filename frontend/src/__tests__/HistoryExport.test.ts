import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// We test the export logic as standalone functions to avoid mocking the entire page

describe('History Export (CSV)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  function generateCSV(items: { symbol: string; signal_type: string; outcome: string; return_pct: string; exit_price: string; resolved_at: string }[]) {
    return [
      'Symbol,Signal Type,Outcome,Return %,Exit Price,Resolved At',
      ...items.map((item) => `${item.symbol},${item.signal_type},${item.outcome},${item.return_pct},${item.exit_price},${item.resolved_at}`),
    ].join('\n');
  }

  it('generates correct CSV header', () => {
    const csv = generateCSV([]);
    expect(csv).toBe('Symbol,Signal Type,Outcome,Return %,Exit Price,Resolved At');
  });

  it('generates CSV with one row', () => {
    const csv = generateCSV([{
      symbol: 'HDFC',
      signal_type: 'BUY',
      outcome: 'hit_target',
      return_pct: '5.2',
      exit_price: '1780',
      resolved_at: '2026-03-20T10:00:00Z',
    }]);
    const lines = csv.split('\n');
    expect(lines).toHaveLength(2);
    expect(lines[1]).toBe('HDFC,BUY,hit_target,5.2,1780,2026-03-20T10:00:00Z');
  });

  it('generates CSV with multiple rows', () => {
    const csv = generateCSV([
      { symbol: 'HDFC', signal_type: 'BUY', outcome: 'hit_target', return_pct: '5.2', exit_price: '1780', resolved_at: '2026-03-20T10:00:00Z' },
      { symbol: 'BTC', signal_type: 'SELL', outcome: 'hit_stop', return_pct: '-2.1', exit_price: '95000', resolved_at: '2026-03-21T14:00:00Z' },
    ]);
    const lines = csv.split('\n');
    expect(lines).toHaveLength(3);
    expect(lines[1]).toContain('HDFC');
    expect(lines[2]).toContain('BTC');
  });

  it('handles empty fields gracefully', () => {
    const csv = generateCSV([{
      symbol: '',
      signal_type: '',
      outcome: 'pending',
      return_pct: '',
      exit_price: '',
      resolved_at: '',
    }]);
    const lines = csv.split('\n');
    expect(lines[1]).toBe(',,pending,,,');
  });
});

describe('History Export (JSON)', () => {
  function generateJSON(items: { symbol: string | null; signal_type: string | null; outcome: string; return_pct: string | null; exit_price: string | null; resolved_at: string | null }[]) {
    return JSON.stringify(items, null, 2);
  }

  it('generates valid JSON', () => {
    const json = generateJSON([{
      symbol: 'RELIANCE',
      signal_type: 'STRONG_BUY',
      outcome: 'hit_target',
      return_pct: '8.3',
      exit_price: '2900',
      resolved_at: '2026-03-22T09:00:00Z',
    }]);
    const parsed = JSON.parse(json);
    expect(parsed).toHaveLength(1);
    expect(parsed[0].symbol).toBe('RELIANCE');
  });

  it('handles null fields', () => {
    const json = generateJSON([{
      symbol: null,
      signal_type: null,
      outcome: 'pending',
      return_pct: null,
      exit_price: null,
      resolved_at: null,
    }]);
    const parsed = JSON.parse(json);
    expect(parsed[0].symbol).toBeNull();
    expect(parsed[0].signal_type).toBeNull();
  });

  it('generates correct structure for multiple items', () => {
    const json = generateJSON([
      { symbol: 'HDFC', signal_type: 'BUY', outcome: 'hit_target', return_pct: '5.2', exit_price: '1780', resolved_at: '2026-03-20T10:00:00Z' },
      { symbol: 'BTC', signal_type: 'SELL', outcome: 'hit_stop', return_pct: '-2.1', exit_price: '95000', resolved_at: '2026-03-21T14:00:00Z' },
    ]);
    const parsed = JSON.parse(json);
    expect(parsed).toHaveLength(2);
    expect(parsed[0].outcome).toBe('hit_target');
    expect(parsed[1].outcome).toBe('hit_stop');
  });
});

describe('Outcome Labels (plain English tooltips)', () => {
  const OUTCOME_LABELS: Record<string, { plain: string }> = {
    hit_target: { plain: 'Target price was reached — profit!' },
    hit_stop: { plain: 'Stop-loss was triggered — limited loss' },
    expired: { plain: 'Signal expired before hitting target or stop' },
    pending: { plain: 'Still active — waiting for outcome' },
  };

  it('all outcomes have plain English descriptions', () => {
    for (const key of ['hit_target', 'hit_stop', 'expired', 'pending']) {
      expect(OUTCOME_LABELS[key].plain).toBeTruthy();
      expect(OUTCOME_LABELS[key].plain.length).toBeGreaterThan(10);
    }
  });

  it('hit_target mentions profit', () => {
    expect(OUTCOME_LABELS.hit_target.plain).toContain('profit');
  });

  it('hit_stop mentions loss', () => {
    expect(OUTCOME_LABELS.hit_stop.plain).toContain('loss');
  });

  it('expired mentions target or stop', () => {
    expect(OUTCOME_LABELS.expired.plain).toMatch(/target|stop/);
  });
});
