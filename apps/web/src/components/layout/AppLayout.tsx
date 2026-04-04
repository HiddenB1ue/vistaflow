
import './TransitionOverlay.css';
import { useEffect, useRef } from 'react';
import { Outlet } from 'react-router-dom';
import { ErrorBoundary } from '@vistaflow/ui';
import { TRANSITION_LABELS } from '@/constants/labels';
import { usePageTransition } from '@/hooks/usePageTransition';

export function AppLayout() {
  const curtainRef = useRef<HTMLDivElement>(null);
  const { setCurtainRef } = usePageTransition();

  useEffect(() => {
    const el = curtainRef.current;
    if (!el) return;
    setCurtainRef(el);
  }, [setCurtainRef]);

  return (
    <div className="relative min-h-screen" style={{ backgroundColor: 'var(--color-bg)' }}>
      <div ref={curtainRef} className="transition-overlay" style={{ display: 'none' }}>
        <div className="loading-text">{TRANSITION_LABELS.loading}</div>
        <div
          className="loading-bar-container hidden"
          style={{
            width: '12rem',
            height: '1px',
            background: 'rgba(255,255,255,0.1)',
            marginTop: '1.5rem',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div className="loading-bar absolute left-0 top-0 h-full time-theme-bg" style={{ width: '33.333%' }} />
        </div>
      </div>
      <ErrorBoundary>
        <Outlet />
      </ErrorBoundary>
    </div>
  );
}
