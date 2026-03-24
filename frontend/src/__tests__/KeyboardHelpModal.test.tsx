import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { KeyboardHelpModal } from '@/components/shared/KeyboardHelpModal';

vi.mock('@/hooks/useKeyboardShortcuts', () => ({
  KEYBOARD_SHORTCUTS: [
    { key: '1', description: 'All markets' },
    { key: '2', description: 'Stocks only' },
    { key: '/', description: 'Focus search' },
    { key: '?', description: 'Toggle help' },
  ],
}));

describe('KeyboardHelpModal', () => {
  beforeEach(() => {
    // Ensure test environment is detected as non-touch
    Object.defineProperty(navigator, 'maxTouchPoints', { value: 0, configurable: true });
    // Remove ontouchstart if set
    delete (window as Record<string, unknown>).ontouchstart;
  });
  it('returns null when not open', () => {
    const { container } = render(<KeyboardHelpModal isOpen={false} onClose={vi.fn()} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders when open', () => {
    render(<KeyboardHelpModal isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
  });

  it('renders all shortcuts', () => {
    render(<KeyboardHelpModal isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('All markets')).toBeInTheDocument();
    expect(screen.getByText('Stocks only')).toBeInTheDocument();
    expect(screen.getByText('Focus search')).toBeInTheDocument();
    expect(screen.getByText('Toggle help')).toBeInTheDocument();
  });

  it('renders shortcut keys in kbd elements', () => {
    render(<KeyboardHelpModal isOpen={true} onClose={vi.fn()} />);
    const kbds = document.querySelectorAll('kbd');
    // 4 shortcuts + 1 hint kbd
    expect(kbds.length).toBeGreaterThanOrEqual(4);
  });

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn();
    render(<KeyboardHelpModal isOpen={true} onClose={onClose} />);
    fireEvent.click(screen.getByText('✕'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop clicked', () => {
    const onClose = vi.fn();
    render(<KeyboardHelpModal isOpen={true} onClose={onClose} />);
    // Click the overlay (first fixed div)
    const overlay = document.querySelector('.fixed');
    fireEvent.click(overlay!);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not close when inner content clicked', () => {
    const onClose = vi.fn();
    render(<KeyboardHelpModal isOpen={true} onClose={onClose} />);
    fireEvent.click(screen.getByText('Keyboard Shortcuts'));
    expect(onClose).not.toHaveBeenCalled();
  });
});
