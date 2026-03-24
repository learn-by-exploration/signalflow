import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TermsOfServicePage from '@/app/terms/page';

describe('TermsOfServicePage', () => {
  it('renders the page title', () => {
    render(<TermsOfServicePage />);
    expect(screen.getByText('Terms of Service')).toBeDefined();
  });

  it('has prominent Not Investment Advice section', () => {
    render(<TermsOfServicePage />);
    expect(screen.getByText(/3\. Not Investment Advice/)).toBeDefined();
  });

  it('contains SEBI non-registration disclosure', () => {
    render(<TermsOfServicePage />);
    expect(
      screen.getByText(/NOT registered with the Securities and Exchange Board of India/),
    ).toBeDefined();
  });

  it('contains Limitation of Liability section', () => {
    render(<TermsOfServicePage />);
    expect(screen.getByText('7. Limitation of Liability')).toBeDefined();
  });

  it('states 18+ age requirement', () => {
    render(<TermsOfServicePage />);
    expect(screen.getByText(/at least 18 years of age/)).toBeDefined();
  });

  it('contains link to Privacy Policy', () => {
    render(<TermsOfServicePage />);
    const links = screen.getAllByRole('link', { name: 'Privacy Policy' });
    expect(links.some((l) => l.getAttribute('href') === '/privacy')).toBe(true);
  });

  it('contains Governing Law section', () => {
    render(<TermsOfServicePage />);
    expect(screen.getByText('9. Governing Law')).toBeDefined();
    expect(screen.getByText(/laws of India/)).toBeDefined();
  });
});
