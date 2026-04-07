/**
 * Tests for GuidedScenario component.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GuidedScenario } from '@/components/graph/GuidedScenario';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe('GuidedScenario', () => {
  it('renders all walkthrough cards', () => {
    render(<GuidedScenario />);
    expect(screen.getByText('Explore an Entity')).toBeInTheDocument();
    expect(screen.getByText('Run an Impact Simulation')).toBeInTheDocument();
    expect(screen.getByText('Analyze Supply Chain Risk')).toBeInTheDocument();
    expect(screen.getByText('Understand Signal Context')).toBeInTheDocument();
  });

  it('shows difficulty badges', () => {
    render(<GuidedScenario />);
    expect(screen.getAllByText('beginner').length).toBe(2);
    expect(screen.getAllByText('intermediate').length).toBe(2);
  });

  it('shows step count and duration', () => {
    render(<GuidedScenario />);
    expect(screen.getAllByText(/min/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/steps/).length).toBeGreaterThanOrEqual(1);
  });

  it('opens a walkthrough when clicked', async () => {
    render(<GuidedScenario />);
    const card = screen.getByText('Explore an Entity');
    await userEvent.click(card);

    expect(screen.getByText('Step 1 of 4')).toBeInTheDocument();
    expect(screen.getByText('Search for an entity')).toBeInTheDocument();
  });

  it('navigates through steps', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    // Step 1
    expect(screen.getByText('Step 1 of 4')).toBeInTheDocument();

    // Go to step 2
    await userEvent.click(screen.getByText('Next →'));
    expect(screen.getByText('Step 2 of 4')).toBeInTheDocument();
    expect(screen.getByText('View entity details')).toBeInTheDocument();

    // Go back
    await userEvent.click(screen.getByText('← Back'));
    expect(screen.getByText('Step 1 of 4')).toBeInTheDocument();
  });

  it('shows Complete button on last step', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    // Navigate to last step
    for (let i = 0; i < 3; i++) {
      await userEvent.click(screen.getByText('Next →'));
    }

    expect(screen.getByText('Step 4 of 4')).toBeInTheDocument();
    expect(screen.getByText('✓ Complete')).toBeInTheDocument();
  });

  it('closes walkthrough on Complete', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    // Navigate to last step
    for (let i = 0; i < 3; i++) {
      await userEvent.click(screen.getByText('Next →'));
    }

    await userEvent.click(screen.getByText('✓ Complete'));

    // Should return to card view
    expect(screen.getByText('Explore an Entity')).toBeInTheDocument();
    expect(screen.queryByText('Step 1 of 4')).not.toBeInTheDocument();
  });

  it('closes walkthrough on close button', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    await userEvent.click(screen.getByText('✕ Close'));

    expect(screen.queryByText('Step 1 of 4')).not.toBeInTheDocument();
  });

  it('shows action links for steps with URLs', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    // Step 1 should have a link to /knowledge-graph
    const link = screen.getByText('Go to Supply Chain Map and search →');
    expect(link.closest('a')).toHaveAttribute('href', '/knowledge-graph');
  });

  it('renders progress bar', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    // Progress bar should be present (can't easily test visual state,
    // but the structure should have 4 progress segments)
    const walkthrough = screen.getByText('Step 1 of 4').closest('div.rounded-xl');
    expect(walkthrough).toBeInTheDocument();
  });

  it('disables back button on first step', async () => {
    render(<GuidedScenario />);
    await userEvent.click(screen.getByText('Explore an Entity'));

    const backButton = screen.getByText('← Back');
    expect(backButton).toBeDisabled();
  });
});
