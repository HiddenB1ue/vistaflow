import type { SearchSuggestion } from '@/types/search';
import { fetchStationSuggestionsFromCache } from './stationCache';

/**
 * 获取车站搜索建议（使用本地缓存）
 */
export async function fetchStationSuggestions(
  keyword: string,
): Promise<SearchSuggestion[]> {
  return fetchStationSuggestionsFromCache(keyword);
}
