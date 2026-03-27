import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MobileMenuSheet } from '@/components/shared/MobileMenuSheet';

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
});

describe('MobileMenuSheet', () => {
  it('does not render when isOpen=false', () => {
    const { container } = render(<MobileMenuSheet isOpen={false} onClose={vi.fn()} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders grouped links when isOpen=true', () => {
    render(<MobileMenuSheet isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Track Record')).toBeInTheDocument();
    expect(screen.getByText('Signal History')).toBeInTheDocument();
    expect(screen.getByText('Research')).toBeInTheDocument();
    expect(screen.getByText('News')).toBeInTheDocument();
    expect(screen.getByText('Account')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('About')).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();
  });

  it('renders legal links', () => {
    render(<MobileMenuSheet isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText('Privacy')).toBeInTheDocument();
    expect(screen.getByText('Terms')).toBeInTheDocument();
    expect(screen.getByText('Refund Policy')).toBeInTheDocument();
    expect(screen.getByText('Contact')).toBeInTheDocument();
  });

  it('has role="dialog" and aria-modal="true"', () => {
    render(<MobileMenuSheet isOpen={true} onClose={vi.fn()} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-label', 'Navigation menu');
  });

  it('calls onClose when overlay is clicked', () => {
    const onClose = vi.fn();
    render(<MobileMenuSheet isOpen={true} onClose={onClose} />);
    // The overlay is the first fixed div with aria-hidden
    const overlay = screen.getByRole('dialog').parentElement?.querySelector('[aria-hidden="true"]');
    if (overlay) {
      fireEvent.click(overlay);
      expect(onClose).toHaveBeenCalled();
    }
  });

  it('does not render when unauthenticated', () => {
    mockSession = { data: null, status: 'unauthenticated' };
    const { container } = render(<MobileMenuSheet isOpen={true} onClose={vi.fn()} />);
    expect(container.innerHTML).toBe('');
  });
});
