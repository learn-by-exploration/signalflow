import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UpgradePrompt } from '@/components/shared/UpgradePrompt';

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe('UpgradePrompt', () => {
  it('renders feature name as Pro feature', () => {
    render(<UpgradePrompt feature="aiQA" />);
    expect(screen.getByText(/Ask AI.*is a Pro feature/)).toBeInTheDocument();
  });

  it('shows View Plans link to pricing page', () => {
    render(<UpgradePrompt feature="backtesting" />);
    const link = screen.getByText('View Plans');
    expect(link.closest('a')).toHaveAttribute('href', '/pricing');
  });

  it('shows the Pro tier price', () => {
    render(<UpgradePrompt feature="portfolio" />);
    expect(screen.getByText(/₹749\/mo/)).toBeInTheDocument();
  });

  it('falls back gracefully for unknown feature', () => {
    render(<UpgradePrompt feature="unknownFeature" />);
    expect(screen.getByText(/unknownFeature.*is a Pro feature/)).toBeInTheDocument();
  });

  it('has the lightning bolt icon', () => {
    render(<UpgradePrompt feature="aiQA" />);
    expect(screen.getByText('⚡')).toBeInTheDocument();
  });
});
