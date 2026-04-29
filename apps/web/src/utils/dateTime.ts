export function formatRouteDateTime(date: string, time: string, baseDate: string): string {
  if (!date || date === baseDate) {
    return time;
  }
  return `${date.slice(5)} ${time}`;
}
