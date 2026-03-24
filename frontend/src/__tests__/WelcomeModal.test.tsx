import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WelcomeModal } from '@/components/shared/WelcomeModal';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

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
});

describe('WelcomeModal', () => {
  it('shows the modal on first visit (no localStorage key)', () => {
    render(<WelcomeModal />);
    expect(screen.getByText('Real-Time Signals')).toBeInTheDocument();
  });

  it('does not show modal if already welcomed', () => {
    store['signalflow_welcomed'] = 'true';
    const { container } = render(<WelcomeModal />);
    expect(container.innerHTML).toBe('');
  });

  it('shows first step content', () => {
    render(<WelcomeModal />);
    expect(screen.getByText('Real-Time Signals')).toBeInTheDocument();
    expect(screen.getByText(/AI-powered buy\/sell signals/)).toBeInTheDocument();
  });

  it('advances to next step on "Next" button click', () => {
    render(<WelcomeModal />);
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('AI + Technical Analysis')).toBeInTheDocument();
  });

  it('shows all 4 steps', () => {
    render(<WelcomeModal />);
    expect(screen.getByText('Real-Time Signals')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('AI + Technical Analysis')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('Clear Targets & Stop-Loss')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Next'));
    expect(screen.getByText('Alerts via Telegram')).toBeInTheDocument();
  });

  it('dismisses modal and sets localStorage on Skip', () => {
    render(<WelcomeModal />);
    fireEvent.click(screen.getByText('Skip'));
    expect(store['signalflow_welcomed']).toBe('true');
  });
});
