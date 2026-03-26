'use client';

import { useState, useEffect } from 'react';
import { useUserStore } from '@/store/userStore';
import { FocusTrap } from './FocusTrap';

/**
 * Modal prompt that asks the user for their Telegram Chat ID.
 * Delayed until the 3rd session to avoid overwhelming new users.
 */
export function ChatIdPrompt() {
  const { chatId, setChatId } = useUserStore();
  const [input, setInput] = useState('');
  const [dismissed, setDismissed] = useState(false);
  const [shouldShow, setShouldShow] = useState(false);

  // Track visit count — only show on 3rd+ visit
  useEffect(() => {
    const key = 'signalflow_visit_count';
    const count = parseInt(localStorage.getItem(key) ?? '0', 10) + 1;
    localStorage.setItem(key, String(count));
    if (count >= 3) setShouldShow(true);
  }, []);

  // Don't show if already set, dismissed, or too early
  if (chatId || dismissed || !shouldShow) return null;

  function handleSave() {
    const num = parseInt(input.trim(), 10);
    if (isNaN(num) || num <= 0) return;
    setChatId(num);
  }

  return (
    <FocusTrap isOpen={!chatId && !dismissed && shouldShow} onClose={() => setDismissed(true)}>
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div role="dialog" aria-modal="true" aria-label="Connect Your Account" className="bg-bg-secondary border border-border-default rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4">
        <h2 className="text-lg font-display font-bold">Connect Your Account</h2>
        <p className="text-sm text-text-secondary leading-relaxed">
          Enter your Telegram Chat ID to sync your portfolio, alerts, and preferences.
          You can get this by messaging <span className="font-mono text-accent-purple">@SignalFlowBot</span> and using the <span className="font-mono text-accent-purple">/start</span> command.
        </p>

        <div>
          <label className="text-xs text-text-muted block mb-1">Telegram Chat ID</label>
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. 123456789"
            aria-label="Telegram Chat ID"
            className="w-full bg-bg-primary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted"
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
          />
        </div>

        <div className="flex items-center justify-between">
          <button
            onClick={() => setDismissed(true)}
            className="text-xs text-text-muted hover:text-text-secondary transition-colors"
          >
            Skip for now
          </button>
          <button
            onClick={handleSave}
            disabled={!input.trim() || isNaN(parseInt(input.trim(), 10))}
            className="px-5 py-2 text-sm bg-accent-purple text-white rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-40"
          >
            Save
          </button>
        </div>

        <p className="text-xs text-text-muted text-center">
          This is stored locally in your browser. No account or sign-up required.
        </p>
      </div>
    </div>
    </FocusTrap>
  );
}
