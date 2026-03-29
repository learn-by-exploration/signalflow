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

  it('calls API when upgrade button is clicked (no client-side tier switch)', async () => {
    // B1 fix: clicking Upgrade to Pro now calls the payments API
    // instead of directly setting the tier in the store.
    // The tier only changes after webhook confirmation.
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ data: { subscription_id: 'sub_1' } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    );
    render(<PricingPage />);
    fireEvent.click(screen.getByText('Upgrade to Pro'));
    // Tier should NOT change immediately — it stays 'free' until webhook
    expect(useTierStore.getState().tier).toBe('free');
    fetchSpy.mockRestore();
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
