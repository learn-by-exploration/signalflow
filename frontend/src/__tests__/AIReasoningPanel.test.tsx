import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AIReasoningPanel } from '@/components/signals/AIReasoningPanel';

describe('AIReasoningPanel', () => {
  it('renders reasoning text when expanded', () => {
    render(<AIReasoningPanel reasoning="Credit growth is accelerating." isExpanded={true} />);
    expect(screen.getByText('Credit growth is accelerating.')).toBeInTheDocument();
  });

  it('shows "AI Reasoning" label when expanded', () => {
    render(<AIReasoningPanel reasoning="Test." isExpanded={true} />);
    expect(screen.getByText('AI Reasoning')).toBeInTheDocument();
  });

  it('has hidden content when collapsed (opacity-0)', () => {
    const { container } = render(<AIReasoningPanel reasoning="Hidden text." isExpanded={false} />);
    const wrapper = container.firstElementChild;
    expect(wrapper?.className).toContain('opacity-0');
  });

  it('has visible content when expanded (opacity-100)', () => {
    const { container } = render(<AIReasoningPanel reasoning="Visible text." isExpanded={true} />);
    const wrapper = container.firstElementChild;
    expect(wrapper?.className).toContain('opacity-100');
  });
});
