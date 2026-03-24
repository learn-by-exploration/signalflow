import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import EconomicCalendarPage from '@/app/calendar/page';

describe('EconomicCalendarPage', () => {
  it('renders the page title', () => {
    render(<EconomicCalendarPage />);
    expect(screen.getByText('Economic Calendar')).toBeInTheDocument();
  });

  it('shows market filter buttons', () => {
    render(<EconomicCalendarPage />);
    // Market filter section has all four options — get buttons only
    const buttons = screen.getAllByRole('button');
    const marketLabels = buttons.map((b) => b.textContent).filter(Boolean);
    expect(marketLabels).toContain('All');
    expect(marketLabels).toContain('Stock');
    expect(marketLabels).toContain('Crypto');
    expect(marketLabels).toContain('Forex');
  });

  it('shows impact filter buttons', () => {
    render(<EconomicCalendarPage />);
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('renders economic events', () => {
    render(<EconomicCalendarPage />);
    expect(screen.getByText('RBI Monetary Policy Decision')).toBeInTheDocument();
    expect(screen.getByText('FOMC Interest Rate Decision')).toBeInTheDocument();
  });

  it('shows previous and forecast data for events', () => {
    render(<EconomicCalendarPage />);
    // All events have Previous/Forecast labels
    const prevLabels = screen.getAllByText('Previous');
    expect(prevLabels.length).toBeGreaterThan(0);
    const forecastLabels = screen.getAllByText('Forecast');
    expect(forecastLabels.length).toBeGreaterThan(0);
  });

  it('shows trading tip note', () => {
    render(<EconomicCalendarPage />);
    expect(screen.getByText(/Avoid entering new positions/i)).toBeInTheDocument();
  });

  it('filters by high impact only', () => {
    render(<EconomicCalendarPage />);
    // Click "High" impact filter - get the second one (first "High" is in the list already)
    const highButtons = screen.getAllByText('High');
    fireEvent.click(highButtons[0]);
    // Low impact events like "US Jobless Claims" should be hidden
    expect(screen.queryByText('US Jobless Claims (Weekly)')).not.toBeInTheDocument();
  });
});
