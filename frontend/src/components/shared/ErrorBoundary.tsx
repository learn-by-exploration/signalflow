'use client';

import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  name?: string;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(
      `ErrorBoundary${this.props.name ? ` [${this.props.name}]` : ''} caught:`,
      error,
      errorInfo.componentStack,
    );
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="bg-bg-card border border-signal-sell/30 rounded-xl p-6 text-center">
            <p className="text-signal-sell font-display font-medium mb-2">
              {this.props.name
                ? `${this.props.name} had a problem loading`
                : 'Something went wrong'}
            </p>
            <p className="text-xs text-text-muted mb-3">Click below to retry, or refresh the page.</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="text-sm text-accent-purple hover:underline"
            >
              Try again
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
