'use client';

import { KEYBOARD_SHORTCUTS } from '@/hooks/useKeyboardShortcuts';
import { FocusTrap } from './FocusTrap';

interface KeyboardHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function KeyboardHelpModal({ isOpen, onClose }: KeyboardHelpModalProps) {
  // Don't show on touch devices
  if (!isOpen) return null;
  if (typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)) return null;

  return (
    <FocusTrap isOpen={isOpen} onClose={onClose}>
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard Shortcuts"
        className="bg-bg-secondary border border-border-default rounded-xl p-6 max-w-sm w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-semibold text-text-primary">Keyboard Shortcuts</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">✕</button>
        </div>
        <div className="space-y-2">
          {KEYBOARD_SHORTCUTS.map((s) => (
            <div key={s.key} className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">{s.description}</span>
              <kbd className="bg-bg-card border border-border-default rounded px-2 py-0.5 text-xs font-mono text-text-primary">
                {s.key}
              </kbd>
            </div>
          ))}
        </div>
        <p className="text-xs text-text-muted mt-4">Press <kbd className="font-mono">?</kbd> to toggle this panel</p>
      </div>
    </div>
    </FocusTrap>
  );
}
