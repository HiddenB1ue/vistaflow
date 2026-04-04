import { Component, type ReactNode } from 'react';
import { ErrorFallback } from './ErrorFallback';

export interface ErrorBoundaryProps {
  fallback?: ReactNode | ((error: Error, reset: () => void) => ReactNode);
  onReset?: () => void;
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  handleReset = () => {
    this.setState({ error: null });
    this.props.onReset?.();
  };

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    const { fallback } = this.props;
    if (typeof fallback === 'function') {
      return fallback(error, this.handleReset);
    }
    if (fallback) return fallback;
    return <ErrorFallback error={error} onReset={this.handleReset} />;
  }
}
