import type { SearchParams } from '@/types/search';
import type { RouteList } from '@/types/route';
import { apiClient } from './api';
import { mockRoutes } from './mock/routes.mock';

const USE_MOCK = true; // 接口未就绪时使用 mock

export async function fetchRoutes(params: SearchParams): Promise<RouteList> {
  if (USE_MOCK) {
    // 模拟网络延迟
    await new Promise((resolve) => setTimeout(resolve, 800));
    return mockRoutes;
  }
  const { data } = await apiClient.get<RouteList>('/routes', { params });
  return data;
}
