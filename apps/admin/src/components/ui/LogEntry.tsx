import type { LogSeverity } from '@/types/log';
import { Badge, LogRow } from '@vistaflow/ui';
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
    <LogRow
      timestamp={timestamp}
      badge={<Badge variant={severityBadgeMap[severity]}>{severity}</Badge>}
    >
      {message}
    </LogRow>
  );
}
