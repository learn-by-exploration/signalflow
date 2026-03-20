'use client';

import { useState } from 'react';
import { useUserStore } from '@/store/userStore';

/**
 * Modal prompt that asks the user for their Telegram Chat ID.
 * Shown when chatId is null (first visit after onboarding).
 */
export function ChatIdPrompt() {
  const { chatId, setChatId } = useUserStore();
  const [input, setInput] = useState('');
  const [dismissed, setDismissed] = useState(false);

  // Don't show if already set or dismissed this session
  if (chatId || dismissed) return null;

  function handleSave() {
    const num = parseInt(input.trim(), 10);
    if (isNaN(num) || num <= 0) return;
    setChatId(num);
  }

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-bg-secondary border border-border-default rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4">
        <h2 className="text-lg font-display font-bold">Connect Your Account</h2>
        <p className="text-sm text-text-secondary leading-relaxed">
          Enter your Telegram Chat ID to sync your portfolio, alerts, and preferences.
          You can get this by messaging <span className="font-mono text-accent-purple">@SignalFlowBot</span> and using the <span className="font-mono text-accent-purple">/start</span> command.
        </p>

        <div>
          <label className="text-xs text-text-muted block mb-1">Telegram Chat ID</label>
          <input
            type="number"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. 123456789"
            className="w-full bg-bg-primary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
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

        <p className="text-[10px] text-text-muted text-center">
          This is stored locally in your browser. No account or sign-up required.
        </p>
      </div>
    </div>
  );
}
