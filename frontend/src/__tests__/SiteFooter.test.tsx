import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SiteFooter } from '@/components/shared/SiteFooter';

// Mock Next.js modules
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe('SiteFooter', () => {
  it('renders Product column with primary links', () => {
    render(<SiteFooter />);
    expect(screen.getByText('Product')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Watchlist')).toBeInTheDocument();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Brief')).toBeInTheDocument();
    expect(screen.getByText('Track Record')).toBeInTheDocument();
  });

  it('renders Research column with research links', () => {
    render(<SiteFooter />);
    expect(screen.getByText('Research')).toBeInTheDocument();
    expect(screen.getByText('News')).toBeInTheDocument();
    expect(screen.getByText('Calendar')).toBeInTheDocument();
    expect(screen.getByText('Backtest')).toBeInTheDocument();
    expect(screen.getByText('Signal History')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
  });

  it('renders Legal column with legal links', () => {
    render(<SiteFooter />);
    expect(screen.getByText('Legal')).toBeInTheDocument();
    expect(screen.getByText('Privacy')).toBeInTheDocument();
    expect(screen.getByText('Terms')).toBeInTheDocument();
    expect(screen.getByText('Refund Policy')).toBeInTheDocument();
  });

  it('renders Support column with contact link', () => {
    render(<SiteFooter />);
    expect(screen.getByText('Support')).toBeInTheDocument();
    expect(screen.getByText('Contact & Grievance')).toBeInTheDocument();
  });

  it('renders SEBI disclaimer text', () => {
    render(<SiteFooter />);
    expect(screen.getByText(/NOT registered with SEBI/)).toBeInTheDocument();
    expect(screen.getByText(/educational and informational purposes only/)).toBeInTheDocument();
  });

  it('renders copyright', () => {
    render(<SiteFooter />);
    const year = new Date().getFullYear().toString();
    expect(screen.getByText(new RegExp(`${year} SignalFlow AI`))).toBeInTheDocument();
  });

  it('has role="contentinfo"', () => {
    render(<SiteFooter />);
    const footer = screen.getByRole('contentinfo', { name: 'Site footer' });
    expect(footer).toBeInTheDocument();
  });
});
