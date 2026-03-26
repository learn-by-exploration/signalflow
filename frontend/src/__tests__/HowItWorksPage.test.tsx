import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('HowItWorksPage', () => {
  it('renders main heading', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText('How SignalFlow AI Works')).toBeInTheDocument();
  });

  it('renders all 6 steps', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText('Data Collection')).toBeInTheDocument();
    expect(screen.getByText(/Technical Analysis/)).toBeInTheDocument();
    expect(screen.getByText(/AI Sentiment & Event Chain Analysis/)).toBeInTheDocument();
    expect(screen.getByText('Signal Generation')).toBeInTheDocument();
    expect(screen.getByText('Target & Stop-Loss')).toBeInTheDocument();
    expect(screen.getByText('AI Reasoning')).toBeInTheDocument();
  });

  it('renders technical indicator weights', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText('SMA Crossover')).toBeInTheDocument();
    expect(screen.getByText('MACD')).toBeInTheDocument();
    expect(screen.getByText('RSI')).toBeInTheDocument();
    expect(screen.getByText('Bollinger Bands')).toBeInTheDocument();
    expect(screen.getByText('Volume')).toBeInTheDocument();
  });

  it('shows indicator percentage weights', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getAllByText('25%')).toHaveLength(2); // MACD + SMA
    expect(screen.getByText('20%')).toBeDefined(); // RSI
    expect(screen.getAllByText('15%')).toHaveLength(2); // BB + Volume
  });

  it('renders signal types table', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText('STRONG BUY')).toBeInTheDocument();
    expect(screen.getByText('80–100%')).toBeInTheDocument();
    expect(screen.getByText('HOLD')).toBeInTheDocument();
    expect(screen.getByText('STRONG SELL')).toBeInTheDocument();
  });

  it('shows the confidence formula', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText(/technical.*0\.50.*event_chain.*0\.35.*sentiment.*0\.15/)).toBeInTheDocument();
  });

  it('shows target/stop-loss formulas', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText(/Target = Price \+ \(ATR × 2\.0\)/)).toBeInTheDocument();
    expect(screen.getByText(/Stop-Loss = Price - \(ATR × 1\.0\)/)).toBeInTheDocument();
  });

  it('includes disclaimer', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText(/not financial advice/)).toBeInTheDocument();
  });

  it('mentions 31 symbols across three markets', async () => {
    const { default: Page } = await import('@/app/how-it-works/page');
    render(<Page />);
    expect(screen.getByText(/31 symbols/)).toBeInTheDocument();
  });
});
