import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PrivacyPolicyPage from '@/app/privacy/page';

describe('PrivacyPolicyPage', () => {
  it('renders the page title', () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByText('Privacy Policy')).toBeDefined();
  });

  it('contains Data We Collect section', () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByText('1. Data We Collect')).toBeDefined();
  });

  it('contains Your Rights section with DPDPA reference', () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByText('4. Your Rights')).toBeDefined();
    const dpdpaMatches = screen.getAllByText(/DPDPA/);
    expect(dpdpaMatches.length).toBeGreaterThan(0);
  });

  it('contains Grievance Officer section with contact email', () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByText('8. Grievance Officer')).toBeDefined();
    const emailLinks = screen.getAllByText('privacy@signalflow.ai');
    expect(emailLinks.length).toBeGreaterThan(0);
  });

  it('contains link to Terms of Service', () => {
    render(<PrivacyPolicyPage />);
    const link = screen.getByRole('link', { name: 'Terms of Service' });
    expect(link.getAttribute('href')).toBe('/terms');
  });

  it('lists all required data categories', () => {
    render(<PrivacyPolicyPage />);
    expect(screen.getByText('Email address')).toBeDefined();
    expect(screen.getByText('Telegram chat ID')).toBeDefined();
    expect(screen.getByText('Trade logs')).toBeDefined();
    expect(screen.getByText('Watchlist symbols')).toBeDefined();
  });
});
