import type { SearchSuggestion } from '@/types/search';
import { apiClient } from './api';

interface BackendSuggestItem {
  name: string;
  telecode: string;
  pinyin: string;
  abbr: string;
}

interface BackendSuggestResponse {
  items: BackendSuggestItem[];
}

export async function fetchStationSuggestions(
  keyword: string,
): Promise<SearchSuggestion[]> {
  const kw = keyword.trim();
  if (!kw) return [];

  const { data } = await apiClient.get<{ data: BackendSuggestResponse }>(
    '/stations/suggest',
    { params: { q: kw, limit: 10 } },
  );

  return data.data.items.map((item) => ({
    id:   item.telecode || item.name,
    name: item.name,
    code: item.telecode,
    city: '',
  }));
}
