import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navbar } from '@/components/shared/Navbar';
import { useSignalStore } from '@/store/signalStore';

// Mock Next.js modules
vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

let mockPathname = '/';
vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
}));

// Mock SettingsPanel to avoid complexity
vi.mock('@/components/shared/SettingsPanel', () => ({
  SettingsPanel: ({ isOpen }: { isOpen: boolean }) => isOpen ? <div data-testid="settings-panel">Settings</div> : null,
}));

beforeEach(() => {
  mockPathname = '/';
  useSignalStore.setState({ unseenCount: 0 });
});

describe('Navbar', () => {
  it('renders the SignalFlow logo', () => {
    render(<Navbar />);
    expect(screen.getByText('SignalFlow')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();
  });

  it('renders primary navigation links', () => {
    render(<Navbar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Track Record')).toBeInTheDocument();
    expect(screen.getByText('Alerts')).toBeInTheDocument();
  });

  it('highlights active page with aria-current', () => {
    mockPathname = '/history';
    render(<Navbar />);
    const link = screen.getAllByText('Track Record')[0].closest('a');
    expect(link).toHaveAttribute('aria-current', 'page');
  });

  it('does not show unseen badge on active Dashboard', () => {
    mockPathname = '/';
    useSignalStore.setState({ unseenCount: 5 });
    render(<Navbar />);
    // Badge should not show when Dashboard is active
    expect(screen.queryByText('5')).not.toBeInTheDocument();
  });

  it('shows unseen count badge when Dashboard is not active', () => {
    mockPathname = '/history';
    useSignalStore.setState({ unseenCount: 5 });
    render(<Navbar />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('caps unseen badge at 9+', () => {
    mockPathname = '/history';
    useSignalStore.setState({ unseenCount: 15 });
    render(<Navbar />);
    expect(screen.getByText('9+')).toBeInTheDocument();
  });

  it('renders Settings button with proper aria-label', () => {
    render(<Navbar />);
    expect(screen.getByLabelText('Settings')).toBeInTheDocument();
  });

  it('opens settings panel when gear icon is clicked', () => {
    render(<Navbar />);
    fireEvent.click(screen.getByLabelText('Settings'));
    expect(screen.getByTestId('settings-panel')).toBeInTheDocument();
  });

  it('renders "More" dropdown with additional links on click', () => {
    render(<Navbar />);
    fireEvent.click(screen.getByText('More'));
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Backtest')).toBeInTheDocument();
    expect(screen.getByText('Daily Brief')).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();
  });

  it('renders mobile toggle button', () => {
    render(<Navbar />);
    expect(screen.getByLabelText('Toggle menu')).toBeInTheDocument();
  });

  it('shows mobile menu when hamburger is clicked', () => {
    render(<Navbar />);
    fireEvent.click(screen.getByLabelText('Toggle menu'));
    // Mobile menu includes all links
    const portfolioLinks = screen.getAllByText('Portfolio');
    expect(portfolioLinks.length).toBeGreaterThanOrEqual(1);
  });
});
