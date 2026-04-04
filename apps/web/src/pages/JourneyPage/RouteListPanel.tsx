
import './RouteListPanel.css';
import { useMemo, useState, type RefObject } from 'react';
import type { Route, RouteList } from '@/types/route';
import type { FilterPrefs } from '@/stores/uiStore';
import { JOURNEY_LABELS } from '@/constants/labels';
import { PanelCard, SectionHeader, SegmentedControl } from '@vistaflow/ui';
import { RouteCard } from './RouteCard';
import { filterAndSortRoutes, SORT_OPTIONS, type SortMode } from './routeList.helpers';

interface RouteListPanelProps {
  routes: RouteList;
  selectedRoute: Route | null;
  date: string;
  filterPrefs: FilterPrefs;
  onSelect: (route: Route) => void;
  listRef: RefObject<HTMLDivElement | null>;
}

export function RouteListPanel({ routes, selectedRoute, date, filterPrefs, onSelect, listRef }: RouteListPanelProps) {
  const [sortMode, setSortMode] = useState<SortMode>('smart');

  const sortedRoutes = useMemo(
    () => filterAndSortRoutes(routes, filterPrefs, sortMode),
    [routes, filterPrefs, sortMode],
  );

  return (
    <PanelCard className="h-full overflow-hidden border-none bg-transparent p-0 shadow-none">
      <div className="sticky-header shrink-0 px-2 pt-2" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
        <SectionHeader
          eyebrow={JOURNEY_LABELS.routeListEyebrow}
          title={JOURNEY_LABELS.routeListTitle(date)}
          subtitle={JOURNEY_LABELS.routeListSubtitle(sortedRoutes.length)}
          actions={<SegmentedControl size="sm" value={sortMode} onChange={setSortMode} options={SORT_OPTIONS} />}
        />
      </div>

      <div ref={listRef} className="flex-1 overflow-y-auto scroll-smooth pb-32 pr-4 pt-4" style={{ scrollbarWidth: 'none' }}>
        {sortedRoutes.map((route) => (
          <RouteCard key={route.id} route={route} isActive={selectedRoute?.id === route.id} onClick={onSelect} />
        ))}
      </div>
    </PanelCard>
  );
}
