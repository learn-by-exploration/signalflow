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
    <div className="rounded-xl bg-bg-card border border-border-default p-4">
      <h3 className="text-sm font-display font-semibold mb-3">🤖 Ask AI About a Symbol</h3>
      <form onSubmit={handleAsk} className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="Symbol (e.g. HDFCBANK)"
            className="flex-shrink-0 w-36 bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
          />
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything..."
            maxLength={500}
            className="flex-1 bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !symbol.trim() || !question.trim()}
          className="w-full bg-accent-purple text-white py-2 rounded-lg text-sm font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-50"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
      {answer && (
        <div className="mt-3 p-3 bg-bg-secondary rounded-lg text-sm text-text-secondary leading-relaxed">
          {answer}
        </div>
      )}
    </div>
  );
}
