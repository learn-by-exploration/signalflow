'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { AskResponse } from '@/lib/types';

export function AskAI() {
  const [symbol, setSymbol] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim() || !question.trim()) return;

    setLoading(true);
    setAnswer(null);
    try {
      const res = (await api.askAboutSymbol(symbol.trim(), question.trim())) as { data: AskResponse };
      setAnswer(res.data.answer);
    } catch {
      setAnswer('Failed to get a response. Try again later.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg bg-[var(--bg-card)] border border-[var(--border-default)] p-4">
      <h3 className="text-sm font-semibold mb-3">🤖 Ask AI About a Symbol</h3>
      <form onSubmit={handleAsk} className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Symbol (e.g. HDFCBANK)"
            className="flex-shrink-0 w-36 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded px-3 py-1.5 text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-purple)]"
          />
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything..."
            maxLength={500}
            className="flex-1 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded px-3 py-1.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-purple)]"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !symbol.trim() || !question.trim()}
          className="w-full bg-[var(--accent-purple)] text-white py-2 rounded text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
      {answer && (
        <div className="mt-3 p-3 bg-[var(--bg-secondary)] rounded text-sm text-[var(--text-secondary)] leading-relaxed">
          {answer}
        </div>
      )}
    </div>
  );
}
