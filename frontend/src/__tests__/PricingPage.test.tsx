import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PricingPage from '@/app/pricing/page';
import { UpgradePrompt } from '@/components/shared/UpgradePrompt';
import { useTierStore } from '@/store/tierStore';

beforeEach(() => {
  useTierStore.setState({ tier: 'free', signalsViewedToday: 0 });
});

describe('PricingPage', () => {
  it('renders page title', () => {
    render(<PricingPage />);
    expect(screen.getByText('Choose Your Plan')).toBeDefined();
  });

  it('shows both Free and Pro tiers', () => {
    render(<PricingPage />);
    expect(screen.getByText('Free')).toBeDefined();
    expect(screen.getByText('Pro')).toBeDefined();
  });

  it('displays prices correctly', () => {
    render(<PricingPage />);
    expect(screen.getByText('₹0')).toBeDefined();
  });

  it('shows feature list with checkmarks for enabled features', () => {
    render(<PricingPage />);
    const checkmarks = screen.getAllByText('✓');
    expect(checkmarks.length).toBeGreaterThan(0);
  });

  it('shows feature list with crosses for disabled features', () => {
    render(<PricingPage />);
    const crosses = screen.getAllByText('✗');
    expect(crosses.length).toBeGreaterThan(0);
  });

  it('marks free as Current Plan when on free tier', () => {
    render(<PricingPage />);
    const buttons = screen.getAllByRole('button');
    const currentButton = buttons.find((b) => b.textContent === 'Current Plan');
    expect(currentButton).toBeDefined();
  });

  it('shows Upgrade to Pro button when on free tier', () => {
    render(<PricingPage />);
    expect(screen.getByText('Upgrade to Pro')).toBeDefined();
  });

  it('switches to Pro tier when upgrade button is clicked', () => {
    render(<PricingPage />);
    fireEvent.click(screen.getByText('Upgrade to Pro'));
    expect(useTierStore.getState().tier).toBe('pro');
  });

  it('shows Recommended badge on Pro plan', () => {
    render(<PricingPage />);
    expect(screen.getByText('Recommended')).toBeDefined();
  });
});

describe('UpgradePrompt', () => {
  it('renders feature name in heading', () => {
    render(<UpgradePrompt feature="aiQA" />);
    expect(screen.getByText('Ask AI is a Pro feature')).toBeDefined();
  });

  it('renders link to pricing page', () => {
    render(<UpgradePrompt feature="backtesting" />);
    const link = screen.getByText('View Plans');
    expect(link.getAttribute('href')).toBe('/pricing');
  });

  it('shows Pro price', () => {
    render(<UpgradePrompt feature="aiQA" />);
    expect(screen.getByText(/₹749\/mo/)).toBeDefined();
  });

  it('handles unknown features gracefully', () => {
    render(<UpgradePrompt feature="unknownFeature" />);
    expect(screen.getByText('unknownFeature is a Pro feature')).toBeDefined();
  });
});
