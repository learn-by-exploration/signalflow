/**
 * Tests for EntityLineage component.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { EntityLineage } from '@/components/graph/EntityLineage';

// Mock mkg-api
vi.mock('@/lib/mkg-api', () => ({
  mkgApi: {
    getEntityLineage: vi.fn(),
  },
}));

import { mkgApi } from '@/lib/mkg-api';

const mockLineage = {
  entity_id: 'e-tsmc',
  source_articles: ['article-001', 'article-002'],
  highest_confidence: 0.95,
  extraction_tiers_used: ['tier_1', 'tier_3'],
  data_sources: [
    { source: 'Reuters', article_id: 'article-001', url: 'https://reuters.com/example' },
    { source: 'Bloomberg', article_id: 'article-002' },
  ],
};

describe('EntityLineage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {}),
    );

    const { container } = render(<EntityLineage entityId="e-tsmc" />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('displays lineage data', async () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockResolvedValue(mockLineage);

    render(<EntityLineage entityId="e-tsmc" />);

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // source count
    });

    expect(screen.getByText('95%')).toBeInTheDocument(); // highest confidence
    expect(screen.getByText('Data Sources')).toBeInTheDocument();
  });

  it('shows extraction tier badges', async () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockResolvedValue(mockLineage);

    render(<EntityLineage entityId="e-tsmc" />);

    await waitFor(() => {
      expect(screen.getByText(/Rule-Based/)).toBeInTheDocument();
    });

    expect(screen.getByText(/LLM Extraction/)).toBeInTheDocument();
  });

  it('shows data source entries', async () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockResolvedValue(mockLineage);

    render(<EntityLineage entityId="e-tsmc" />);

    await waitFor(() => {
      expect(screen.getByText('Reuters')).toBeInTheDocument();
    });

    expect(screen.getByText('Bloomberg')).toBeInTheDocument();
  });

  it('shows link for sources with URLs', async () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockResolvedValue(mockLineage);

    render(<EntityLineage entityId="e-tsmc" />);

    await waitFor(() => {
      expect(screen.getByText('Open →')).toBeInTheDocument();
    });

    const link = screen.getByText('Open →');
    expect(link).toHaveAttribute('href', 'https://reuters.com/example');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('handles API failure gracefully', async () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Not found'));

    render(<EntityLineage entityId="e-unknown" />);

    await waitFor(() => {
      expect(screen.getByText(/Lineage data unavailable/)).toBeInTheDocument();
    });
  });

  it('shows seed data message when no sources', async () => {
    (mkgApi.getEntityLineage as ReturnType<typeof vi.fn>).mockResolvedValue({
      entity_id: 'e-seed',
      source_articles: [],
      highest_confidence: 1.0,
      extraction_tiers_used: [],
      data_sources: [],
    });

    render(<EntityLineage entityId="e-seed" />);

    await waitFor(() => {
      expect(screen.getByText(/seed data/)).toBeInTheDocument();
    });
  });
});
