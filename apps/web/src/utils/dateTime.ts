const MS_PER_DAY = 24 * 60 * 60 * 1000;

export function getRouteDayOffset(date: string, baseDate: string): number {
  if (!date || !baseDate || date === baseDate) {
    return 0;
  }

  const targetTime = Date.parse(`${date}T00:00:00Z`);
  const baseTime = Date.parse(`${baseDate}T00:00:00Z`);
  if (!Number.isFinite(targetTime) || !Number.isFinite(baseTime)) {
    return 0;
  }

  return Math.max(0, Math.round((targetTime - baseTime) / MS_PER_DAY));
}
