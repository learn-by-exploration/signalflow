/**
 * Tests for ImpactSimulator component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImpactSimulator } from '@/components/graph/ImpactSimulator';
import { mkgApi } from '@/lib/mkg-api';
import { useGraphStore } from '@/store/graphStore';
import type { MKGEntity, PropagationResult } from '@/lib/mkg-types';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    searchEntities: vi.fn(),
    runPropagation: vi.fn(),
  },
}));

// Mock next/link (used by child components)
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const mockSearchEntities = vi.mocked(mkgApi.searchEntities);
const mockRunPropagation = vi.mocked(mkgApi.runPropagation);

function makeEntity(overrides: Partial<MKGEntity> = {}): MKGEntity {
  return {
    id: 'e-tsmc',
    entity_type: 'Company',
    name: 'TSMC',
    canonical_name: 'tsmc',
    tags: ['semiconductor'],
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function makeResult(): PropagationResult {
  return {
    propagation: [
      { entity_id: 'e-apple', impact: 0.72, depth: 2, path: ['e-tsmc', 'e-fox', 'e-apple'], direction: 'downstream' },
    ],
    causal_chains: [
      {
        trigger: 'e-tsmc',
        trigger_name: 'TSMC',
        trigger_event: 'Factory fire',
        affected_entity: 'e-apple',
        affected_name: 'Apple',
        impact_score: 0.72,
        hops: 2,
        path: ['TSMC', 'Foxconn', 'Apple'],
        edge_labels: ['SUPPLIES_TO', 'SUPPLIES_TO'],
        narrative: 'TSMC disruption cascades to Apple.',
      },
    ],
    impact_table: {
      rows: [
        {
          rank: 1,
          entity_id: 'e-apple',
          entity_name: 'Apple',
          entity_type: 'Company',
          impact_score: 0.72,
          impact_pct: 72,
          depth: 2,
          path: ['TSMC', 'Foxconn', 'Apple'],
        },
      ],
      total: 1,
      trigger: 'TSMC',
    },
  };
}

describe('ImpactSimulator', () => {
  beforeEach(() => {
    useGraphStore.getState().reset();
    vi.clearAllMocks();
  });

  it('renders the title', () => {
    render(<ImpactSimulator />);
    expect(screen.getByText(/Impact Simulator/)).toBeInTheDocument();
  });

  it('renders entity search when no trigger selected', () => {
    render(<ImpactSimulator />);
    expect(screen.getByPlaceholderText(/Search for a company/)).toBeInTheDocument();
  });

  it('renders event description input', () => {
    render(<ImpactSimulator />);
    expect(screen.getByPlaceholderText(/Factory fire/)).toBeInTheDocument();
  });

  it('renders max depth selector', () => {
    render(<ImpactSimulator />);
    expect(screen.getByText('Max Depth')).toBeInTheDocument();
  });

  it('renders min impact selector', () => {
    render(<ImpactSimulator />);
    expect(screen.getByText('Min Impact')).toBeInTheDocument();
  });

  it('disables run button when no entity selected', () => {
    render(<ImpactSimulator />);
    const button = screen.getByText('Run Simulation');
    expect(button).toBeDisabled();
  });

  it('renders disclaimer text', () => {
    render(<ImpactSimulator />);
    expect(screen.getByText(/Not investment advice/)).toBeInTheDocument();
  });

  it('does not show results initially', () => {
    render(<ImpactSimulator />);
    expect(screen.queryByText('Impact Table')).not.toBeInTheDocument();
    expect(screen.queryByText('Chain Analysis')).not.toBeInTheDocument();
  });

  it('shows error message when simulation fails', async () => {
    const user = userEvent.setup();
    mockSearchEntities.mockResolvedValue([makeEntity()]);
    mockRunPropagation.mockRejectedValue(new Error('API Error'));

    render(<ImpactSimulator />);

    // Search and select entity
    const searchInput = screen.getByPlaceholderText(/Search for a company/);
    await user.type(searchInput, 'TSMC');

    // Wait for search results to appear
    await waitFor(() => {
      expect(mockSearchEntities).toHaveBeenCalled();
    });

    // Select the entity from dropdown
    await waitFor(() => {
      const result = screen.getByText('TSMC');
      return result;
    });
    const resultItem = screen.getByText('TSMC');
    await user.click(resultItem);

    // Run simulation
    const runButton = screen.getByText('Run Simulation');
    await user.click(runButton);

    // Should show error
    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });
  });
});
