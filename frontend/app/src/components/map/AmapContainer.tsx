import { useRef, useEffect } from 'react';
import type { Route } from '@/types/route';
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
    // 高德地图初始化占位：VITE_AMAP_KEY 配置后此处加载 SDK
    // 当前仅渲染 SVG 叠加层
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full"
      style={{ backgroundColor: 'var(--color-bg)' }}
    >
      {/* 地图底图（高德 SDK 挂载点） */}
      <div className="absolute inset-0" id="amap-root" />

      {/* SVG 叠加层 */}
      <div className="absolute inset-0 pointer-events-none">
        <PulseMapOverlay
          selectedRoute={selectedRoute}
          width={400}
          height={600}
        />
      </div>

      {/* 无地图时的状态提示 */}
      {!window.AMap && (
        <div
          className="absolute bottom-4 left-4 text-xs tracking-widest uppercase flex items-center gap-2"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full animate-pulse"
            style={{ backgroundColor: 'var(--color-pulse)' }}
          />
          AI 宏观拓扑预演
        </div>
      )}
    </div>
  );
}
