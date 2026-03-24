import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SettingsPanel } from '@/components/shared/SettingsPanel';

describe('SettingsPanel', () => {
  it('does not render when closed', () => {
    render(<SettingsPanel isOpen={false} onClose={() => {}} />);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('renders when open', () => {
    render(<SettingsPanel isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('has View Mode options', () => {
    render(<SettingsPanel isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('Simple')).toBeInTheDocument();
    expect(screen.getByText('Standard')).toBeInTheDocument();
  });

  it('has Text Size options', () => {
    render(<SettingsPanel isOpen={true} onClose={() => {}} />);
    expect(screen.getByText('Small')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Large')).toBeInTheDocument();
  });

  it('calls onClose when Done is clicked', async () => {
    const user = userEvent.setup();
    const onClose = { fn: () => {} };
    const spy = (onClose.fn = vi.fn());
    render(<SettingsPanel isOpen={true} onClose={spy} />);
    await user.click(screen.getByText('Done'));
    expect(spy).toHaveBeenCalled();
  });

  it('calls onClose when overlay clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<SettingsPanel isOpen={true} onClose={onClose} />);
    // Click the overlay (the outer div)
    const overlay = screen.getByText('Settings').closest('.fixed');
    if (overlay) await user.click(overlay);
    expect(onClose).toHaveBeenCalled();
  });
});
