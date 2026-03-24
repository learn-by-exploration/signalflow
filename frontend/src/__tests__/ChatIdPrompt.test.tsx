import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatIdPrompt } from '@/components/shared/ChatIdPrompt';
import { useUserStore } from '@/store/userStore';

// Mock localStorage
const store: Record<string, string> = {};
Object.defineProperty(globalThis, 'localStorage', {
  value: {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, val: string) => { store[key] = val; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
  },
  writable: true,
});

beforeEach(() => {
  Object.keys(store).forEach((k) => delete store[k]);
  useUserStore.setState({ chatId: null });
});

describe('ChatIdPrompt', () => {
  it('does not show before 3rd visit', () => {
    store['signalflow_visit_count'] = '1';
    const { container } = render(<ChatIdPrompt />);
    expect(container.innerHTML).toBe('');
  });

  it('shows on 3rd visit when no chatId is set', () => {
    store['signalflow_visit_count'] = '2'; // will become 3
    render(<ChatIdPrompt />);
    expect(screen.getByText('Connect Your Account')).toBeInTheDocument();
  });

  it('does not show when chatId is already set', () => {
    store['signalflow_visit_count'] = '5';
    useUserStore.setState({ chatId: 12345 });
    const { container } = render(<ChatIdPrompt />);
    expect(container.innerHTML).toBe('');
  });

  it('dismisses on "Skip for now" click', () => {
    store['signalflow_visit_count'] = '5';
    render(<ChatIdPrompt />);
    expect(screen.getByText('Connect Your Account')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Skip for now'));
    expect(screen.queryByText('Connect Your Account')).not.toBeInTheDocument();
  });

  it('saves chat ID on valid input + Save click', () => {
    store['signalflow_visit_count'] = '5';
    render(<ChatIdPrompt />);
    fireEvent.change(screen.getByPlaceholderText('e.g. 123456789'), { target: { value: '999888' } });
    fireEvent.click(screen.getByText('Save'));
    expect(useUserStore.getState().chatId).toBe(999888);
  });

  it('Save button is disabled with empty input', () => {
    store['signalflow_visit_count'] = '5';
    render(<ChatIdPrompt />);
    expect(screen.getByText('Save')).toBeDisabled();
  });

  it('increments visit count in localStorage', () => {
    store['signalflow_visit_count'] = '4';
    render(<ChatIdPrompt />);
    expect(store['signalflow_visit_count']).toBe('5');
  });
});
