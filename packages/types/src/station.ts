/** 站点基础类型 — 两个应用共享的核心字段 */
export interface BaseStation {
  /** 站点名称 */
  name: string;
  /** 站点编码（电报码） */
  code: string;
  /** 所属城市 */
  city: string;
}
