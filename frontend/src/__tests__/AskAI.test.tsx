import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AskAI } from '@/components/signals/AskAI';

// Mock the api module
vi.mock('@/lib/api', () => ({
  api: {
    askAboutSymbol: vi.fn(),
  },
}));

import { api } from '@/lib/api';

const mockAsk = api.askAboutSymbol as ReturnType<typeof vi.fn>;

beforeEach(() => {
  mockAsk.mockReset();
});

describe('AskAI', () => {
  it('renders the form with symbol and question inputs', () => {
    render(<AskAI />);
    expect(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask anything...')).toBeInTheDocument();
  });

  it('shows character count for the question', () => {
    render(<AskAI />);
    expect(screen.getByText('0/500')).toBeInTheDocument();
  });

  it('updates character count as user types', () => {
    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'Hello' } });
    expect(screen.getByText('5/500')).toBeInTheDocument();
  });

  it('auto-uppercases the symbol input', () => {
    render(<AskAI />);
    const input = screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)');
    fireEvent.change(input, { target: { value: 'hdfcbank' } });
    expect(input).toHaveValue('HDFCBANK');
  });

  it('submit button is disabled when inputs are empty', () => {
    render(<AskAI />);
    const btn = screen.getByRole('button', { name: /ask/i });
    expect(btn).toBeDisabled();
  });

  it('submit button is disabled when only symbol is filled', () => {
    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    expect(screen.getByRole('button', { name: /ask/i })).toBeDisabled();
  });

  it('submit button is enabled when both fields are filled', () => {
    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'What is the outlook?' } });
    expect(screen.getByRole('button', { name: /ask/i })).not.toBeDisabled();
  });

  it('shows answer text after successful API call', async () => {
    mockAsk.mockResolvedValue({ data: { answer: 'BTC looks bullish.', source: 'claude' } });

    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'Outlook?' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText('BTC looks bullish.')).toBeInTheDocument();
    });
  });

  it('shows rate limit message on 429 error', async () => {
    mockAsk.mockRejectedValue({ response: { status: 429 } });

    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'What?' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText(/Too many questions/)).toBeInTheDocument();
    });
  });

  it('shows fallback message on other errors', async () => {
    mockAsk.mockRejectedValue(new Error('Network error'));

    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'Why?' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText(/Could not reach AI/)).toBeInTheDocument();
    });
  });

  it('shows "Thinking..." while loading', async () => {
    let resolve: (value: unknown) => void;
    mockAsk.mockReturnValue(new Promise((r) => { resolve = r; }));

    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'Test' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    expect(screen.getByText('Thinking...')).toBeInTheDocument();

    // Resolve to cleanup
    resolve!({ data: { answer: 'done', source: 'claude' } });
    await waitFor(() => {
      expect(screen.getByText('done')).toBeInTheDocument();
    });
  });

  it('shows budget warning when source is fallback', async () => {
    mockAsk.mockResolvedValue({ data: { answer: 'Cached response.', source: 'fallback' } });

    render(<AskAI />);
    fireEvent.change(screen.getByPlaceholderText('Symbol (e.g. HDFCBANK)'), { target: { value: 'BTC' } });
    fireEvent.change(screen.getByPlaceholderText('Ask anything...'), { target: { value: 'Info?' } });
    fireEvent.click(screen.getByRole('button', { name: /ask/i }));

    await waitFor(() => {
      expect(screen.getByText(/AI budget exhausted/)).toBeInTheDocument();
    });
  });
});
