import type { ReactNode } from 'react';

export interface ErrorFallbackLabels {
  eyebrow: string;
  title: string;
  resetLabel: string;
}

export interface ErrorFallbackProps {
  error: Error;
  onReset: () => void;
  labels?: Partial<ErrorFallbackLabels>;
}

const DEFAULT_LABELS: ErrorFallbackLabels = {
  eyebrow: '发生错误',
  title: '页面暂时无法显示',
  resetLabel: '重试',
};

export function ErrorFallback({ error, onReset, labels }: ErrorFallbackProps): ReactNode {
  const resolvedLabels = { ...DEFAULT_LABELS, ...labels };

  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '40vh',
        gap: '1.5rem',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '0.65rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#F87171' }}>
        {resolvedLabels.eyebrow}
      </div>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 300, color: '#F5F5F7' }}>
        {resolvedLabels.title}
      </h2>
      <pre
        style={{
          maxWidth: '32rem',
          padding: '1rem',
          borderRadius: '8px',
          background: 'rgba(248,113,113,0.08)',
          border: '1px solid rgba(248,113,113,0.2)',
          color: '#F87171',
          fontSize: '0.75rem',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {error.message}
      </pre>
      <button
        onClick={onReset}
        style={{
          padding: '0.625rem 1.5rem',
          borderRadius: '9999px',
          border: '1px solid rgba(255,255,255,0.15)',
          background: 'transparent',
          color: '#F5F5F7',
          fontSize: '0.8125rem',
          cursor: 'pointer',
          letterSpacing: '0.05em',
        }}
      >
        {resolvedLabels.resetLabel}
      </button>
    </div>
  );
}
