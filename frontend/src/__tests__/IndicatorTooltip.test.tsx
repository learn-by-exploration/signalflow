import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IndicatorTooltip } from '@/components/shared/IndicatorTooltip';

describe('IndicatorTooltip', () => {
  it('renders children text', () => {
    render(<IndicatorTooltip term="RSI">RSI (14)</IndicatorTooltip>);
    expect(screen.getByText('RSI (14)')).toBeInTheDocument();
  });

  it('shows info icon for known terms', () => {
    const { container } = render(<IndicatorTooltip term="MACD">MACD</IndicatorTooltip>);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('shows tooltip on hover', async () => {
    const user = userEvent.setup();
    render(<IndicatorTooltip term="RSI">RSI</IndicatorTooltip>);
    const trigger = screen.getByRole('button');
    await user.hover(trigger);
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByRole('tooltip')).toHaveTextContent(/Relative Strength Index/);
  });

  it('shows tooltip on focus', async () => {
    const user = userEvent.setup();
    render(<IndicatorTooltip term="MACD">MACD</IndicatorTooltip>);
    const trigger = screen.getByRole('button');
    await user.tab();
    // trigger should receive focus and show tooltip
    expect(trigger).toHaveFocus();
    expect(screen.getByRole('tooltip')).toHaveTextContent(/Moving Average Convergence/);
  });

  it('renders children directly if term not found', () => {
    const { container } = render(
      <IndicatorTooltip term="UnknownTerm">Unknown</IndicatorTooltip>
    );
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    // No info icon for unknown terms
    expect(container.querySelector('svg')).not.toBeInTheDocument();
  });

  it('has aria-describedby when tooltip is visible', async () => {
    const user = userEvent.setup();
    render(<IndicatorTooltip term="Volume">Volume</IndicatorTooltip>);
    const trigger = screen.getByRole('button');
    await user.hover(trigger);
    expect(trigger).toHaveAttribute('aria-describedby', 'tooltip-Volume');
  });
});
