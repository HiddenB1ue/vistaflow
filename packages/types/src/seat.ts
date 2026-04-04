/** 座位类型联合 */
export type SeatClassType = 'business' | 'first' | 'second';

/** 座位等级信息 */
export interface SeatClass {
  type: SeatClassType;
  /** 显示标签（如"商务座"） */
  label: string;
  /** 价格 */
  price: number;
  /** 是否可用 */
  available: boolean;
}
