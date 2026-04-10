export interface KpiStats {
  totalRecords: number;
  stationCoverage: number;
  coordCompletionRate: number;
  pendingAlerts: number;
  todayApiCalls: number;
  remainingQuota: number;
}

export interface ActiveTask {
  id: number;
  name: string;
  status: 'running' | 'pending';
  elapsedTime?: string;
  startedAt?: string;
}

export interface SystemAlert {
  id: number;
  severity: 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
}

export interface SparklineData {
  values: number[];
  labels: string[];
}

export interface ApiQuota {
  percentage: number;
  used: number;
  total: number;
}
