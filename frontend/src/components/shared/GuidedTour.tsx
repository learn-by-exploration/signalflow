'use client';

import { useState, useEffect, useCallback } from 'react';

interface TourStep {
  target: string;
  title: string;
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

const TOUR_STEPS: TourStep[] = [
  {
    target: '[data-tour="market-overview"]',
    title: 'Market Overview',
    content: 'This bar shows live prices for stocks, crypto, and forex. The green dot means data is flowing in real-time.',
    position: 'bottom',
  },
  {
    target: '[data-tour="win-rate"]',
    title: 'Signal Performance',
    content: 'See how our AI signals have performed — win rate, average return, and total signals tracked.',
    position: 'bottom',
  },
  {
    target: '[data-tour="signal-feed"]',
    title: 'Active Signals',
    content: 'These are live buy/sell signals from our AI. Each card shows the symbol, direction (▲ buy, ▼ sell), and confidence level. Tap any card to expand it.',
    position: 'top',
  },
  {
    target: '[data-tour="signal-filters"]',
    title: 'Filter by Market',
    content: 'Filter signals by market type — Stocks, Crypto, or Forex. Your filter choice will be saved automatically.',
    position: 'bottom',
  },
];

const STORAGE_KEY = 'signalflow_tour_completed';

export function GuidedTour() {
  const [currentStep, setCurrentStep] = useState(-1);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0, height: 0 });

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const completed = localStorage.getItem(STORAGE_KEY);
    const welcomed = localStorage.getItem('signalflow_welcomed');
    // Start tour after welcome modal has been dismissed and tour not yet done
    if (!completed && welcomed === 'true') {
      const timer = setTimeout(() => setCurrentStep(0), 800);
      return () => clearTimeout(timer);
    }
  }, []);

  const updatePosition = useCallback(() => {
    if (currentStep < 0 || currentStep >= TOUR_STEPS.length) return;
    const step = TOUR_STEPS[currentStep];
    const el = document.querySelector(step.target);
    if (el) {
      const rect = el.getBoundingClientRect();
      setPosition({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height,
      });
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [currentStep]);

  useEffect(() => {
    updatePosition();
    window.addEventListener('resize', updatePosition);
    return () => window.removeEventListener('resize', updatePosition);
  }, [updatePosition]);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleDismiss();
    }
  };

  const handleDismiss = () => {
    localStorage.setItem(STORAGE_KEY, 'true');
    setCurrentStep(-1);
  };

  if (currentStep < 0 || currentStep >= TOUR_STEPS.length) return null;

  const step = TOUR_STEPS[currentStep];
  const isLast = currentStep === TOUR_STEPS.length - 1;

  // Calculate tooltip position
  const tooltipStyle: React.CSSProperties = {};
  if (step.position === 'bottom') {
    tooltipStyle.top = position.top + position.height + 12;
    tooltipStyle.left = Math.max(16, position.left);
  } else if (step.position === 'top') {
    tooltipStyle.top = position.top - 12;
    tooltipStyle.left = Math.max(16, position.left);
    tooltipStyle.transform = 'translateY(-100%)';
  }

  return (
    <div className="fixed inset-0 z-[100]" role="dialog" aria-label="Guided tour">
      {/* Overlay */}
      <div className="absolute inset-0 bg-black/60" onClick={handleDismiss} />

      {/* Highlight spotlight */}
      <div
        className="absolute z-[101] rounded-lg ring-2 ring-accent-purple ring-offset-2 ring-offset-transparent pointer-events-none transition-all duration-300"
        style={{
          top: position.top - 4,
          left: position.left - 4,
          width: position.width + 8,
          height: position.height + 8,
        }}
      />

      {/* Tooltip */}
      <div
        className="absolute z-[102] max-w-xs w-full bg-bg-secondary border border-accent-purple/30 rounded-xl p-4 shadow-2xl transition-all duration-300"
        style={tooltipStyle}
      >
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-display font-bold text-accent-purple">{step.title}</h3>
          <span className="text-[10px] text-text-muted font-mono">
            {currentStep + 1}/{TOUR_STEPS.length}
          </span>
        </div>
        <p className="text-sm text-text-secondary leading-relaxed mb-4">{step.content}</p>
        <div className="flex items-center justify-between">
          <button
            onClick={handleDismiss}
            className="text-xs text-text-muted hover:text-text-secondary transition-colors"
          >
            Skip tour
          </button>
          <button
            onClick={handleNext}
            className="px-4 py-1.5 bg-accent-purple text-white rounded-lg text-xs font-medium hover:bg-accent-purple/90 transition-colors"
          >
            {isLast ? 'Got it!' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
