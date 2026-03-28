import { useState, useMemo } from 'react';
import type { Route, RouteList } from '@/types/route';
import { RouteCard } from './RouteCard';

type SortMode = 'smart' | 'fastest' | 'cheapest';

interface FilterPrefs {
  directOnly: boolean;
  business: boolean;
  first: boolean;
  second: boolean;
}

interface RouteListPanelProps {
  routes: RouteList;
  selectedRoute: Route | null;
  date: string;
  filterPrefs: FilterPrefs;
  onSelect: (route: Route) => void;
  listRef: React.RefObject<HTMLDivElement | null>;
}

export function RouteListPanel({ routes, selectedRoute, date, filterPrefs, onSelect, listRef }: RouteListPanelProps) {
  const [sortMode, setSortMode] = useState<SortMode>('smart');

  const sorted = useMemo(() => {
    let arr = [...routes];
    if (filterPrefs.directOnly) {
      arr = arr.filter((r) => r.segs.length === 1);
    }
    if (sortMode === 'fastest') arr.sort((a, b) => a.durationMinutes - b.durationMinutes);
    if (sortMode === 'cheapest') {
      arr.sort((a, b) => {
        const allSeatsA = a.segs.flatMap((s) => ('transfer' in s ? [] : s.seats));
        const allSeatsB = b.segs.flatMap((s) => ('transfer' in s ? [] : s.seats));
        const pa = Math.min(...allSeatsA.filter((s) => s.available).map((s) => s.price));
        const pb = Math.min(...allSeatsB.filter((s) => s.available).map((s) => s.price));
        return pa - pb;
      });
    }
    return arr;
  }, [routes, sortMode]);

  const labels: Record<SortMode, string> = { smart: '智能推荐', fastest: '耗时最短', cheapest: '价格最低' };

  return (
    <div className="w-full h-full flex flex-col">
      {/* 粘性标题栏 */}
      <div
        className="sticky-header flex justify-between items-end border-b shrink-0"
        style={{ borderColor: 'rgba(255,255,255,0.1)' }}
      >
        <div className="text-lg font-serif italic text-starlight">
          {date || '今日'} 出行方案
        </div>
        <div className="flex gap-8 text-sm font-display tracking-[0.1em] uppercase text-muted">
          {(['smart', 'fastest', 'cheapest'] as SortMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setSortMode(mode)}
              className={`cursor-pointer transition-colors hover:text-starlight${sortMode === mode ? ' time-theme-text font-medium' : ''}`}
            >
              {labels[mode]}
            </button>
          ))}
        </div>
      </div>

      {/* 路线列表 */}
      <div
        ref={listRef}
        className="flex-1 overflow-y-auto pb-32 scroll-smooth pr-4"
        style={{ scrollbarWidth: 'none' }}
      >
        {sorted.map((route) => (
          <RouteCard
            key={route.id}
            route={route}
            isActive={selectedRoute?.id === route.id}
            onClick={onSelect}
          />
        ))}
      </div>
    </div>
  );
}
