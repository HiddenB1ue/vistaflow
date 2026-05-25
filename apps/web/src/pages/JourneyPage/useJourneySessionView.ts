import { useEffect, useMemo, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  fetchJourneySearchSessionView,
  type JourneyViewRequest,
  type JourneyViewResult,
} from '@/services/routeService';
import { createSessionStream } from '@/services/searchStreamService';
import { useSearchStore } from '@/stores/searchStore';
import { usePriceStore } from '@/stores/priceStore';
import { useRouteStore } from '@/stores/routeStore';
import type { Route } from '@/types/route';
import type { SearchParams } from '@/types/search';

interface StoredViewState {
  routes: Route[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  appliedView: JourneyViewResult['appliedView'] | null;
  availableFacets: JourneyViewResult['availableFacets'];
  sessionSearchId: string | null;
}

interface UseJourneySessionViewOptions extends StoredViewState {
  searchId: string | null;
  params: SearchParams;
  currentViewRequest: JourneyViewRequest;
  setSortMode: (mode: 'duration' | 'departure' | 'price') => void;
  setViewResult: (searchId: string, result: JourneyViewResult) => void;
  revealPage: () => void;
}

export function useJourneySessionView({
  searchId,
  params,
  currentViewRequest,
  routes,
  total,
  page,
  pageSize,
  totalPages,
  appliedView,
  availableFacets,
  sessionSearchId,
  setSortMode,
  setViewResult,
  revealPage,
}: UseJourneySessionViewOptions) {
  const navigate = useNavigate();
  const sseStarted = useRef(false);

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

  const query = useQuery({
    queryKey: ['journey-search-view', searchId, currentViewRequest],
    queryFn: () => fetchJourneySearchSessionView(searchId ?? '', currentViewRequest),
    enabled: Boolean(searchId),
    initialData,
  });

  useEffect(() => {
    if (searchId || sseStarted.current) return;
    if (!params.origin.trim() || !params.destination.trim()) {
      navigate('/', { replace: true });
      return;
    }
    sseStarted.current = true;

    createSessionStream(params)
      .then((session) => {
        const { setSearchId } = useSearchStore.getState();
        setSearchId(session.searchId);
        setSortMode('duration');
        setViewResult(session.searchId, session.viewResult);
        revealPage();
      })
      .catch((err) => {
        console.error('SSE session creation failed:', err);
      });
  }, [searchId, params, navigate, setSortMode, setViewResult, revealPage]);

  useEffect(() => {
    if (searchId) {
      revealPage();
    }
  }, [searchId, revealPage]);

  useEffect(() => {
    if (!searchId || !query.data) return;
    setViewResult(searchId, query.data);
    const priceMap = usePriceStore.getState().priceMap;
    if (Object.keys(priceMap).length > 0) {
      useRouteStore.getState().updateRoutesPrices(priceMap);
    }
  }, [query.data, searchId, setViewResult]);

  return query;
}
