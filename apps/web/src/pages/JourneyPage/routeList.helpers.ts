import type { JourneySortMode } from '@/services/routeService';

export const SORT_OPTIONS: Array<{ value: JourneySortMode; label: string }> = [
  { value: 'duration', label: '\u603b\u8017\u65f6' },
  { value: 'price', label: '\u6700\u4f4e\u4ef7\u683c' },
  { value: 'departure', label: '\u51fa\u53d1\u65f6\u95f4' },
];
