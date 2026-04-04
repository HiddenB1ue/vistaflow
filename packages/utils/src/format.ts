/** 格式化分钟数为“X小时X分”形式 */
export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}分`;
  if (m === 0) return `${h}小时`;
  return `${h}小时${m}分`;
}

/** 格式化价格为“¥XXX”形式 */
export function formatPrice(amount: number): string {
  return `¥${amount.toLocaleString('zh-CN')}`;
}
