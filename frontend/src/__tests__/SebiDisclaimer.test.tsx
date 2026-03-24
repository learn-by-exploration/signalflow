import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { SebiDisclaimer } from '@/components/shared/SebiDisclaimer';

describe('SebiDisclaimer', () => {
  it('renders the disclaimer text', () => {
    const { getByText } = render(<SebiDisclaimer />);
    expect(getByText(/not registered with SEBI/i)).toBeInTheDocument();
    expect(getByText(/not investment advice/i)).toBeInTheDocument();
  });

  it('renders as a footer element', () => {
    const { container } = render(<SebiDisclaimer />);
    const footer = container.querySelector('footer');
    expect(footer).toBeTruthy();
  });

  it('mentions consulting a SEBI-registered advisor', () => {
    const { getByText } = render(<SebiDisclaimer />);
    expect(getByText(/SEBI-registered advisor/i)).toBeInTheDocument();
  });

  it('includes trade at your own risk warning', () => {
    const { getByText } = render(<SebiDisclaimer />);
    expect(getByText(/Trade at your own risk/i)).toBeInTheDocument();
  });
});
