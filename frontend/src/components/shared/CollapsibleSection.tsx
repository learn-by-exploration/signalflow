'use client';

import { useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  storageKey?: string;
}

export function CollapsibleSection({ title, defaultOpen = false, children, storageKey }: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(() => {
    if (storageKey && typeof window !== 'undefined') {
      const stored = sessionStorage.getItem(storageKey);
      if (stored !== null) return stored === 'true';
    }
    return defaultOpen;
  });

  function toggle() {
    const next = !isOpen;
    setIsOpen(next);
    if (storageKey && typeof window !== 'undefined') {
      sessionStorage.setItem(storageKey, String(next));
    }
  }

  return (
    <div className="border border-border-default rounded-xl overflow-hidden">
      <button
        onClick={toggle}
        aria-expanded={isOpen}
        className="w-full flex items-center justify-between px-4 py-3 text-left text-sm font-display font-semibold text-text-secondary hover:bg-bg-card transition-colors touch-target"
      >
        {title}
        <svg
          className={`w-4 h-4 text-text-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <div
        className="grid transition-all duration-200 ease-in-out"
        style={{ gridTemplateRows: isOpen ? '1fr' : '0fr' }}
      >
        <div className="overflow-hidden">
          <div className="px-4 pb-4 pt-1">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
