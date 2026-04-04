export type TaskStatus = 'running' | 'pending' | 'completed' | 'error' | 'terminated';
type TaskType = 'fetch-status' | 'fetch-station' | 'geocode' | 'price' | 'cleanup';

export interface Task {
  id: string;
  name: string;
  type: TaskType;
  typeLabel: string;
  status: TaskStatus;
  description: string;
  cron?: string;
  metrics: { label: string; value: string };
  timing: { label: string; value: string };
  errorMessage?: string;
}
