/**
 * Comprehensive compliance test suite.
 *
 * Verifies that regulatory compliance measures are present and correctly
 * implemented across the frontend. Tests cover:
 * - Disclaimers on all key pages
 * - Consent flow requirements
 * - Legal page existence and content
 * - Language reframing (no BUY/SELL in user-facing labels)
 * - Cookie consent presence
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BADGE_LABELS } from '@/lib/constants';

// ── 1. Language Reframing Compliance ──

describe('Language Reframing Compliance', () => {
  it('BADGE_LABELS does not contain BUY or SELL as standalone labels', () => {
    const labels = Object.values(BADGE_LABELS);
    for (const label of labels) {
      // Labels should use BULLISH/BEARISH, not BUY/SELL
      expect(label).not.toBe('BUY');
      expect(label).not.toBe('SELL');
      expect(label).not.toBe('STRONG BUY');
      expect(label).not.toBe('STRONG SELL');
    }
  });

  it('BADGE_LABELS uses Bullish/Bearish terminology', () => {
    expect(BADGE_LABELS.STRONG_BUY).toContain('BULLISH');
    expect(BADGE_LABELS.BUY).toContain('BULLISH');
    expect(BADGE_LABELS.SELL).toContain('BEARISH');
    expect(BADGE_LABELS.STRONG_SELL).toContain('BEARISH');
  });

  it('HOLD label is unchanged', () => {
    expect(BADGE_LABELS.HOLD).toBe('HOLD');
  });
});

// ── 2. Legal Pages Existence ──

describe('Legal Pages Content', () => {
  it('Privacy Policy page renders with required sections', async () => {
    const { default: PrivacyPage } = await import('@/app/privacy/page');
    render(<PrivacyPage />);
    expect(screen.getByText('Privacy Policy')).toBeDefined();
    expect(screen.getByText('1. Data We Collect')).toBeDefined();
    expect(screen.getByText('4. Your Rights')).toBeDefined();
    expect(screen.getByText('8. Grievance Officer')).toBeDefined();
  });

  it('Terms of Service page renders with SEBI disclaimer', async () => {
    const { default: TermsPage } = await import('@/app/terms/page');
    render(<TermsPage />);
    expect(screen.getByText('Terms of Service')).toBeDefined();
    expect(screen.getByText(/NOT registered with the Securities and Exchange Board/)).toBeDefined();
    expect(screen.getByText('7. Limitation of Liability')).toBeDefined();
  });

  it('Contact page renders with Grievance Officer section', async () => {
    const { default: ContactPage } = await import('@/app/contact/page');
    render(<ContactPage />);
    expect(screen.getAllByText(/Grievance Officer/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/DPDPA 2023/).length).toBeGreaterThan(0);
  });

  it('Refund Policy page renders with key sections', async () => {
    const { default: RefundPage } = await import('@/app/refund-policy/page');
    render(<RefundPage />);
    expect(screen.getByText(/Refund & Cancellation Policy/)).toBeDefined();
    expect(screen.getByText(/Trading losses are not grounds for a refund/i)).toBeDefined();
  });
});

// ── 3. Disclaimer Presence ──

describe('Disclaimer Compliance', () => {
  it('SebiDisclaimer contains NOT registered with SEBI', async () => {
    const { SebiDisclaimer } = await import(
      '@/components/shared/SebiDisclaimer'
    );
    render(<SebiDisclaimer />);
    expect(screen.getByText(/NOT registered with SEBI/)).toBeDefined();
  });

  it('SebiDisclaimer contains links to Privacy, Terms, and Contact', async () => {
    const { SebiDisclaimer } = await import(
      '@/components/shared/SebiDisclaimer'
    );
    render(<SebiDisclaimer />);
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toBeDefined();
    expect(screen.getByRole('link', { name: 'Terms of Service' })).toBeDefined();
    expect(screen.getByRole('link', { name: /Contact/ })).toBeDefined();
  });

  it('SebiDisclaimer uses accessible font size (not 10px)', async () => {
    const { SebiDisclaimer } = await import(
      '@/components/shared/SebiDisclaimer'
    );
    const { container } = render(<SebiDisclaimer />);
    const mainP = container.querySelector('p');
    expect(mainP?.className).toContain('text-xs');
    expect(mainP?.className).not.toContain('text-[10px]');
  });

  it('Pricing page contains risk disclosure', async () => {
    // Need to mock zustand store for pricing page
    const { useTierStore } = await import('@/store/tierStore');
    useTierStore.setState({ tier: 'free', signalsViewedToday: 0 });

    const { default: PricingPage } = await import('@/app/pricing/page');
    render(<PricingPage />);
    expect(screen.getByText(/Risk Disclosure/)).toBeDefined();
    expect(screen.getByText(/NOT registered with SEBI/)).toBeDefined();
  });
});

// ── 4. Consent Flow ──

describe('Consent Flow Compliance', () => {
  beforeEach(() => {
    vi.mock('next-auth/react', () => ({ signIn: vi.fn() }));
    vi.mock('next/navigation', () => ({
      useSearchParams: () => ({ get: () => null }),
    }));
  });

  it('Sign-in page has consent checkbox', async () => {
    const { default: SignInPage } = await import('@/app/auth/signin/page');
    render(<SignInPage />);
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThanOrEqual(1);
  });

  it('Sign-in consent mentions 18+ age requirement', async () => {
    const { default: SignInPage } = await import('@/app/auth/signin/page');
    render(<SignInPage />);
    expect(screen.getByText(/18 years or older/)).toBeDefined();
  });

  it('Sign-in consent mentions Terms and Privacy', async () => {
    const { default: SignInPage } = await import('@/app/auth/signin/page');
    render(<SignInPage />);
    expect(screen.getByRole('link', { name: 'Terms of Service' })).toBeDefined();
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toBeDefined();
  });
});

// ── 5. Cookie Consent ──

describe('Cookie Consent Compliance', () => {
  beforeEach(() => {
    const store: Record<string, string> = {};
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: (key: string) => store[key] ?? null,
        setItem: (key: string, value: string) => { store[key] = value; },
        removeItem: (key: string) => { delete store[key]; },
      },
      writable: true,
    });
  });

  it('CookieConsent banner appears for new users', async () => {
    const { CookieConsent } = await import(
      '@/components/shared/CookieConsent'
    );
    render(<CookieConsent />);
    expect(screen.getByRole('dialog', { name: 'Cookie consent' })).toBeDefined();
  });

  it('CookieConsent mentions Privacy Policy', async () => {
    const { CookieConsent } = await import(
      '@/components/shared/CookieConsent'
    );
    render(<CookieConsent />);
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toBeDefined();
  });
});
