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

// Mock next-auth/react — default to authenticated
let mockSession: { data: unknown; status: string } = {
  data: { user: { name: 'Test', email: 'test@example.com' } },
  status: 'authenticated',
};
vi.mock('next-auth/react', () => ({
  useSession: () => mockSession,
  signOut: vi.fn(),
}));

beforeEach(() => {
  mockPathname = '/';
  mockSession = {
    data: { user: { name: 'Test', email: 'test@example.com' } },
    status: 'authenticated',
  };
  useSignalStore.setState({ unseenCount: 0 });
});

describe('Navbar (authenticated)', () => {
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
    mockPathname = '/track-record';
    render(<Navbar />);
    const link = screen.getAllByText('Track Record')[0].closest('a');
    expect(link).toHaveAttribute('aria-current', 'page');
  });

  it('does not show unseen badge on active Dashboard', () => {
    mockPathname = '/';
    useSignalStore.setState({ unseenCount: 5 });
    render(<Navbar />);
    expect(screen.queryByText('5')).not.toBeInTheDocument();
  });

  it('shows unseen count badge when Dashboard is not active', () => {
    mockPathname = '/track-record';
    useSignalStore.setState({ unseenCount: 5 });
    render(<Navbar />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('caps unseen badge at 9+', () => {
    mockPathname = '/track-record';
    useSignalStore.setState({ unseenCount: 15 });
    render(<Navbar />);
    expect(screen.getByText('9+')).toBeInTheDocument();
  });

  it('renders Settings link with proper aria-label', () => {
    render(<Navbar />);
    const settingsLink = screen.getByLabelText('Settings');
    expect(settingsLink).toBeInTheDocument();
    expect(settingsLink.closest('a')).toHaveAttribute('href', '/settings');
  });

  it('renders "More" dropdown with additional links on click', () => {
    render(<Navbar />);
    fireEvent.click(screen.getByText('More ▾'));
    expect(screen.getByText('Signal History')).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();
  });

  it('renders mobile toggle button', () => {
    render(<Navbar />);
    expect(screen.getByLabelText('Toggle menu')).toBeInTheDocument();
  });

  it('shows mobile menu when hamburger is clicked', () => {
    render(<Navbar />);
    fireEvent.click(screen.getByLabelText('Toggle menu'));
    const alertLinks = screen.getAllByText('Alerts');
    expect(alertLinks.length).toBeGreaterThanOrEqual(1);
  });
});

describe('Navbar (unauthenticated)', () => {
  beforeEach(() => {
    mockSession = { data: null, status: 'unauthenticated' };
  });

  it('shows only public links for visitors', () => {
    render(<Navbar />);
    expect(screen.getByText('How It Works')).toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('Track Record')).not.toBeInTheDocument();
    expect(screen.queryByText('More')).not.toBeInTheDocument();
  });

  it('shows Sign In button for visitors', () => {
    render(<Navbar />);
    const signInLink = screen.getByText('Sign In');
    expect(signInLink.closest('a')).toHaveAttribute('href', '/auth/signin');
  });

  it('does not show Settings for visitors', () => {
    render(<Navbar />);
    expect(screen.queryByLabelText('Settings')).not.toBeInTheDocument();
  });

  it('mobile menu shows public links and Sign In for visitors', () => {
    render(<Navbar />);
    fireEvent.click(screen.getByLabelText('Toggle menu'));
    const signInLinks = screen.getAllByText('Sign In');
    expect(signInLinks.length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText('Portfolio')).not.toBeInTheDocument();
  });
});
