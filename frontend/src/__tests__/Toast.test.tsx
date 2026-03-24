import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { ToastProvider, useToast } from '@/components/shared/Toast';

function TestConsumer() {
  const { toast } = useToast();
  return (
    <div>
      <button onClick={() => toast('Info message')}>Show Info</button>
      <button onClick={() => toast('Success!', 'success')}>Show Success</button>
      <button onClick={() => toast('Error!', 'error')}>Show Error</button>
    </div>
  );
}

beforeEach(() => {
  vi.useFakeTimers();
});

describe('Toast', () => {
  it('shows toast message on trigger', () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText('Show Info'));
    expect(screen.getByRole('alert')).toHaveTextContent('Info message');
  });

  it('shows success toast with correct styling', () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText('Show Success'));
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Success!');
    expect(alert.className).toContain('signal-buy');
  });

  it('shows error toast with correct styling', () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText('Show Error'));
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Error!');
    expect(alert.className).toContain('signal-sell');
  });

  it('auto-dismisses toast after 3 seconds', () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText('Show Info'));
    expect(screen.getByRole('alert')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows multiple toasts', () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByText('Show Info'));
    fireEvent.click(screen.getByText('Show Success'));

    const alerts = screen.getAllByRole('alert');
    expect(alerts).toHaveLength(2);
  });

  it('has accessible status container', () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>,
    );

    const container = document.querySelector('[role="status"]');
    expect(container).toBeTruthy();
    expect(container?.getAttribute('aria-live')).toBe('polite');
  });

  it('renders children', () => {
    render(
      <ToastProvider>
        <div>App Content</div>
      </ToastProvider>,
    );
    expect(screen.getByText('App Content')).toBeInTheDocument();
  });
});
