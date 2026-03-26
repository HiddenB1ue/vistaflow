import { useRef, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { usePageTransition } from '@/hooks/usePageTransition';

export function AppLayout() {
  const curtainRef = useRef<HTMLDivElement>(null);
  const { setCurtainRef } = usePageTransition();

  useEffect(() => {
    const el = curtainRef.current;
    if (!el) return;
    setCurtainRef(el);
    // 不在 AppLayout 触发 revealPage，由各页面自行在 mount 后调用
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="relative min-h-screen" style={{ backgroundColor: 'var(--color-bg)' }}>
      {/* 剧场级转场幕布 */}
      <div
        ref={curtainRef}
        className="transition-overlay"
        style={{ display: 'none' }}
      >
        <div className="loading-text">环境感知中...</div>
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
          <div
            className="loading-bar absolute left-0 top-0 h-full time-theme-bg"
            style={{
              width: '33.333%',
            }}
          />
        </div>
      </div>
      <Outlet />
    </div>
  );
}
