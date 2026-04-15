import { useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AuraBackground,
  ContentSection,
  DrawerBackdrop,
  NoiseTexture,
  PageHeader,
} from '@vistaflow/ui';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';
import { AmapContainer } from '@/components/map/AmapContainer';
import { JourneyViewDrawer } from '@/components/overlays/JourneyViewDrawer';
import { JOURNEY_LABELS } from '@/constants/labels';
import { useCardReveal } from '@/hooks/useCardReveal';
import { usePageTransition } from '@/hooks/usePageTransition';
import {
  buildJourneyViewRequest,
  fetchJourneySearchSessionView,
} from '@/services/routeService';
import { useRouteStore } from '@/stores/routeStore';
import { useSearchStore } from '@/stores/searchStore';
import { useUiStore } from '@/stores/uiStore';
import type { Route } from '@/types/route';
import { RouteListPanel } from './RouteListPanel';

export function JourneyPage() {
  const navigate = useNavigate();
  const params = useSearchStore((state) => state.params);
  const searchId = useSearchStore((state) => state.searchId);
  const {
    routes,
    selectedRoute,
    total,
    page,
    pageSize,
    totalPages,
    sortMode,
    appliedView,
    availableFacets,
    sessionSearchId,
    setViewResult,
    selectRoute,
    setPage,
    setPageSize,
    setSortMode,
  } = useRouteStore();
  const { revealPage } = usePageTransition();
  const {
    isJourneyFilterOpen,
    journeyFilterPrefs,
    setJourneyFilterOpen,
    setJourneyFilterPrefs,
    resetJourneyFilterPrefs,
  } = useUiStore();

  const currentViewRequest = useMemo(
    () => buildJourneyViewRequest(journeyFilterPrefs, sortMode, page, pageSize),
    [journeyFilterPrefs, sortMode, page, pageSize],
  );

  const initialData = useMemo(() => {
    if (!searchId || sessionSearchId !== searchId || appliedView === null) {
      return undefined;
    }

    const matchesCurrentView =
      appliedView.page === currentViewRequest.page &&
      appliedView.pageSize === currentViewRequest.page_size &&
      appliedView.sortBy === currentViewRequest.sort_by &&
      appliedView.excludeDirectTrainCodesInTransferRoutes ===
        currentViewRequest.exclude_direct_train_codes_in_transfer_routes &&
      appliedView.displayTrainTypes.join(',') ===
        currentViewRequest.display_train_types.join(',') &&
      appliedView.transferCounts.join(',') === currentViewRequest.transfer_counts.join(',');

    if (!matchesCurrentView) {
      return undefined;
    }

    return {
      items: routes,
      total,
      page,
      pageSize,
      totalPages,
      appliedView,
      availableFacets,
    };
  }, [
    appliedView,
    availableFacets,
    currentViewRequest,
    page,
    pageSize,
    routes,
    searchId,
    sessionSearchId,
    total,
    totalPages,
  ]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['journey-search-view', searchId, currentViewRequest],
    queryFn: () => fetchJourneySearchSessionView(searchId ?? '', currentViewRequest),
    enabled: Boolean(searchId),
    initialData,
  });

  useEffect(() => {
    revealPage();
  }, [revealPage]);

  useEffect(() => {
    if (!searchId || !data) return;
    setViewResult(searchId, data);
  }, [data, searchId, setViewResult]);

  useEffect(() => {
    if (!searchId) {
      navigate('/', { replace: true });
    }
  }, [navigate, searchId]);

  const listRef = useCardReveal([routes]);
  const handleSelect = (route: Route) => selectRoute(route);
  const sessionExpired = error instanceof Error;

  return (
    <div
      className="relative min-h-screen"
      style={{ backgroundColor: 'var(--color-bg)' }}
    >
      <AuraBackground enableMouseTracking />
      <NoiseTexture />
      <DrawerBackdrop
        isActive={isJourneyFilterOpen}
        onClick={() => setJourneyFilterOpen(false)}
      />
      <Navbar onFilterOpen={() => setJourneyFilterOpen(!isJourneyFilterOpen)} />

      <JourneyViewDrawer
        isOpen={isJourneyFilterOpen}
        prefs={journeyFilterPrefs}
        onChange={(patch) => {
          setJourneyFilterPrefs(patch);
          setPage(1);
        }}
        onClose={() => setJourneyFilterOpen(false)}
      />

      <section
        id="results-dashboard"
        className="vf-page-gutter fixed inset-0 z-40 flex flex-col gap-6 lg:flex-row"
        style={{
          paddingTop: 'calc(var(--vf-topbar-clearance) - 1rem)',
          paddingBottom: 'var(--vf-page-bottom-space)',
        }}
      >
        <div
          className="flex h-full w-full shrink-0 flex-col border-r lg:w-4/12"
          style={{ borderColor: 'rgba(255,255,255,0.1)' }}
        >
          <PageHeader
            className="border-b border-white/8 px-0 pb-5 pt-0 pr-8"
            eyebrow={JOURNEY_LABELS.mapEyebrow}
            title={<>{params.origin || '出发地'} → {params.destination || '目的地'}</>}
            subtitle={
              selectedRoute
                ? JOURNEY_LABELS.selectedRouteHint(selectedRoute.id)
                : JOURNEY_LABELS.noSelectionHint
            }
          />

          <div className="relative flex flex-1 items-center justify-center py-6">
            <AmapContainer selectedRoute={selectedRoute} />
          </div>

          <div className="flex items-center gap-3 text-xs font-display uppercase tracking-widest text-muted">
            <div className="time-theme-bg h-1.5 w-1.5 animate-pulse rounded-full" />
            <span>
              {selectedRoute ? JOURNEY_LABELS.mapStatus : JOURNEY_LABELS.mapStatusIdle}
            </span>
          </div>
        </div>

        <div className="relative flex h-full w-full flex-col overflow-hidden pl-2 lg:w-8/12">
          {sessionExpired ? (
            <ContentSection className="flex flex-1 flex-col items-center justify-center gap-6 text-sm tracking-widest text-muted">
              <div>搜索会话已过期，请重新搜索。</div>
              <button
                type="button"
                className="rounded-full border border-white/10 px-6 py-3 text-xs uppercase tracking-[0.2em] text-starlight"
                onClick={() => navigate('/', { replace: true })}
              >
                返回搜索页
              </button>
            </ContentSection>
          ) : isLoading ? (
            <ContentSection className="flex-1 items-center justify-center text-sm tracking-widest text-muted">
              {JOURNEY_LABELS.loading}
            </ContentSection>
          ) : (
            <RouteListPanel
              routes={routes}
              selectedRoute={selectedRoute}
              date={params.date}
              total={total}
              pageSize={pageSize}
              sortMode={sortMode}
              appliedView={appliedView}
              availableFacets={availableFacets}
              onClearFilters={() => {
                resetJourneyFilterPrefs();
                setPage(1);
              }}
              onSelect={handleSelect}
              onSortModeChange={setSortMode}
              onPageSizeChange={setPageSize}
              onTransferCountsChange={(transferCounts) => {
                setJourneyFilterPrefs({ transferCounts });
                setPage(1);
              }}
              onDisplayTrainTypesChange={(displayTrainTypes) => {
                setJourneyFilterPrefs({ displayTrainTypes });
                setPage(1);
              }}
              listRef={listRef}
            />
          )}
        </div>
      </section>
    </div>
  );
}
