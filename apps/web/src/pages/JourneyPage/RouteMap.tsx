import './RouteMap.css';
import 'maplibre-gl/dist/maplibre-gl.css';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Map as MapGL,
  Source,
  Layer,
  Marker,
  NavigationControl,
} from 'react-map-gl/maplibre';
import type { MapRef } from 'react-map-gl/maplibre';
import type { LngLatBoundsLike } from 'maplibre-gl';
import type { Route } from '@/types/route';
import { isTransfer } from '@/types/route';
import type { RouteStopGeo } from '@/services/routeService';
import { useUiStore } from '@/stores/uiStore';
import { convertRouteListToWgs84, convertPointToWgs84 } from '@/services/coordinateService';
import { REMOTE_STYLE_URL, TILE_SERVER_URL, ROUTE_COLORS } from './mapStyle';

/** 单条路线 GCJ-02 → WGS-84 */
function toWgs84(route: Route): Route {
  return convertRouteListToWgs84([route])[0];
}

/** 中国中心点默认视角 */
const DEFAULT_CENTER = { longitude: 104.5, latitude: 35.5 };
const DEFAULT_ZOOM = 3.5;

/** 脉冲参数 */
const PULSE_COUNT = 2;
const PULSE_WIDTH = 0.15;
const PULSE_DURATION = 3500;
const PULSE_SAMPLES = 48;

interface RouteMapProps {
  route: Route | null;
  routes: Route[];
  stopsGeo: RouteStopGeo[];
}

/** 从 Route 的 pathPoints 构建 GeoJSON LineString */
function buildRouteGeoJSON(
  route: Route,
): GeoJSON.Feature<GeoJSON.LineString> {
  return {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'LineString',
      coordinates: route.pathPoints.map(({ lng, lat }) => [lng, lat]),
    },
  };
}

interface StationMarkerData {
  key: string;
  name: string;
  lng: number;
  lat: number;
  role: 'origin' | 'destination' | 'transfer' | 'stop';
}

function collectStationMarkers(route: Route): StationMarkerData[] {
  const markers: StationMarkerData[] = [];
  const seen = new Set<string>();

  const add = (name: string, lng: number, lat: number, role: StationMarkerData['role']) => {
    if (seen.has(name)) return;
    seen.add(name);
    if (lng === 0 && lat === 0) return;
    markers.push({ key: `${role}-${name}`, name, lng, lat, role });
  };

  add(route.origin.name, route.origin.lng, route.origin.lat, 'origin');

  for (const seg of route.segs) {
    if (isTransfer(seg)) continue;
    add(seg.destination.name, seg.destination.lng, seg.destination.lat, 'transfer');
  }

  // Override the last added marker's role to 'destination'
  if (markers.length > 0) {
    const last = markers[markers.length - 1];
    if (last.name === route.destination.name) {
      last.role = 'destination';
      last.key = `destination-${last.name}`;
    }
  }

  return markers;
}

function computeBounds(
  points: Array<{ lng: number; lat: number }>,
): LngLatBoundsLike | null {
  const valid = points.filter(({ lng, lat }) => lng !== 0 || lat !== 0);
  if (valid.length === 0) return null;

  let minLng = Infinity;
  let maxLng = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;

  for (const { lng, lat } of valid) {
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }

  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

/** hex → [r, g, b] */
function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/**
 * 生成脉冲 line-gradient 表达式。
 * 多道光波沿线流向终点，线本身明暗呼吸，终点方向整体渐弱。
 */
function buildPulseGradient(
  progress: number,
  rgb: [number, number, number],
// eslint-disable-next-line @typescript-eslint/no-explicit-any
): any[] {
  const [r, g, b] = rgb;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const expr: any[] = ['interpolate', ['linear'], ['line-progress']];

  for (let s = 0; s <= PULSE_SAMPLES; s++) {
    const p = s / PULSE_SAMPLES;
    let peak = 0;
    for (let i = 0; i < PULSE_COUNT; i++) {
      const c = (progress + i / PULSE_COUNT) % 1;
      const d = Math.min(
        Math.abs(p - c),
        Math.abs(p - c + 1),
        Math.abs(p - c - 1),
      );
      const f = Math.max(0, 1 - d / PULSE_WIDTH);
      peak = Math.max(peak, f * f);
    }
    const dirFade = 1 - p * 0.35;
    const a = (0.05 + peak * 0.95) * dirFade;
    expr.push(p, `rgba(${r},${g},${b},${a.toFixed(3)})`);
  }

  return expr;
}

export function RouteMap({ route, routes, stopsGeo }: RouteMapProps) {
  const theme = useUiStore((s) => s.theme);
  const colors = ROUTE_COLORS[theme];
  const mapRef = useRef<MapRef>(null);
  const [styleLoaded, setStyleLoaded] = useState(false);

  const wgsRoute = useMemo(() => (route ? toWgs84(route) : null), [route]);

  /** 未选中方案时，从首条路线取起终点作为概览 */
  const overviewRoute = useMemo(() => {
    if (wgsRoute || routes.length === 0) return null;
    const first = toWgs84(routes[0]);
    const { origin, destination } = first;
    if (origin.lng === 0 && origin.lat === 0) return null;
    if (destination.lng === 0 && destination.lat === 0) return null;
    return first;
  }, [wgsRoute, routes]);

  /** 当前实际用于渲染的路线数据：选中路线 > 概览路线 */
  const activeRoute = wgsRoute ?? overviewRoute;
  const isOverview = activeRoute !== null && wgsRoute === null;

  /** stopsGeo 坐标 GCJ-02 → WGS-84 */
  const wgsStopsGeo = useMemo(
    () => (wgsRoute && stopsGeo.length > 0
      ? stopsGeo.map((s) => ({ name: s.name, ...convertPointToWgs84(s) }))
      : []),
    [wgsRoute, stopsGeo],
  );

  const routeGeoJSON = useMemo(
    () => {
      if (!activeRoute) return null;
      if (isOverview) {
        return {
          type: 'Feature' as const,
          properties: {},
          geometry: {
            type: 'LineString' as const,
            coordinates: [
              [activeRoute.origin.lng, activeRoute.origin.lat],
              [activeRoute.destination.lng, activeRoute.destination.lat],
            ],
          },
        };
      }
      if (wgsStopsGeo.length > 0) {
        return {
          type: 'Feature' as const,
          properties: {},
          geometry: {
            type: 'LineString' as const,
            coordinates: wgsStopsGeo.map(({ lng, lat }) => [lng, lat]),
          },
        };
      }
      return buildRouteGeoJSON(activeRoute);
    },
    [activeRoute, isOverview, wgsStopsGeo],
  );

  const stationMarkers = useMemo(
    () => {
      if (!activeRoute) return [];
      if (isOverview) {
        const markers: StationMarkerData[] = [];
        const { origin, destination } = activeRoute;
        if (origin.lng !== 0 || origin.lat !== 0) {
          markers.push({ key: 'origin', name: origin.name, lng: origin.lng, lat: origin.lat, role: 'origin' });
        }
        if (destination.lng !== 0 || destination.lat !== 0) {
          markers.push({ key: 'destination', name: destination.name, lng: destination.lng, lat: destination.lat, role: 'destination' });
        }
        return markers;
      }
      const base = collectStationMarkers(activeRoute);
      if (wgsStopsGeo.length === 0) return base;

      const baseNames = new Set(base.map((m) => m.name));
      const stopMarkers: StationMarkerData[] = wgsStopsGeo
        .filter((s) => !baseNames.has(s.name))
        .map((s) => ({ key: `stop-${s.name}`, name: s.name, lng: s.lng, lat: s.lat, role: 'stop' as const }));
      return [...base, ...stopMarkers];
    },
    [activeRoute, isOverview, wgsStopsGeo],
  );

  // fitBounds when active route changes (or when map style finishes loading)
  useEffect(() => {
    if (!activeRoute || !mapRef.current || !styleLoaded) return;

    const allPoints: Array<{ lng: number; lat: number }> = [
      ...activeRoute.pathPoints,
      ...stationMarkers.map(({ lng, lat }) => ({ lng, lat })),
    ];
    const bounds = computeBounds(allPoints);
    if (!bounds) return;

    mapRef.current.fitBounds(bounds, {
      padding: { top: 60, bottom: 60, left: 40, right: 40 },
      maxZoom: 12,
      duration: 800,
    });
  }, [activeRoute, styleLoaded, stationMarkers]);

  // Animated pulse — line itself breathes with traveling light waves
  useEffect(() => {
    const map = mapRef.current?.getMap();
    if (!map || !wgsRoute || !styleLoaded) return;
    if (!map.getSource('route')) return;

    const rgb = hexToRgb(colors.line);

    map.addLayer({
      id: 'route-pulse',
      type: 'line',
      source: 'route',
      paint: {
        'line-width': 2.5,
        'line-gradient': buildPulseGradient(0, rgb) as never,
      },
      layout: { 'line-cap': 'round', 'line-join': 'round' },
    });

    let animId: number;
    const animate = (ts: number) => {
      const t = (ts % PULSE_DURATION) / PULSE_DURATION;
      map.setPaintProperty('route-pulse', 'line-gradient', buildPulseGradient(t, rgb));
      animId = requestAnimationFrame(animate);
    };
    animId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animId);
      try { if (map.getLayer('route-pulse')) map.removeLayer('route-pulse'); } catch { /* unmount race */ }
    };
  }, [wgsRoute, styleLoaded, colors]);

  const handleLoad = useCallback(() => {
    setStyleLoaded(true);
  }, []);

  return (
    <div className="route-map">
      <MapGL
        ref={mapRef}
        initialViewState={{
          ...DEFAULT_CENTER,
          zoom: DEFAULT_ZOOM,
        }}
        mapStyle={REMOTE_STYLE_URL}
        onLoad={handleLoad}
        transformRequest={(url) => {
          if (url.startsWith('/')) {
            return { url: `${TILE_SERVER_URL}${url}` };
          }
          return { url };
        }}
        attributionControl={false}
      >
        <NavigationControl position="top-right" showCompass={false} />

        {styleLoaded && routeGeoJSON && (
          <Source id="route" type="geojson" data={routeGeoJSON} lineMetrics>
            {/* 实心底层轨迹线 (增加实体感) */}
            {!isOverview && (
              <Layer
                id="route-base"
                type="line"
                paint={{
                  'line-color': '#ffffff',
                  'line-width': 1.5,
                  'line-opacity': 0.15,
                }}
                layout={{ 'line-cap': 'round', 'line-join': 'round' }}
              />
            )}
            
            {/* 静态大面积柔光底层 */}
            <Layer
              id="route-glow-outer"
              type="line"
              paint={{
                'line-color': colors.glow,
                'line-width': isOverview ? 8 : 16,
                'line-blur': isOverview ? 8 : 12,
                'line-opacity': isOverview ? 0.15 : 0.3,
              }}
            />
            {/* 核心内层高光 */}
            <Layer
              id="route-glow-inner"
              type="line"
              paint={{
                'line-color': colors.station,
                'line-width': isOverview ? 3 : 5,
                'line-blur': isOverview ? 2 : 3,
                'line-opacity': isOverview ? 0.4 : 0.8,
              }}
            />
            
            {/* 概览模式：纤细的追踪虚线 */}
            {isOverview && (
              <Layer
                id="route-overview-line"
                type="line"
                paint={{
                  'line-color': colors.line,
                  'line-width': 1.5,
                  'line-opacity': 0.5,
                  'line-dasharray': [2, 4],
                }}
                layout={{ 'line-cap': 'round', 'line-join': 'round' }}
              />
            )}
          </Source>
        )}

        {styleLoaded &&
          stationMarkers.map((marker) => (
            <Marker
              key={marker.key}
              longitude={marker.lng}
              latitude={marker.lat}
              anchor="center"
            >
              <div
                className="route-map-marker"
                style={{ '--marker-color': colors.station } as React.CSSProperties}
              >
                <div
                  className={`route-map-marker__dot route-map-marker__dot--${marker.role}`}
                />
                <div className="route-map-marker__label">{marker.name}</div>
              </div>
            </Marker>
          ))}
      </MapGL>

      {!route && routes.length === 0 && (
        <div className="route-map-empty">
          <span className="route-map-empty__text">选择方案查看路线</span>
        </div>
      )}
    </div>
  );
}
