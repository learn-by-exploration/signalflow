import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SebiDisclaimer } from '@/components/shared/SebiDisclaimer';

describe('SebiDisclaimer', () => {
  it('renders the disclaimer text', () => {
    render(<SebiDisclaimer />);
    expect(screen.getByText(/NOT registered with SEBI/)).toBeDefined();
    expect(screen.getByText(/not constitute investment advice/i)).toBeDefined();
  });

  it('renders as a footer element with accessibility attributes', () => {
    const { container } = render(<SebiDisclaimer />);
    const footer = container.querySelector('footer');
    expect(footer).toBeTruthy();
    expect(footer?.getAttribute('role')).toBe('contentinfo');
    expect(footer?.getAttribute('aria-label')).toBe('Legal disclaimer');
  });

  it('mentions consulting a SEBI-registered advisor', () => {
    render(<SebiDisclaimer />);
    expect(screen.getByText(/SEBI-registered investment advisor/i)).toBeDefined();
  });

  it('uses text-xs font size instead of 10px', () => {
    const { container } = render(<SebiDisclaimer />);
    const mainParagraph = container.querySelector('p');
    expect(mainParagraph?.className).toContain('text-xs');
    // Ensure we don't use sub-12px arbitrary sizes
    expect(mainParagraph?.className).not.toMatch(/text-\[\d+px\]/);
  });

  it('contains links to Privacy Policy and Terms', () => {
    render(<SebiDisclaimer />);
    const privacyLink = screen.getByRole('link', { name: 'Privacy Policy' });
    const termsLink = screen.getByRole('link', { name: 'Terms of Service' });
    expect(privacyLink.getAttribute('href')).toBe('/privacy');
    expect(termsLink.getAttribute('href')).toBe('/terms');
  });

  it('labels disclaimer as Important Disclaimer', () => {
    render(<SebiDisclaimer />);
    expect(screen.getByText(/Important Disclaimer/)).toBeDefined();
  });
});
