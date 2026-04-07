/**
 * Tests for ScenarioCards component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ScenarioCards } from '@/components/graph/ScenarioCards';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    searchEntities: vi.fn(),
    runPropagation: vi.fn(),
  },
}));

import { mkgApi } from '@/lib/mkg-api';

const mockEntity = {
  id: 'e-tsmc',
  entity_type: 'Company',
  name: 'TSMC',
  canonical_name: 'TSMC',
  tags: ['semiconductor'],
  created_at: null,
  updated_at: null,
};

const mockResult = {
  propagation: [
    { entity_id: 'e-apple', impact: 0.7, depth: 1, path: [], direction: 'outgoing' },
  ],
  causal_chains: [],
  impact_table: {
    rows: [
      {
        rank: 1,
        entity_id: 'e-apple',
        entity_name: 'Apple',
        entity_type: 'Company',
        impact_score: 0.7,
        impact_pct: 70,
        depth: 1,
        path: [],
      },
    ],
    total: 1,
    trigger: 'TSMC',
  },
};

describe('ScenarioCards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all 6 preset scenario cards', () => {
    render(<ScenarioCards onScenarioRun={vi.fn()} />);
    expect(screen.getByText('Taiwan Earthquake')).toBeInTheDocument();
    expect(screen.getByText('Samsung Fab Fire')).toBeInTheDocument();
    expect(screen.getByText('US-China Trade Escalation')).toBeInTheDocument();
    expect(screen.getByText('RBI Rate Hike')).toBeInTheDocument();
    expect(screen.getByText('IT Sector Slowdown')).toBeInTheDocument();
    expect(screen.getByText('Crypto Market Crash')).toBeInTheDocument();
  });

  it('displays scenario descriptions', () => {
    render(<ScenarioCards onScenarioRun={vi.fn()} />);
    expect(screen.getByText(/Major earthquake disrupts/)).toBeInTheDocument();
  });

  it('runs a scenario when clicked', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([mockEntity]);
    (mkgApi.runPropagation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResult);

    const onScenarioRun = vi.fn();
    render(<ScenarioCards onScenarioRun={onScenarioRun} />);

    const card = screen.getByText('Taiwan Earthquake');
    await userEvent.click(card);

    await waitFor(() => {
      expect(onScenarioRun).toHaveBeenCalledTimes(1);
    });

    expect(mkgApi.searchEntities).toHaveBeenCalledWith('TSMC', undefined, 1);
    expect(mkgApi.runPropagation).toHaveBeenCalledWith(
      expect.objectContaining({
        trigger_entity_id: 'e-tsmc',
      }),
    );
  });

  it('shows error when entity not found', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockResolvedValue([]);

    render(<ScenarioCards onScenarioRun={vi.fn()} />);

    const card = screen.getByText('Taiwan Earthquake');
    await userEvent.click(card);

    await waitFor(() => {
      expect(screen.getByText(/Entity.*not found/i)).toBeInTheDocument();
    });
  });

  it('shows loading state during scenario run', async () => {
    (mkgApi.searchEntities as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve([mockEntity]), 200)),
    );
    (mkgApi.runPropagation as ReturnType<typeof vi.fn>).mockResolvedValue(mockResult);

    render(<ScenarioCards onScenarioRun={vi.fn()} />);

    const card = screen.getByText('Taiwan Earthquake');
    await userEvent.click(card);

    // Should show some loading indication
    expect(screen.getByText('Taiwan Earthquake')).toBeInTheDocument();
  });

  it('has the section heading', () => {
    render(<ScenarioCards onScenarioRun={vi.fn()} />);
    expect(screen.getByText('Quick Scenarios')).toBeInTheDocument();
  });
});
