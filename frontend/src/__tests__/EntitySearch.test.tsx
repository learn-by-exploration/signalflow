/**
 * Tests for EntitySearch component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EntitySearch } from '@/components/graph/EntitySearch';
import { useGraphStore } from '@/store/graphStore';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    searchEntities: vi.fn(),
  },
}));

import { mkgApi } from '@/lib/mkg-api';

const mockSearch = mkgApi.searchEntities as ReturnType<typeof vi.fn>;

describe('EntitySearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useGraphStore.getState().reset();
  });

  it('renders search input with placeholder', () => {
    render(<EntitySearch />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search companies/i)).toBeInTheDocument();
  });

  it('renders custom placeholder', () => {
    render(<EntitySearch placeholder="Find entities..." />);
    expect(screen.getByPlaceholderText('Find entities...')).toBeInTheDocument();
  });

  it('has correct ARIA attributes', () => {
    render(<EntitySearch />);
    const input = screen.getByRole('combobox');
    expect(input).toHaveAttribute('aria-expanded', 'false');
    expect(input).toHaveAttribute('aria-autocomplete', 'list');
  });

  it('does not search for queries shorter than 2 chars', async () => {
    render(<EntitySearch />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'T' } });
    // Wait for debounce
    await new Promise((r) => setTimeout(r, 350));
    expect(mockSearch).not.toHaveBeenCalled();
  });

  it('calls search API after debounce', async () => {
    mockSearch.mockResolvedValue([
      {
        id: 'e1', entity_type: 'Company', name: 'TSMC',
        canonical_name: 'tsmc', tags: ['semiconductor'],
        created_at: null, updated_at: null,
      },
    ]);

    render(<EntitySearch />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'TSM' } });

    await waitFor(() => {
      expect(mockSearch).toHaveBeenCalledWith('TSM', undefined, 10);
    });
  });

  it('shows results dropdown', async () => {
    mockSearch.mockResolvedValue([
      {
        id: 'e1', entity_type: 'Company', name: 'TSMC Semiconductor',
        canonical_name: 'tsmc', tags: [],
        created_at: null, updated_at: null,
      },
    ]);

    render(<EntitySearch />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'TSM' } });

    await waitFor(() => {
      expect(screen.getByText('TSMC Semiconductor')).toBeInTheDocument();
    });
  });

  it('calls onSelect when clicking a result', async () => {
    const entity = {
      id: 'e1', entity_type: 'Company', name: 'TSMC',
      canonical_name: 'tsmc', tags: [],
      created_at: null, updated_at: null,
    };
    mockSearch.mockResolvedValue([entity]);
    const onSelect = vi.fn();

    render(<EntitySearch onSelect={onSelect} />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'TSM' } });

    await waitFor(() => {
      expect(screen.getByText('TSMC')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('TSMC'));
    expect(onSelect).toHaveBeenCalledWith(entity);
  });

  it('shows entity type label in results', async () => {
    mockSearch.mockResolvedValue([
      {
        id: 'e1', entity_type: 'Company', name: 'TSMC',
        canonical_name: 'tsmc', tags: [],
        created_at: null, updated_at: null,
      },
    ]);

    render(<EntitySearch />);
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'TSM' } });

    await waitFor(() => {
      expect(screen.getByText('Company')).toBeInTheDocument();
    });
  });

  it('closes dropdown on Escape', async () => {
    mockSearch.mockResolvedValue([
      {
        id: 'e1', entity_type: 'Company', name: 'TSMC',
        canonical_name: 'tsmc', tags: [],
        created_at: null, updated_at: null,
      },
    ]);

    render(<EntitySearch />);
    const input = screen.getByRole('combobox');
    fireEvent.change(input, { target: { value: 'TSM' } });

    await waitFor(() => {
      expect(screen.getByText('TSMC')).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByText('TSMC')).not.toBeInTheDocument();
  });
});
