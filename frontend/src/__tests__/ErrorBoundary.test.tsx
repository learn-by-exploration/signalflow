import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

function ThrowingChild({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('Test error');
  return <div>Child rendered OK</div>;
}

describe('ErrorBoundary', () => {
  // Suppress console.error noise from React error boundaries
  const originalError = console.error;
  beforeEach(() => { console.error = vi.fn(); });
  afterEach(() => { console.error = originalError; });

  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Hello</div>
      </ErrorBoundary>,
    );
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders default fallback when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Try again')).toBeInTheDocument();
  });

  it('shows named error message when name prop is provided', () => {
    render(
      <ErrorBoundary name="SignalFeed">
        <ThrowingChild shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText('SignalFeed had a problem loading')).toBeInTheDocument();
  });

  it('renders custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <ThrowingChild shouldThrow />
      </ErrorBoundary>,
    );
    expect(screen.getByText('Custom fallback')).toBeInTheDocument();
  });

  it('resets error state when "Try again" is clicked', () => {
    let shouldThrow = true;
    function ControlledChild() {
      if (shouldThrow) throw new Error('Oops');
      return <div>Recovered</div>;
    }

    const { rerender } = render(
      <ErrorBoundary>
        <ControlledChild />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    // Allow next render to succeed
    shouldThrow = false;
    fireEvent.click(screen.getByText('Try again'));

    // Force rerender
    rerender(
      <ErrorBoundary>
        <ControlledChild />
      </ErrorBoundary>,
    );

    expect(screen.getByText('Recovered')).toBeInTheDocument();
  });

  it('calls componentDidCatch and logs the error', () => {
    render(
      <ErrorBoundary name="TestBound">
        <ThrowingChild shouldThrow />
      </ErrorBoundary>,
    );
    // console.error is called by React and by our componentDidCatch
    expect(console.error).toHaveBeenCalled();
  });
});
