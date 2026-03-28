/** 格式化价格为 "¥XXX" 形式 */
export function formatPrice(amount: number): string {
  return `¥${amount.toLocaleString('zh-CN')}`;
}
