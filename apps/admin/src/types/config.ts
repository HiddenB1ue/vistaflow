export type SystemSettingValue = string | number | boolean | Record<string, unknown> | unknown[] | null;

export interface SystemSetting {
  key: string;
  value: SystemSettingValue;
  valueType: 'string' | 'int' | 'float' | 'bool' | 'json';
  category: 'amap' | 'ticket_12306' | 'task' | 'system' | string;
  label: string;
  description?: string;
  enabled: boolean;
  updatedAt: string;
}

export interface SystemSettingBatchUpdateItem {
  key: string;
  value: SystemSettingValue;
  enabled: boolean;
}

export interface SystemSettingsBatchUpdateRequest {
  items: SystemSettingBatchUpdateItem[];
}

export interface SystemSettingsBatchUpdateResponse {
  updatedCount: number;
  updatedKeys: string[];
  updatedAt: string;
}
