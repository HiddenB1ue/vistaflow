
import type { RouteList } from '@/types/route';
import { convertRouteListCoordinates } from '@/services/coordinateService';
import { routeFixtures } from './routeFixtures';

export const mockRoutes: RouteList = convertRouteListCoordinates(routeFixtures);
