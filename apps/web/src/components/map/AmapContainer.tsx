
import './map.css';
import { useEffect, useRef } from 'react';
import type { Route } from '@/types/route';
import { MAP_LABELS } from '@/constants/labels';
import { PulseMapOverlay } from './PulseMapOverlay';

interface AmapContainerProps {
  selectedRoute: Route | null;
}

declare global {
  interface Window {
    AMap?: unknown;
  }
}

export function AmapContainer({ selectedRoute }: AmapContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void containerRef.current;
    // 预留给后续接入 VITE_AMAP_KEY 与真实高德地图 SDK。
  }, []);

  return (
    <div ref={containerRef} className="relative h-full w-full" style={{ backgroundColor: 'var(--color-bg)' }}>
      <div className="absolute inset-0" id="amap-root" />

      <div className="pointer-events-none absolute inset-0">
        <PulseMapOverlay selectedRoute={selectedRoute} width={400} height={600} />
      </div>

      {!window.AMap && (
        <div
          className="absolute bottom-4 left-4 flex items-center gap-2 text-xs uppercase tracking-widest"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          <span className="h-1.5 w-1.5 animate-pulse rounded-full" style={{ backgroundColor: 'var(--color-pulse)' }} />
          {MAP_LABELS.noMapHint}
        </div>
      )}
    </div>
  );
}
