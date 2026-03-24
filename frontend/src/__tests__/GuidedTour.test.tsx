import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { GuidedTour } from '@/components/shared/GuidedTour';

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

describe('GuidedTour', () => {
  beforeEach(() => {
    Object.keys(store).forEach((k) => delete store[k]);
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('does not render when tour already completed', () => {
    store['signalflow_tour_completed'] = 'true';
    store['signalflow_welcomed'] = 'true';
    render(<GuidedTour />);
    act(() => { vi.advanceTimersByTime(1000); });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('does not render when welcome not yet dismissed', () => {
    render(<GuidedTour />);
    act(() => { vi.advanceTimersByTime(1000); });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders tour dialog when welcome completed and tour not done', () => {
    store['signalflow_welcomed'] = 'true';
    render(<GuidedTour />);
    act(() => { vi.advanceTimersByTime(1000); });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Market Overview')).toBeInTheDocument();
    expect(screen.getByText('1/4')).toBeInTheDocument();
  });

  it('has Skip tour and Next buttons', () => {
    store['signalflow_welcomed'] = 'true';
    render(<GuidedTour />);
    act(() => { vi.advanceTimersByTime(1000); });
    expect(screen.getByText('Skip tour')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
  });
});
