/**
 * Tests for FilterPanel component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterPanel } from '@/components/graph/FilterPanel';
import { useGraphStore } from '@/store/graphStore';

describe('FilterPanel', () => {
  beforeEach(() => {
    useGraphStore.getState().resetFilters();
  });

  it('renders the Filters heading', () => {
    render(<FilterPanel />);
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('renders Entity Types section', () => {
    render(<FilterPanel />);
    expect(screen.getByText('Entity Types')).toBeInTheDocument();
  });

  it('renders all 8 entity type buttons', () => {
    render(<FilterPanel />);
    const types = ['Company', 'Facility', 'Country', 'Person', 'Sector', 'Product', 'Regulation', 'Event'];
    types.forEach((type) => {
      expect(screen.getByText(type)).toBeInTheDocument();
    });
  });

  it('renders Connection Types section', () => {
    render(<FilterPanel />);
    expect(screen.getByText('Connection Types')).toBeInTheDocument();
  });

  it('renders relation type buttons with spaces instead of underscores', () => {
    render(<FilterPanel />);
    expect(screen.getByText('SUPPLIES TO')).toBeInTheDocument();
    expect(screen.getByText('COMPETES WITH')).toBeInTheDocument();
  });

  it('toggles entity type on click', async () => {
    const user = userEvent.setup();
    render(<FilterPanel />);

    const companyBtn = screen.getByText('Company');
    await user.click(companyBtn);

    expect(useGraphStore.getState().filters.entityTypes).toContain('Company');
  });

  it('untoggle entity type on second click', async () => {
    const user = userEvent.setup();
    render(<FilterPanel />);

    const companyBtn = screen.getByText('Company');
    await user.click(companyBtn);
    await user.click(companyBtn);

    expect(useGraphStore.getState().filters.entityTypes).not.toContain('Company');
  });

  it('toggles relation type on click', async () => {
    const user = userEvent.setup();
    render(<FilterPanel />);

    const btn = screen.getByText('SUPPLIES TO');
    await user.click(btn);

    expect(useGraphStore.getState().filters.relationTypes).toContain('SUPPLIES_TO');
  });

  it('renders confidence slider', () => {
    render(<FilterPanel />);
    expect(screen.getByText(/Min Confidence/)).toBeInTheDocument();
  });

  it('shows reset button when filters are active', async () => {
    const user = userEvent.setup();
    render(<FilterPanel />);

    // Initially no reset button
    expect(screen.queryByText('Reset')).not.toBeInTheDocument();

    // Add a filter
    await user.click(screen.getByText('Company'));

    // Reset button should appear
    expect(screen.getByText('Reset')).toBeInTheDocument();
  });

  it('resets filters when reset clicked', async () => {
    const user = userEvent.setup();
    render(<FilterPanel />);

    // Add a filter
    await user.click(screen.getByText('Company'));
    expect(useGraphStore.getState().filters.entityTypes).toContain('Company');

    // Click reset
    await user.click(screen.getByText('Reset'));
    expect(useGraphStore.getState().filters.entityTypes).toHaveLength(0);
  });

  it('updates confidence range via slider', () => {
    render(<FilterPanel />);
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '50' } });
    expect(useGraphStore.getState().filters.confidenceRange[0]).toBe(0.5);
  });
});
