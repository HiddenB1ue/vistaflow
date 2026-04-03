import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Navbar } from '@/components/layout/Navbar';
import { AuraBackground, NoiseTexture } from '@vistaflow/ui';
import { AmapContainer } from '@/components/map/AmapContainer';
import { FilterDrawer } from '@/components/overlays/FilterDrawer';
import { RouteListPanel } from './RouteListPanel';
import { useSearchStore } from '@/stores/searchStore';
import { useRouteStore } from '@/stores/routeStore';
import { useUiStore } from '@/stores/uiStore';
import { fetchRoutes } from '@/services/routeService';
import { useCardReveal } from '@/hooks/useCardReveal';
import { usePageTransition } from '@/hooks/usePageTransition';
import type { Route } from '@/types/route';

export function JourneyPage() {
  const params = useSearchStore((s) => s.params);
  const { routes, selectedRoute, setRoutes, selectRoute } = useRouteStore();
  const { revealPage } = usePageTransition();
  const {
    isJourneyFilterOpen,
    journeyFilterPrefs,
    setJourneyFilterOpen,
    setJourneyFilterPrefs,
  } = useUiStore();

  const { data, isLoading } = useQuery({
    queryKey: ['routes', params],
    queryFn: () => fetchRoutes(params),
  });

  useEffect(() => {
    revealPage();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (data) {
      setRoutes(data);
      if (data.length > 0) selectRoute(data[0]);
    }
  }, [data, setRoutes, selectRoute]);

  const listRef = useCardReveal([routes]);

  const handleSelect = (route: Route) => selectRoute(route);

  return (
    <div
      className="relative min-h-screen"
      style={{ backgroundColor: 'var(--color-bg)' }}
    >
      <AuraBackground enableMouseTracking={true} />
      <NoiseTexture />
      <Navbar onFilterOpen={() => setJourneyFilterOpen(!isJourneyFilterOpen)} />

      <FilterDrawer
        isOpen={isJourneyFilterOpen}
        directOnly={journeyFilterPrefs.directOnly}
        business={journeyFilterPrefs.business}
        first={journeyFilterPrefs.first}
        second={journeyFilterPrefs.second}
        onDirectOnlyChange={(v) => setJourneyFilterPrefs({ directOnly: v })}
        onBusinessChange={(v) => setJourneyFilterPrefs({ business: v })}
        onFirstChange={(v) => setJourneyFilterPrefs({ first: v })}
        onSecondChange={(v) => setJourneyFilterPrefs({ second: v })}
        onClose={() => setJourneyFilterOpen(false)}
      />

      <section
        id="results-dashboard"
        className="fixed inset-0 z-40 pt-32 pb-10 px-8 lg:px-20 flex flex-col lg:flex-row gap-12"
      >
        {/* 左侧：地图 */}
        <div className="w-full lg:w-4/12 h-full flex flex-col border-r shrink-0" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
          <div className="mb-10 pr-10">
            <div className="text-xs time-theme-text font-display tracking-[0.3em] uppercase mb-4 opacity-80">Route Map</div>
            <h2 className="font-serif text-5xl italic font-light text-starlight mb-2">
              {params.origin || '出发地'} 到 {params.destination || '目的地'}
            </h2>
            <div className="text-sm text-muted">
              {selectedRoute ? `已选择方案: ${selectedRoute.id}` : '未选择具体方案，全览模式。'}
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center py-10 relative">
            <AmapContainer selectedRoute={selectedRoute} />
          </div>

          <div className="text-xs text-muted font-display tracking-widest uppercase flex items-center gap-3">
            <div className="w-1.5 h-1.5 time-theme-bg rounded-full animate-pulse" />
            <span>{selectedRoute ? 'AI 实时路线推演' : 'AI 宏观拓扑预演'}</span>
          </div>
        </div>

        {/* 右侧：路线列表 */}
        <div className="w-full lg:w-8/12 h-full flex flex-col pl-2 relative overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-sm tracking-widest text-muted">
              正在检索出行方案…
            </div>
          ) : (
            <RouteListPanel
              routes={routes}
              selectedRoute={selectedRoute}
              date={params.date}
              filterPrefs={journeyFilterPrefs}
              onSelect={handleSelect}
              listRef={listRef}
            />
          )}
        </div>
      </section>
    </div>
  );
}
