import type { LogSeverity } from '@/types/log';
import { Badge } from '@vistaflow/ui';
import type { ReactNode } from 'react';

interface LogEntryProps {
  timestamp: string;
  severity: LogSeverity;
  message: ReactNode;
}

const severityBadgeMap: Record<LogSeverity, 'green' | 'blue' | 'yellow' | 'red' | 'purple'> = {
  SUCCESS: 'green',
  INFO: 'blue',
  WARN: 'yellow',
  ERROR: 'red',
  SYSTEM: 'purple',
};

export function LogEntry({ timestamp, severity, message }: LogEntryProps) {
  return (
    <div className="log-line">
      <span className="log-time">{timestamp}</span>
      <Badge variant={severityBadgeMap[severity]}>{severity}</Badge>
      <span className="text-starlight/80 text-xs leading-relaxed">{message}</span>
    </div>
  );
}
