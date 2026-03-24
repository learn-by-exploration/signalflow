import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default md size', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner.className).toContain('h-6');
    expect(spinner.className).toContain('w-6');
  });

  it('renders sm size', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner.className).toContain('h-4');
    expect(spinner.className).toContain('w-4');
  });

  it('renders lg size', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner.className).toContain('h-10');
    expect(spinner.className).toContain('w-10');
  });

  it('has animation class', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner.className).toContain('animate-spin');
  });

  it('has rounded-full border styling', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.firstChild as HTMLElement;
    expect(spinner.className).toContain('rounded-full');
    expect(spinner.className).toContain('border-2');
  });
});
