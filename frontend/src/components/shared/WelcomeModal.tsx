'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const STORAGE_KEY = 'signalflow_welcomed';

const STEPS = [
  {
    emoji: '📊',
    title: 'Real-Time Signals',
    desc: 'Get AI-powered market analysis for Indian stocks, crypto, and forex — updated every 5 minutes.',
  },
  {
    emoji: '🤖',
    title: 'AI + Technical Analysis',
    desc: 'Each signal combines 5 technical indicators (RSI, MACD, Bollinger, Volume, SMA) with Claude AI sentiment analysis.',
  },
  {
    emoji: '🎯',
    title: 'Clear Targets & Stop-Loss',
    desc: 'Every signal includes entry price, target, and stop-loss — so you always know your risk before entering.',
  },
  {
    emoji: '📱',
    title: 'Alerts via Telegram',
    desc: 'Get instant alerts on your phone. Configure which markets and confidence levels matter to you.',
  },
];

export function WelcomeModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const welcomed = localStorage.getItem(STORAGE_KEY);
      if (!welcomed) {
        setIsOpen(true);
      }
    }
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, 'true');
    setIsOpen(false);
  }

  if (!isOpen) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-bg-secondary border border-border-default rounded-2xl max-w-md w-full p-6 shadow-2xl">
        {/* Progress dots */}
        <div className="flex justify-center gap-1.5 mb-6">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 rounded-full transition-all ${
                i === step ? 'w-6 bg-accent-purple' : 'w-1.5 bg-border-default'
              }`}
            />
          ))}
        </div>

        {/* Content */}
        <div className="text-center mb-6">
          <div className="text-5xl mb-4">{current.emoji}</div>
          <h2 className="text-xl font-display font-bold mb-2">{current.title}</h2>
          <p className="text-sm text-text-secondary leading-relaxed">{current.desc}</p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={dismiss}
            className="text-xs text-text-muted hover:text-text-secondary transition-colors"
          >
            Skip
          </button>

          <div className="flex gap-2">
            {step > 0 && (
              <button
                onClick={() => setStep(step - 1)}
                className="px-4 py-2 text-sm border border-border-default rounded-lg text-text-secondary hover:border-border-hover transition-colors"
              >
                Back
              </button>
            )}
            {isLast ? (
              <button
                onClick={dismiss}
                className="px-5 py-2 text-sm bg-accent-purple text-white rounded-lg font-medium hover:bg-accent-purple/90 transition-colors"
              >
                Get Started →
              </button>
            ) : (
              <button
                onClick={() => setStep(step + 1)}
                className="px-5 py-2 text-sm bg-accent-purple text-white rounded-lg font-medium hover:bg-accent-purple/90 transition-colors"
              >
                Next
              </button>
            )}
          </div>
        </div>

        {/* Learn more link on last step */}
        {isLast && (
          <div className="text-center mt-4">
            <Link
              href="/how-it-works"
              onClick={dismiss}
              className="text-xs text-accent-purple hover:underline"
            >
              💡 Want the full breakdown? Read How It Works
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
