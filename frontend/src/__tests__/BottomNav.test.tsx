import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BottomNav } from '@/components/shared/BottomNav';
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

describe('BottomNav', () => {
  it('renders 5 tabs: Home, Watchlist, Brief, Portfolio, Menu', () => {
    render(<BottomNav />);
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Watchlist')).toBeInTheDocument();
    expect(screen.getByText('Brief')).toBeInTheDocument();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Menu')).toBeInTheDocument();
  });

  it('highlights active tab with aria-current="page"', () => {
    mockPathname = '/watchlist';
    render(<BottomNav />);
    const watchlistLink = screen.getByText('Watchlist').closest('a');
    expect(watchlistLink).toHaveAttribute('aria-current', 'page');
  });

  it('shows unseen badge on Home tab when not on Dashboard', () => {
    mockPathname = '/portfolio';
    useSignalStore.setState({ unseenCount: 3 });
    render(<BottomNav />);
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('caps unseen badge at 9+', () => {
    mockPathname = '/portfolio';
    useSignalStore.setState({ unseenCount: 20 });
    render(<BottomNav />);
    expect(screen.getByText('9+')).toBeInTheDocument();
  });

  it('does not show badge when on Dashboard', () => {
    mockPathname = '/';
    useSignalStore.setState({ unseenCount: 5 });
    render(<BottomNav />);
    expect(screen.queryByText('5')).not.toBeInTheDocument();
  });

  it('does not render when unauthenticated', () => {
    mockSession = { data: null, status: 'unauthenticated' };
    const { container } = render(<BottomNav />);
    expect(container.innerHTML).toBe('');
  });

  it('has role="navigation" and aria-label', () => {
    render(<BottomNav />);
    const nav = screen.getByRole('navigation', { name: 'Main navigation' });
    expect(nav).toBeInTheDocument();
  });

  it('Menu tab toggles menu sheet', () => {
    render(<BottomNav />);
    const menuButton = screen.getByLabelText('Menu');
    fireEvent.click(menuButton);
    // When menu sheet opens, it should render the dialog
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
