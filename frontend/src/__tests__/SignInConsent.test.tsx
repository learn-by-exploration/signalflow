import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SignInPage from '@/app/auth/signin/page';

// Mock next-auth
vi.mock('next-auth/react', () => ({
  signIn: vi.fn(),
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: () => null,
  }),
}));

describe('SignIn Consent Flow', () => {
  it('renders consent checkbox', () => {
    render(<SignInPage />);
    const checkboxes = screen.getAllByRole('checkbox');
    expect(checkboxes.length).toBeGreaterThanOrEqual(1);
  });

  it('sign-in button is disabled when consent not given', () => {
    render(<SignInPage />);
    const submitButton = screen.getByRole('button', { name: 'Sign In' });
    expect(submitButton.hasAttribute('disabled')).toBe(true);
  });

  it('Google button is disabled when consent not given', () => {
    render(<SignInPage />);
    const googleButton = screen.getByRole('button', { name: /Google/ });
    expect(googleButton.hasAttribute('disabled')).toBe(true);
  });

  it('buttons enabled after checking consent', () => {
    render(<SignInPage />);
    // The consent checkbox is the one associated with the 18+ age text
    const checkboxes = screen.getAllByRole('checkbox');
    const consentCheckbox = checkboxes.find(
      (cb) => cb.closest('label')?.textContent?.includes('18 years or older')
    );
    fireEvent.click(consentCheckbox!);

    const submitButton = screen.getByRole('button', { name: 'Sign In' });
    expect(submitButton.hasAttribute('disabled')).toBe(false);

    const googleButton = screen.getByRole('button', { name: /Google/ });
    expect(googleButton.hasAttribute('disabled')).toBe(false);
  });

  it('contains 18+ age declaration', () => {
    render(<SignInPage />);
    expect(screen.getByText(/18 years or older/)).toBeDefined();
  });

  it('contains links to Terms and Privacy', () => {
    render(<SignInPage />);
    expect(screen.getByRole('link', { name: 'Terms of Service' })).toBeDefined();
    expect(screen.getByRole('link', { name: 'Privacy Policy' })).toBeDefined();
  });

  it('contains not investment advice acknowledgment', () => {
    render(<SignInPage />);
    expect(screen.getByText(/does not constitute investment advice/)).toBeDefined();
  });
});
