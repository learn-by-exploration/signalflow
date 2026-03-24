import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import {
  SignalCardSkeleton,
  SignalFeedSkeleton,
  MarketOverviewSkeleton,
  WinRateCardSkeleton,
  HistoryTableSkeleton,
  PortfolioSkeleton,
} from '@/components/shared/Skeleton';

describe('Skeleton components', () => {
  it('renders SignalCardSkeleton with animate-pulse', () => {
    const { container } = render(<SignalCardSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders SignalFeedSkeleton with default 5 items', () => {
    const { container } = render(<SignalFeedSkeleton />);
    const pulseItems = container.querySelectorAll('.animate-pulse');
    expect(pulseItems).toHaveLength(5);
  });

  it('renders SignalFeedSkeleton with custom count', () => {
    const { container } = render(<SignalFeedSkeleton count={3} />);
    const pulseItems = container.querySelectorAll('.animate-pulse');
    expect(pulseItems).toHaveLength(3);
  });

  it('renders MarketOverviewSkeleton', () => {
    const { container } = render(<MarketOverviewSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders WinRateCardSkeleton', () => {
    const { container } = render(<WinRateCardSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders HistoryTableSkeleton', () => {
    const { container } = render(<HistoryTableSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders PortfolioSkeleton', () => {
    const { container } = render(<PortfolioSkeleton />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });
});
