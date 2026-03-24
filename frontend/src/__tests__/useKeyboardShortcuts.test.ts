import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

function fireKey(key: string, target?: Partial<HTMLElement>) {
  const event = new KeyboardEvent('keydown', { key, bubbles: true });
  if (target) {
    Object.defineProperty(event, 'target', { value: target });
  }
  document.dispatchEvent(event);
}

describe('useKeyboardShortcuts', () => {
  it('calls onFilterChange with "all" when 1 is pressed', () => {
    const onFilterChange = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFilterChange }));
    fireKey('1');
    expect(onFilterChange).toHaveBeenCalledWith('all');
  });

  it('calls onFilterChange with "stock" when 2 is pressed', () => {
    const onFilterChange = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFilterChange }));
    fireKey('2');
    expect(onFilterChange).toHaveBeenCalledWith('stock');
  });

  it('calls onFilterChange with "crypto" when 3 is pressed', () => {
    const onFilterChange = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFilterChange }));
    fireKey('3');
    expect(onFilterChange).toHaveBeenCalledWith('crypto');
  });

  it('calls onFilterChange with "forex" when 4 is pressed', () => {
    const onFilterChange = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFilterChange }));
    fireKey('4');
    expect(onFilterChange).toHaveBeenCalledWith('forex');
  });

  it('calls onFocusSearch when / is pressed', () => {
    const onFocusSearch = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFocusSearch }));
    fireKey('/');
    expect(onFocusSearch).toHaveBeenCalled();
  });

  it('toggles help modal on ? key', () => {
    const { result } = renderHook(() => useKeyboardShortcuts());
    expect(result.current.showHelp).toBe(false);

    act(() => { fireKey('?'); });
    expect(result.current.showHelp).toBe(true);

    act(() => { fireKey('?'); });
    expect(result.current.showHelp).toBe(false);
  });

  it('closes help modal on Escape', () => {
    const { result } = renderHook(() => useKeyboardShortcuts());
    act(() => { fireKey('?'); });
    expect(result.current.showHelp).toBe(true);

    act(() => { fireKey('Escape'); });
    expect(result.current.showHelp).toBe(false);
  });

  it('ignores shortcuts when INPUT is focused', () => {
    const onFilterChange = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFilterChange }));
    fireKey('1', { tagName: 'INPUT' });
    expect(onFilterChange).not.toHaveBeenCalled();
  });

  it('ignores shortcuts when TEXTAREA is focused', () => {
    const onFilterChange = vi.fn();
    renderHook(() => useKeyboardShortcuts({ onFilterChange }));
    fireKey('2', { tagName: 'TEXTAREA' });
    expect(onFilterChange).not.toHaveBeenCalled();
  });

  it('allows Escape when INPUT is focused (blurs)', () => {
    const blur = vi.fn();
    renderHook(() => useKeyboardShortcuts());
    fireKey('Escape', { tagName: 'INPUT', blur } as unknown as Partial<HTMLElement>);
    expect(blur).toHaveBeenCalled();
  });
});
