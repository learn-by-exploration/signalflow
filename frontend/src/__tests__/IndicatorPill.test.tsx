import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IndicatorPill } from '@/components/shared/IndicatorPill';

describe('IndicatorPill', () => {
  it('renders label and value', () => {
    render(<IndicatorPill label="RSI" value="62.7" />);
    expect(screen.getByText('RSI')).toBeInTheDocument();
    expect(screen.getByText('62.7')).toBeInTheDocument();
  });

  it('renders buy signal with green color', () => {
    const { container } = render(<IndicatorPill label="MACD" value="Buy" signal="buy" />);
    const span = container.firstChild as HTMLElement;
    expect(span.style.color).toBe('rgb(102, 187, 106)');
  });

  it('renders sell signal with red color', () => {
    const { container } = render(<IndicatorPill label="RSI" value="Overbought" signal="sell" />);
    const span = container.firstChild as HTMLElement;
    expect(span.style.color).toBe('rgb(239, 83, 80)');
  });

  it('renders neutral signal with hold color', () => {
    const { container } = render(<IndicatorPill label="Vol" value="Normal" signal="neutral" />);
    const span = container.firstChild as HTMLElement;
    expect(span.style.color).toBe('rgb(255, 215, 64)');
  });

  it('defaults to hold color without signal prop', () => {
    const { container } = render(<IndicatorPill label="ATR" value="1.5" />);
    const span = container.firstChild as HTMLElement;
    expect(span.style.color).toBe('rgb(255, 215, 64)');
  });

  it('has font-mono class for value display', () => {
    const { container } = render(<IndicatorPill label="RSI" value="62.7" />);
    const span = container.firstChild as HTMLElement;
    expect(span.className).toContain('font-mono');
  });
});
