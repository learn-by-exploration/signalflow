import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('@/lib/api', () => ({
  api: {
    getSignals: vi.fn(),
  },
}));

vi.mock('@/components/shared/LoadingSpinner', () => ({
  LoadingSpinner: () => <div data-testid="loading-spinner" />,
}));

import { api } from '@/lib/api';

beforeEach(() => {
  vi.mocked(api.getSignals).mockReset();
});

describe('MorningBriefPage', () => {
  it('shows loading state initially', async () => {
    vi.mocked(api.getSignals).mockReturnValue(new Promise(() => {}));
    const { default: Page } = await import('@/app/brief/page');
    render(<Page />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders Daily Brief heading on success', async () => {
    vi.mocked(api.getSignals).mockResolvedValue({
      data: [
        { symbol: 'RELIANCE.NS', signal_type: 'STRONG_BUY', confidence: 90, market_type: 'stock' },
      ],
    });
    const { default: Page } = await import('@/app/brief/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Daily Brief/i)).toBeInTheDocument();
    });
  });

  it('renders top signals section', async () => {
    vi.mocked(api.getSignals).mockResolvedValue({
      data: [
        { symbol: 'RELIANCE.NS', signal_type: 'BUY', confidence: 78, market_type: 'stock' },
      ],
    });
    const { default: Page } = await import('@/app/brief/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Top Signals/i)).toBeInTheDocument();
      expect(screen.getByText('RELIANCE')).toBeInTheDocument();
    });
  });

  it('renders market status section', async () => {
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/brief/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Market Status/i)).toBeInTheDocument();
    });
  });

  it('shows error message on failure', async () => {
    vi.mocked(api.getSignals).mockRejectedValue(new Error('network'));
    const { default: Page } = await import('@/app/brief/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText(/Could not load/i)).toBeInTheDocument();
    });
  });

  it('has navigation links', async () => {
    vi.mocked(api.getSignals).mockResolvedValue({ data: [] });
    const { default: Page } = await import('@/app/brief/page');
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('← Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Signal History →')).toBeInTheDocument();
    });
  });
});
