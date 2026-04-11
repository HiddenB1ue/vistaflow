import type { SearchSuggestion } from '@/types/search';
import { apiClient } from './api';

interface StationData {
  name: string;
  telecode: string;
  pinyin: string;
  abbr: string;
}

class StationCache {
  private stations: StationData[] = [];
  private loaded = false;
  private loading: Promise<void> | null = null;

  /**
   * 加载所有车站数据（仅加载一次）
   */
  async ensureLoaded(): Promise<void> {
    if (this.loaded) return;
    if (this.loading) return this.loading;

    this.loading = this._loadStations();
    await this.loading;
    this.loading = null;
  }

  private async _loadStations(): Promise<void> {
    try {
      const { data } = await apiClient.get<{ data: { items: StationData[] } }>(
        '/stations/all',
      );
      this.stations = data.data.items;
      this.loaded = true;
      console.log(`✅ 已缓存 ${this.stations.length} 个车站数据`);
    } catch (error) {
      console.error('❌ 加载车站数据失败:', error);
      throw error;
    }
  }

  /**
   * 在本地缓存中搜索车站
   */
  search(keyword: string, limit = 10): SearchSuggestion[] {
    if (!this.loaded || !keyword.trim()) {
      return [];
    }

    const kw = keyword.trim().toLowerCase();
    const results: Array<{ station: StationData; score: number }> = [];

    for (const station of this.stations) {
      const name = station.name.toLowerCase();
      const pinyin = (station.pinyin || '').toLowerCase();
      const abbr = (station.abbr || '').toLowerCase();

      let score = 0;

      // 精确匹配 - 最高优先级
      if (name === kw) {
        score = 1000;
      } else if (abbr === kw) {
        score = 900;
      }
      // 前缀匹配 - 高优先级
      else if (name.startsWith(kw)) {
        score = 800;
      } else if (abbr.startsWith(kw)) {
        score = 700;
      } else if (pinyin.startsWith(kw)) {
        score = 600;
      }
      // 包含匹配 - 低优先级
      else if (name.includes(kw)) {
        score = 500;
      } else if (pinyin.includes(kw)) {
        score = 400;
      } else if (abbr.includes(kw)) {
        score = 300;
      }

      if (score > 0) {
        results.push({ station, score });
      }
    }

    // 按分数排序，然后按名称排序
    results.sort((a, b) => {
      if (a.score !== b.score) {
        return b.score - a.score;
      }
      return a.station.name.localeCompare(b.station.name, 'zh-CN');
    });

    // 返回前 N 个结果
    return results.slice(0, limit).map(({ station }) => ({
      id: station.telecode || station.name,
      name: station.name,
      code: station.telecode,
      city: '',
    }));
  }

  /**
   * 清除缓存（用于测试或强制刷新）
   */
  clear(): void {
    this.stations = [];
    this.loaded = false;
    this.loading = null;
  }
}

// 单例实例
export const stationCache = new StationCache();

/**
 * 使用缓存搜索车站建议
 */
export async function fetchStationSuggestionsFromCache(
  keyword: string,
): Promise<SearchSuggestion[]> {
  await stationCache.ensureLoaded();
  return stationCache.search(keyword);
}
