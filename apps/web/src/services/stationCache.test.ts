import { describe, it, expect, beforeEach, vi } from 'vitest';
import { stationCache } from './stationCache';
import { apiClient } from './api';

vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('StationCache', () => {
  beforeEach(() => {
    stationCache.clear();
    vi.clearAllMocks();
  });

  it('should load stations once', async () => {
    const mockData = {
      data: {
        data: {
          items: [
            { name: '北京', telecode: 'BJP', pinyin: 'beijing', abbr: 'bj' },
            { name: '上海', telecode: 'SHH', pinyin: 'shanghai', abbr: 'sh' },
          ],
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockData);

    await stationCache.ensureLoaded();
    await stationCache.ensureLoaded(); // 第二次调用不应该再请求

    expect(apiClient.get).toHaveBeenCalledTimes(1);
    expect(apiClient.get).toHaveBeenCalledWith('/stations/all');
  });

  it('should search by exact name match', async () => {
    const mockData = {
      data: {
        data: {
          items: [
            { name: '北京', telecode: 'BJP', pinyin: 'beijing', abbr: 'bj' },
            { name: '北京南', telecode: 'VNP', pinyin: 'beijingnan', abbr: 'bjn' },
          ],
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockData);
    await stationCache.ensureLoaded();

    const results = stationCache.search('北京');
    expect(results[0].name).toBe('北京'); // 精确匹配应该排在前面
  });

  it('should search by pinyin', async () => {
    const mockData = {
      data: {
        data: {
          items: [
            { name: '北京', telecode: 'BJP', pinyin: 'beijing', abbr: 'bj' },
          ],
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockData);
    await stationCache.ensureLoaded();

    const results = stationCache.search('beijing');
    expect(results).toHaveLength(1);
    expect(results[0].name).toBe('北京');
  });

  it('should search by abbreviation', async () => {
    const mockData = {
      data: {
        data: {
          items: [
            { name: '北京', telecode: 'BJP', pinyin: 'beijing', abbr: 'bj' },
          ],
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockData);
    await stationCache.ensureLoaded();

    const results = stationCache.search('bj');
    expect(results).toHaveLength(1);
    expect(results[0].name).toBe('北京');
  });

  it('should limit results', async () => {
    const mockData = {
      data: {
        data: {
          items: Array.from({ length: 20 }, (_, i) => ({
            name: `车站${i}`,
            telecode: `ST${i}`,
            pinyin: `chezhan${i}`,
            abbr: `cz${i}`,
          })),
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockData);
    await stationCache.ensureLoaded();

    const results = stationCache.search('车站', 5);
    expect(results).toHaveLength(5);
  });

  it('should return empty array for empty keyword', async () => {
    const mockData = {
      data: {
        data: {
          items: [
            { name: '北京', telecode: 'BJP', pinyin: 'beijing', abbr: 'bj' },
          ],
        },
      },
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockData);
    await stationCache.ensureLoaded();

    const results = stationCache.search('');
    expect(results).toHaveLength(0);
  });
});
