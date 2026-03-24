import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ShareButton } from '@/components/signals/ShareButton';

// Mock api
vi.mock('@/lib/api', () => ({
  api: {
    shareSignal: vi.fn(),
  },
}));

import { api } from '@/lib/api';
const mockShareSignal = api.shareSignal as ReturnType<typeof vi.fn>;

// Mock clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
});

beforeEach(() => {
  mockShareSignal.mockReset();
  (navigator.clipboard.writeText as ReturnType<typeof vi.fn>).mockClear();
});

describe('ShareButton', () => {
  it('renders "Share" button initially', () => {
    render(<ShareButton signalId="test-id" />);
    expect(screen.getByText('🔗 Share')).toBeInTheDocument();
  });

  it('shows "Link copied!" after successful share', async () => {
    mockShareSignal.mockResolvedValue({ data: { share_id: 'abc123' } });
    render(<ShareButton signalId="test-id" />);
    fireEvent.click(screen.getByText('🔗 Share'));

    await waitFor(() => {
      expect(screen.getByText('Link copied!')).toBeInTheDocument();
    });
  });

  it('copies URL to clipboard', async () => {
    mockShareSignal.mockResolvedValue({ data: { share_id: 'abc123' } });
    render(<ShareButton signalId="test-id" />);
    fireEvent.click(screen.getByText('🔗 Share'));

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
        expect.stringContaining('/shared/abc123'),
      );
    });
  });

  it('shows loading state while sharing', async () => {
    let resolve: (value: unknown) => void;
    mockShareSignal.mockReturnValue(new Promise((r) => { resolve = r; }));

    render(<ShareButton signalId="test-id" />);
    fireEvent.click(screen.getByText('🔗 Share'));
    expect(screen.getByText('...')).toBeInTheDocument();

    resolve!({ data: { share_id: 'x' } });
    await waitFor(() => {
      expect(screen.getByText('Link copied!')).toBeInTheDocument();
    });
  });

  it('stays as Share button on API failure', async () => {
    mockShareSignal.mockRejectedValue(new Error('fail'));
    render(<ShareButton signalId="test-id" />);
    fireEvent.click(screen.getByText('🔗 Share'));

    await waitFor(() => {
      expect(screen.getByText('🔗 Share')).toBeInTheDocument();
    });
  });
});
