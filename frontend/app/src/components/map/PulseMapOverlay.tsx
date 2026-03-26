import type { Route } from '@/types/route';

interface PulseMapOverlayProps {
  selectedRoute: Route | null;
  width: number;
  height: number;
}

/** 纯 SVG 地图叠加层，不 import 高德 SDK */
export function PulseMapOverlay({ selectedRoute, width, height }: PulseMapOverlayProps) {
  if (!selectedRoute) return null;

  const points = selectedRoute.pathPoints;
  if (points.length < 2) return null;

  // 将经纬度映射到 SVG 坐标系
  const lngs = points.map((p) => p.lng);
  const lats = points.map((p) => p.lat);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const padding = 20;

  const toX = (lng: number) =>
    padding + ((lng - minLng) / (maxLng - minLng || 1)) * (width - padding * 2);
  const toY = (lat: number) =>
    height - padding - ((lat - minLat) / (maxLat - minLat || 1)) * (height - padding * 2);

  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(p.lng)} ${toY(p.lat)}`)
    .join(' ');

  const origin = points[0];
  const dest = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
    >
      {/* 路径线 */}
      <path
        d={pathD}
        fill="none"
        stroke="var(--color-pulse-dim)"
        strokeWidth={1.5}
        strokeDasharray="4 4"
      />

      {/* 途经点 */}
      {points.slice(1, -1).map((p, i) => (
        <circle
          key={i}
          cx={toX(p.lng)}
          cy={toY(p.lat)}
          r={3}
          fill="rgba(255,255,255,0.2)"
        />
      ))}

      {/* 起点脉冲 */}
      <circle
        cx={toX(origin.lng)}
        cy={toY(origin.lat)}
        r={5}
        fill="var(--color-pulse)"
        opacity={0.9}
      />

      {/* 终点脉冲 */}
      <circle
        cx={toX(dest.lng)}
        cy={toY(dest.lat)}
        r={5}
        fill="var(--color-pulse)"
        opacity={0.9}
      />
    </svg>
  );
}
