import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CookieConsent } from '@/components/shared/CookieConsent';

// Mock localStorage
const store: Record<string, string> = {};
beforeEach(() => {
  Object.keys(store).forEach((k) => delete store[k]);
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: (key: string) => store[key] ?? null,
      setItem: (key: string, value: string) => {
        store[key] = value;
      },
      removeItem: (key: string) => {
        delete store[key];
      },
    },
    writable: true,
  });
});

describe('CookieConsent', () => {
  it('shows consent banner when no prior consent', () => {
    render(<CookieConsent />);
    expect(screen.getByRole('dialog', { name: 'Cookie consent' })).toBeDefined();
  });

  it('hides banner when consent was previously given', () => {
    store['signalflow_cookie_consent'] = 'accepted';
    const { container } = render(<CookieConsent />);
    expect(container.innerHTML).toBe('');
  });

  it('contains Privacy Policy link', () => {
    render(<CookieConsent />);
    const link = screen.getByRole('link', { name: 'Privacy Policy' });
    expect(link.getAttribute('href')).toBe('/privacy');
  });

  it('hides and stores consent when Got it is clicked', () => {
    const { container } = render(<CookieConsent />);
    fireEvent.click(screen.getByText('Got it'));
    expect(store['signalflow_cookie_consent']).toBe('accepted');
    // Component should hide (re-render would return null, but state update happened)
    expect(container.querySelector('[role="dialog"]')).toBeNull();
  });
});
