import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SignalBadge } from '@/components/signals/SignalBadge';

describe('SignalBadge', () => {
  it('renders STRONG_BUY with ▲▲ icon', () => {
    render(<SignalBadge signalType="STRONG_BUY" />);
    expect(screen.getByText(/STRONG BUY/)).toBeInTheDocument();
    expect(screen.getByText('▲▲')).toBeInTheDocument();
  });

  it('renders BUY with ▲ icon', () => {
    render(<SignalBadge signalType="BUY" />);
    expect(screen.getByText(/BUY/)).toBeInTheDocument();
    expect(screen.getByText('▲')).toBeInTheDocument();
  });

  it('renders HOLD with ◆ icon', () => {
    render(<SignalBadge signalType="HOLD" />);
    expect(screen.getByText(/HOLD/)).toBeInTheDocument();
    expect(screen.getByText('◆')).toBeInTheDocument();
  });

  it('renders SELL with ▼ icon', () => {
    render(<SignalBadge signalType="SELL" />);
    expect(screen.getByText(/SELL/)).toBeInTheDocument();
    expect(screen.getByText('▼')).toBeInTheDocument();
  });

  it('renders STRONG_SELL with ▼▼ icon', () => {
    render(<SignalBadge signalType="STRONG_SELL" />);
    expect(screen.getByText(/STRONG SELL/)).toBeInTheDocument();
    expect(screen.getByText('▼▼')).toBeInTheDocument();
  });

  it('has accessible role and label', () => {
    render(<SignalBadge signalType="BUY" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('aria-label', 'Signal: BUY');
  });

  it('hides icon from screen readers', () => {
    render(<SignalBadge signalType="BUY" />);
    const icon = screen.getByText('▲');
    expect(icon).toHaveAttribute('aria-hidden', 'true');
  });
});
