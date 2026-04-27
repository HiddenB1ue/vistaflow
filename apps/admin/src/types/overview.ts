export interface KpiStats {
  totalRecords: number;
  stationCoverage: number;
  stationsWithCoordinates: number;
  coordCompletionRate: number;
  pendingAlerts: number;
  todayRecordChanges: number;
  todayTaskRuns: number;
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

