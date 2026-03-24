'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import type { AskResponse } from '@/lib/types';

export function AskAI() {
  const [symbol, setSymbol] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [source, setSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim() || !question.trim()) return;

    setLoading(true);
    setAnswer(null);
    setSource(null);
    try {
      const res = (await api.askAboutSymbol(symbol.trim(), question.trim())) as { data: AskResponse };
      setAnswer(res.data.answer);
      setSource(res.data.source ?? 'claude');
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 429) {
        setAnswer('Too many questions — please wait a minute and try again.');
      } else {
        setAnswer('Could not reach AI right now. Try again shortly.');
      }
      setSource('error');
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
            aria-label="Stock or crypto symbol"
            className="flex-shrink-0 w-36 bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 text-sm font-mono text-text-primary placeholder:text-text-muted"
          />
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask anything..."
            maxLength={500}
            aria-label="Question about the symbol"
            className="flex-1 bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted"
          />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-text-muted">{question.length}/500</span>
          <button
            type="submit"
            disabled={loading || !symbol.trim() || !question.trim()}
            className="px-4 py-1.5 bg-accent-purple text-white rounded-lg text-sm font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-50"
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>
      </form>
      {answer && (
        <div className={`mt-3 p-3 rounded-lg text-sm leading-relaxed ${
          source === 'error'
            ? 'bg-signal-sell/10 text-signal-sell'
            : source === 'fallback'
              ? 'bg-signal-hold/10 text-text-secondary'
              : 'bg-bg-secondary text-text-secondary'
        }`}>
          {source === 'fallback' && (
            <p className="text-xs text-signal-hold mb-1">⚠️ AI budget exhausted — showing cached data</p>
          )}
          {answer}
        </div>
      )}
    </div>
  );
}
