import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { TargetProgressBar } from '@/components/signals/TargetProgressBar';
import type { Signal } from '@/lib/types';

function makeSignal(overrides: Partial<Signal> = {}): Signal {
  return {
    id: 'sig-1',
    symbol: 'HDFCBANK.NS',
    market_type: 'stock',
    signal_type: 'BUY',
    confidence: 72,
    current_price: '100.00',
    target_price: '120.00',
    stop_loss: '90.00',
    timeframe: '2-4 weeks',
    ai_reasoning: 'Test.',
    technical_data: {},
    sentiment_data: null,
    is_active: true,
    created_at: '2026-03-20T10:30:00Z',
    expires_at: null,
    ...overrides,
  };
}

describe('TargetProgressBar', () => {
  it('returns null when stop loss is zero', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ stop_loss: '0' })} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('returns null when target price is zero', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ target_price: '0' })} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('returns null when target equals stop (division by zero)', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ target_price: '100', stop_loss: '100' })} />,
    );
    expect(container.innerHTML).toBe('');
  });

  it('renders the progress bar for valid signal', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal()} />,
    );
    expect(container.innerHTML).not.toBe('');
  });

  it('shows Stop and Target labels', () => {
    const { getByText } = render(
      <TargetProgressBar signal={makeSignal()} />,
    );
    expect(getByText('Stop')).toBeInTheDocument();
    expect(getByText('Target')).toBeInTheDocument();
  });

  it('positions marker at ~33% when price is at 1/3 of range (BUY)', () => {
    // stop=90, target=120, current=100 → progress = ((100-90)/(120-90))*100 = 33.33%
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ current_price: '100', stop_loss: '90', target_price: '120' })} />,
    );
    const marker = container.querySelector('[style*="left"]');
    expect(marker).toBeTruthy();
    // progress is ~33.33%
    const style = marker!.getAttribute('style') || '';
    expect(style).toContain('33.33');
  });

  it('positions marker at 0% when price equals stop', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ current_price: '90' })} />,
    );
    const marker = container.querySelector('[style*="left"]');
    const style = marker!.getAttribute('style') || '';
    expect(style).toContain('0%');
  });

  it('positions marker at 100% when price equals target', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ current_price: '120' })} />,
    );
    const marker = container.querySelector('[style*="left"]');
    const style = marker!.getAttribute('style') || '';
    expect(style).toContain('100%');
  });

  it('clamps progress at 0% when price is below stop', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ current_price: '80' })} />,
    );
    const marker = container.querySelector('[style*="left"]');
    const style = marker!.getAttribute('style') || '';
    expect(style).toContain('0%');
  });

  it('clamps progress at 100% when price is above target', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ current_price: '130' })} />,
    );
    const marker = container.querySelector('[style*="left"]');
    const style = marker!.getAttribute('style') || '';
    expect(style).toContain('100%');
  });

  it('uses livePrice when provided instead of signal price', () => {
    // livePrice=105, stop=90, target=120 → progress = ((105-90)/30)*100 = 50%
    const { container } = render(
      <TargetProgressBar signal={makeSignal()} livePrice={105} />,
    );
    const marker = container.querySelector('[style*="left"]');
    const style = marker!.getAttribute('style') || '';
    expect(style).toContain('50%');
  });

  it('uses BUY gradient for BUY signals (red to green)', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ signal_type: 'BUY' })} />,
    );
    const gradient = container.querySelector('[style*="linear-gradient"]');
    const style = gradient!.getAttribute('style') || '';
    // jsdom converts hex to rgb
    expect(style).toContain('linear-gradient');
    expect(style).toContain('rgb(255, 82, 82)'); // #FF5252
    expect(style).toContain('rgb(0, 230, 118)'); // #00E676
  });

  it('uses reversed gradient for SELL signals (green to red)', () => {
    const { container } = render(
      <TargetProgressBar signal={makeSignal({ signal_type: 'SELL' })} />,
    );
    const gradient = container.querySelector('[style*="linear-gradient"]');
    const style = gradient!.getAttribute('style') || '';
    // SELL gradient: green → yellow → red
    expect(style).toContain('linear-gradient');
    expect(style).toContain('rgb(0, 230, 118)');
    expect(style).toContain('rgb(255, 82, 82)');
  });
});
