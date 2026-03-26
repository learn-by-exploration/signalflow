'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FocusTrap } from './FocusTrap';

const STORAGE_KEY = 'signalflow_cookie_consent';

export function CookieConsent() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem(STORAGE_KEY);
    if (!consent) {
      setVisible(true);
    }
  }, []);

  function accept() {
    localStorage.setItem(STORAGE_KEY, 'accepted');
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <FocusTrap isOpen={visible} onClose={accept}>
    <div className="fixed bottom-0 inset-x-0 z-50 p-4" role="dialog" aria-modal="true" aria-label="Cookie consent">
      <div className="max-w-3xl mx-auto bg-bg-secondary border border-border-default rounded-xl p-4 shadow-lg flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <p className="text-xs text-text-secondary flex-1">
          SignalFlow AI uses a session cookie for authentication and localStorage for your
          display preferences. We do not use tracking cookies.{' '}
          <Link href="/privacy" className="text-accent-purple underline hover:text-text-primary">
            Privacy Policy
          </Link>
        </p>
        <button
          onClick={accept}
          className="shrink-0 px-4 py-2 text-xs font-medium bg-accent-purple text-white rounded-lg hover:bg-accent-purple/90 transition-colors"
        >
          Got it
        </button>
      </div>
    </div>
    </FocusTrap>
  );
}
