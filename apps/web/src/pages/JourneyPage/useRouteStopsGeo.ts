import { useQuery } from '@tanstack/react-query';
import { fetchRouteStopsGeo } from '@/services/routeService';
import type { Route } from '@/types/route';

export function useRouteStopsGeo(route: Route | null) {
  return useQuery({
    queryKey: ['route-stops-geo', route?.id],
    queryFn: () => fetchRouteStopsGeo(route!),
    enabled: route !== null,
  });
}
