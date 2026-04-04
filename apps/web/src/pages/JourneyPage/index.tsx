
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AuraBackground, ContentSection, DrawerBackdrop, NoiseTexture, PageHeader } from '@vistaflow/ui';
import { Navbar } from '@/components/layout/Navbar';
import { AmapContainer } from '@/components/map/AmapContainer';
import { FilterDrawer } from '@/components/overlays/FilterDrawer';
import { JOURNEY_LABELS } from '@/constants/labels';
import { useCardReveal } from '@/hooks/useCardReveal';
import { usePageTransition } from '@/hooks/usePageTransition';
import { fetchRoutes } from '@/services/routeService';
import { useRouteStore } from '@/stores/routeStore';
import { useSearchStore } from '@/stores/searchStore';
import { useUiStore } from '@/stores/uiStore';
import type { Route } from '@/types/route';
import { RouteListPanel } from './RouteListPanel';

export function JourneyPage() {
  const params = useSearchStore((state) => state.params);
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
  }, [revealPage]);

  useEffect(() => {
    if (!data) return;
    setRoutes(data);
    if (data.length > 0) {
      selectRoute(data[0]);
    }
  }, [data, selectRoute, setRoutes]);

  const listRef = useCardReveal([routes]);
  const handleSelect = (route: Route) => selectRoute(route);

  return (
    <div className="relative min-h-screen" style={{ backgroundColor: 'var(--color-bg)' }}>
      <AuraBackground enableMouseTracking />
      <NoiseTexture />
      <DrawerBackdrop isActive={isJourneyFilterOpen} onClick={() => setJourneyFilterOpen(false)} />
      <Navbar onFilterOpen={() => setJourneyFilterOpen(!isJourneyFilterOpen)} />

      <FilterDrawer
        isOpen={isJourneyFilterOpen}
        directOnly={journeyFilterPrefs.directOnly}
        business={journeyFilterPrefs.business}
        first={journeyFilterPrefs.first}
        second={journeyFilterPrefs.second}
        onDirectOnlyChange={(value) => setJourneyFilterPrefs({ directOnly: value })}
        onBusinessChange={(value) => setJourneyFilterPrefs({ business: value })}
        onFirstChange={(value) => setJourneyFilterPrefs({ first: value })}
        onSecondChange={(value) => setJourneyFilterPrefs({ second: value })}
        onClose={() => setJourneyFilterOpen(false)}
      />

      <section
        id="results-dashboard"
        className="vf-page-gutter fixed inset-0 z-40 flex flex-col gap-10 lg:flex-row"
        style={{ paddingTop: 'var(--vf-topbar-clearance)', paddingBottom: 'var(--vf-page-bottom-space)' }}
      >
        <div className="flex h-full w-full shrink-0 flex-col border-r lg:w-4/12" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
          <PageHeader
            className="border-b border-white/8 px-0 pb-8 pt-0 pr-8"
            eyebrow={JOURNEY_LABELS.mapEyebrow}
            title={<>{params.origin || '出发地'} → {params.destination || '目的地'}</>}
            subtitle={selectedRoute ? JOURNEY_LABELS.selectedRouteHint(selectedRoute.id) : JOURNEY_LABELS.noSelectionHint}
          />

          <div className="relative flex flex-1 items-center justify-center py-10">
            <AmapContainer selectedRoute={selectedRoute} />
          </div>

          <div className="flex items-center gap-3 text-xs font-display uppercase tracking-widest text-muted">
            <div className="time-theme-bg h-1.5 w-1.5 animate-pulse rounded-full" />
            <span>{selectedRoute ? JOURNEY_LABELS.mapStatus : JOURNEY_LABELS.mapStatusIdle}</span>
          </div>
        </div>

        <div className="relative flex h-full w-full flex-col overflow-hidden pl-2 lg:w-8/12">
          {isLoading ? (
            <ContentSection className="flex-1 items-center justify-center text-sm tracking-widest text-muted">
              {JOURNEY_LABELS.loading}
            </ContentSection>
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
