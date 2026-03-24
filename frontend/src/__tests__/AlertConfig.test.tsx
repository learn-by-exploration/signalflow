import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AlertConfigModal } from '@/components/alerts/AlertConfig';

describe('AlertConfigModal', () => {
  const defaultProps = {
    config: null,
    onSave: vi.fn(),
    onClose: vi.fn(),
  };

  it('renders alert preferences heading', () => {
    render(<AlertConfigModal {...defaultProps} />);
    expect(screen.getByText('Alert Preferences')).toBeInTheDocument();
  });

  it('renders market toggles', () => {
    render(<AlertConfigModal {...defaultProps} />);
    expect(screen.getByText('Stocks')).toBeInTheDocument();
    expect(screen.getByText('Crypto')).toBeInTheDocument();
    expect(screen.getByText('Forex')).toBeInTheDocument();
  });

  it('renders signal type toggles', () => {
    render(<AlertConfigModal {...defaultProps} />);
    expect(screen.getByText('Strong Buy')).toBeInTheDocument();
    expect(screen.getByText('Buy')).toBeInTheDocument();
    expect(screen.getByText('Sell')).toBeInTheDocument();
    expect(screen.getByText('Strong Sell')).toBeInTheDocument();
  });

  it('renders confidence slider', () => {
    render(<AlertConfigModal {...defaultProps} />);
    const slider = document.querySelector('input[type="range"]') as HTMLInputElement;
    expect(slider).toBeTruthy();
    expect(slider.value).toBe('60'); // default
  });

  it('populates from existing config', () => {
    const config = {
      id: 'cfg-1',
      telegram_chat_id: 123,
      username: 'test',
      markets: ['crypto' as const],
      min_confidence: 80,
      signal_types: ['STRONG_BUY' as const],
      quiet_hours: null,
      is_active: true,
      created_at: '',
      updated_at: '',
    };
    render(<AlertConfigModal config={config} onSave={vi.fn()} onClose={vi.fn()} />);

    const slider = document.querySelector('input[type="range"]') as HTMLInputElement;
    expect(slider.value).toBe('80');
  });

  it('calls onClose when Cancel clicked', () => {
    const onClose = vi.fn();
    render(<AlertConfigModal {...defaultProps} onClose={onClose} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onSave with config data when Save clicked', () => {
    const onSave = vi.fn();
    render(<AlertConfigModal {...defaultProps} onSave={onSave} />);
    fireEvent.click(screen.getByText('Save'));
    expect(onSave).toHaveBeenCalledTimes(1);
    const saved = onSave.mock.calls[0][0];
    expect(saved.markets).toEqual(['stock', 'crypto', 'forex']);
    expect(saved.min_confidence).toBe(60);
    expect(saved.signal_types).toHaveLength(4);
  });

  it('toggles market selection', () => {
    const onSave = vi.fn();
    render(<AlertConfigModal {...defaultProps} onSave={onSave} />);

    // Deselect Stocks
    fireEvent.click(screen.getByText('Stocks'));
    fireEvent.click(screen.getByText('Save'));

    const saved = onSave.mock.calls[0][0];
    expect(saved.markets).not.toContain('stock');
    expect(saved.markets).toContain('crypto');
    expect(saved.markets).toContain('forex');
  });

  it('toggles signal type selection', () => {
    const onSave = vi.fn();
    render(<AlertConfigModal {...defaultProps} onSave={onSave} />);

    // Deselect Buy
    fireEvent.click(screen.getByText('Buy'));
    fireEvent.click(screen.getByText('Save'));

    const saved = onSave.mock.calls[0][0];
    expect(saved.signal_types).not.toContain('BUY');
    expect(saved.signal_types).toContain('STRONG_BUY');
  });

  it('adjusts confidence slider', () => {
    const onSave = vi.fn();
    render(<AlertConfigModal {...defaultProps} onSave={onSave} />);

    const slider = document.querySelector('input[type="range"]') as HTMLInputElement;
    fireEvent.change(slider, { target: { value: '85' } });
    fireEvent.click(screen.getByText('Save'));

    expect(onSave.mock.calls[0][0].min_confidence).toBe(85);
  });
});
